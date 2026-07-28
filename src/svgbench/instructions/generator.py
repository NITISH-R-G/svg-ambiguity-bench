"""Instruction synthesis and adaptive allocation.

Supports C1 (text leaks nothing) and C8 (only defensible predicates become cases).

The allocation problem is set by FA-008: per-SVG predicate availability is inherently
uneven, because definition disagreement and distractor dominance are validity
requirements rather than tunable thresholds. No margin setting makes them uniform.

So balance is a CORPUS-level property, achieved by preferring globally under-used
predicates and operations when choosing within a sample. The alternative - forcing every
sample to contribute the same split - would mean weakening per-sample validity to satisfy
the allocator, which inverts the priority: the generator would serve the allocation
algorithm instead of the construct-validity rules.
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from collections.abc import Sequence

from svgbench.config import Config
from svgbench.generation import SVGSample
from svgbench.groundtruth import REGISTRY, SampleGroundTruth
from svgbench.instructions.lint import lint_instruction_text
from svgbench.instructions.records import (
    Instruction,
    InstructionProvenance,
    RejectedCandidate,
)
from svgbench.instructions.templates import (
    EDIT_COLOURS,
    ROTATION_DEGREES,
    STROKE_COLOURS,
    STROKE_WIDTHS,
    render,
    template_id,
)


def _digest(*parts: object, length: int = 12) -> str:
    key = ":".join(str(part) for part in parts)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:length]


def _operation_params(
    operation: str,
    rng: random.Random,
    unavailable_colours: set[str],
) -> dict[str, object]:
    """Edit parameters, avoiding any colour already present in the document.

    A requested colour that already appears would make a new edit indistinguishable from
    a pre-existing fill at scoring time.
    """
    if operation == "recolor_fill":
        options = [c for c in EDIT_COLOURS if c.lower() not in unavailable_colours]
        if not options:
            raise RuntimeError("no edit colour is free of the document's existing fills")
        return {"fill": rng.choice(options)}
    if operation == "add_stroke":
        options = [c for c in STROKE_COLOURS if c.lower() not in unavailable_colours]
        if not options:
            raise RuntimeError("no stroke colour is free of the document's existing fills")
        return {"stroke": rng.choice(options), "stroke_width": rng.choice(STROKE_WIDTHS)}
    if operation == "rotate":
        return {"degrees": rng.choice(ROTATION_DEGREES)}
    if operation == "delete":
        return {}
    raise ValueError(f"unknown operation {operation!r}")


def build_instructions(
    samples: list[SVGSample],
    truths: list[SampleGroundTruth],
    config: Config,
) -> list[Instruction]:
    """Emit the corpus instruction set. Deterministic given `config.seed`."""
    by_svg = {sample.svg_id: sample for sample in samples}
    budget = config.instructions.instructions_per_svg
    operations = list(config.instructions.operations)

    # Global usage counters drive corpus-level balance: within a sample, the
    # least-used predicate and operation win, so skew accumulated elsewhere is
    # corrected here rather than at the end.
    predicate_usage: Counter[str] = Counter()
    operation_usage: Counter[str] = Counter()

    instructions: list[Instruction] = []

    for truth in truths:
        sample = by_svg[truth.svg_id]
        rng = random.Random(int(_digest(config.seed, "instr", truth.svg_id, length=15), 16))

        rejected = tuple(
            RejectedCandidate(predicate=name, reason=str(result.invalid_reason))
            for name, result in sorted(truth.predicates.items())
            if not result.is_valid
        )

        # Anything a model could match against the markup, checked against emitted text.
        forbidden = {e.element_id for e in sample.elements}
        forbidden |= {e.geometry_token for e in sample.elements}
        forbidden |= {e.fill for e in sample.elements}
        document_colours = {e.fill.lower() for e in sample.elements}

        for predicate, operation in _allocate(
            truth, operations, budget, predicate_usage, operation_usage, rng
        ):
            result = truth.predicates[predicate]
            params = _operation_params(operation, rng, document_colours)

            target_variant = rng.randrange(2)
            operation_variant = rng.randrange(2)
            text = render(predicate, operation, target_variant, operation_variant, params)

            lint_instruction_text(text, forbidden)

            instruction_id = f"ins_{_digest(config.seed, truth.svg_id, predicate, operation)}"
            instructions.append(
                Instruction(
                    instruction_id=instruction_id,
                    case_id=f"case_{_digest(truth.svg_id, instruction_id)}",
                    svg_id=truth.svg_id,
                    family=REGISTRY[predicate].family,
                    predicate=predicate,
                    operation=operation,
                    operation_params=params,
                    text=text,
                    template_id=template_id(
                        predicate, operation, target_variant, operation_variant
                    ),
                    target_element_id=result.winner,
                    k=len(truth.ambiguity_ids),
                    provenance=InstructionProvenance(
                        accepted_because=(
                            "all_definitions_agree",
                            "margin_clears_threshold",
                            "unique_over_full_element_set",
                            "witnesses_agree_on_ranking"
                            if result.family == "ORDINAL_SIZE"
                            else "winner_in_required_quadrant",
                        ),
                        margin=result.margin,
                        rejected_candidates=rejected,
                    ),
                )
            )
            predicate_usage[predicate] += 1
            operation_usage[operation] += 1

    return instructions


def _allocate(
    truth: SampleGroundTruth,
    operations: Sequence[str],
    budget: int,
    predicate_usage: Counter[str],
    operation_usage: Counter[str],
    rng: random.Random,
) -> list[tuple[str, str]]:
    """Choose (predicate, operation) pairs for one sample.

    Reusing a predicate under a different operation is a legitimately distinct case, so
    capacity is |valid predicates| x |operations| rather than |valid predicates|. That
    keeps the budget fillable on samples where few predicates survived, without
    weakening the validity rules that refused the others.

    Both families are guaranteed a slot first: the SVG is the resampling unit, so a
    sample supplying only one family would contribute to one side of the family
    comparison and not the other.
    """
    by_family: dict[str, list[str]] = {}
    for name in truth.valid_predicates:
        by_family.setdefault(truth.predicates[name].family, []).append(name)

    families = sorted(by_family)
    capacity = {family: len(by_family[family]) * len(operations) for family in families}

    # Family quotas are set explicitly rather than emerging from a global least-used
    # rule. Letting per-predicate counts drive the choice skewed the corpus to 61%
    # spatial: there are twice as many spatial predicates as ordinal ones, so each
    # individual spatial predicate accrues usage more slowly and keeps winning the
    # least-used comparison. Balancing predicates is not the same as balancing families.
    share = budget // len(families) if families else 0
    quotas = {family: min(share, capacity[family]) for family in families}

    # Any budget a family cannot absorb goes to one that can, so a sample short on
    # spatial predicates still contributes its full quota of cases.
    leftover = budget - sum(quotas.values())
    while leftover > 0:
        spare = [f for f in families if capacity[f] > quotas[f]]
        if not spare:
            break
        family = max(spare, key=lambda f: (capacity[f] - quotas[f], f))
        quotas[family] += 1
        leftover -= 1

    chosen: list[tuple[str, str]] = []
    used: set[tuple[str, str]] = set()

    for family in families:
        for _ in range(quotas[family]):
            pool = [
                (predicate, operation)
                for predicate in by_family[family]
                for operation in operations
                if (predicate, operation) not in used
            ]
            if not pool:
                break
            # Least globally-used predicate and operation, so skew accumulated on
            # other samples is corrected here. Ties broken deterministically.
            jitter = {pair: rng.random() for pair in pool}
            pair = min(
                pool,
                key=lambda p: (
                    predicate_usage[p[0]] + operation_usage[p[1]],
                    jitter[p],
                ),
            )
            chosen.append(pair)
            used.add(pair)

    return chosen
