"""Instruction generator tests.

Supports C1 (instruction text leaks nothing) and C8 (only defensible predicates become
cases).

The governing constraint, established at Step 5 and recorded as FA-008: per-SVG
predicate availability is inherently uneven, because definition disagreement and
distractor dominance are validity requirements rather than tunable thresholds. Balance
is therefore a CORPUS-level property. Forcing every sample to contribute the same
predicates would make the generator serve the allocation algorithm instead of the
construct-validity rules, which is backwards.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.generation import generate_corpus
from svgbench.groundtruth import build_corpus_ground_truth
from svgbench.instructions import LeakageError, build_instructions, lint_instruction_text

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"


@pytest.fixture(scope="module")
def config():  # type: ignore[no-untyped-def]
    return load_config(BASE, overrides={"generation.n_svgs": 12}).config


@pytest.fixture(scope="module")
def corpus(config):  # type: ignore[no-untyped-def]
    return generate_corpus(config)


@pytest.fixture(scope="module")
def truths(corpus, config):  # type: ignore[no-untyped-def]
    return build_corpus_ground_truth(corpus, config)[0]


@pytest.fixture(scope="module")
def instructions(corpus, truths, config):  # type: ignore[no-untyped-def]
    return build_instructions(corpus, truths, config)


# ---------------------------------------------------------------------------
# Every instruction must have exactly one defensible answer
# ---------------------------------------------------------------------------


def test_every_instruction_targets_a_valid_predicate(instructions, truths) -> None:  # type: ignore[no-untyped-def]
    by_svg = {t.svg_id: t for t in truths}
    for instruction in instructions:
        truth = by_svg[instruction.svg_id]
        assert instruction.predicate in truth.valid_predicates, (
            f"{instruction.instruction_id} uses {instruction.predicate}, refused for "
            f"{instruction.svg_id}: {truth.predicates[instruction.predicate].invalid_reason}"
        )


def test_every_target_matches_ground_truth(instructions, truths) -> None:  # type: ignore[no-untyped-def]
    """The resolver is code, never a model and never a human."""
    by_svg = {t.svg_id: t for t in truths}
    for instruction in instructions:
        assert instruction.target_element_id == by_svg[instruction.svg_id].target_of(
            instruction.predicate
        )


def test_targets_are_always_ambiguity_set_members(instructions, truths) -> None:  # type: ignore[no-untyped-def]
    """A distractor target would not be an ambiguity case at all."""
    by_svg = {t.svg_id: t for t in truths}
    for instruction in instructions:
        assert instruction.target_element_id in by_svg[instruction.svg_id].ambiguity_ids


def test_instruction_ids_and_case_ids_are_unique(instructions) -> None:  # type: ignore[no-untyped-def]
    ids = [i.instruction_id for i in instructions]
    assert len(set(ids)) == len(ids)
    cases = [i.case_id for i in instructions]
    assert len(set(cases)) == len(cases)


def test_no_duplicate_predicate_operation_pair_within_an_svg(instructions) -> None:  # type: ignore[no-untyped-def]
    """Reusing a predicate with a different operation is a legitimately distinct case;
    reusing the same pair would be the identical case twice."""
    seen: Counter[tuple[str, str, str]] = Counter()
    for instruction in instructions:
        seen[(instruction.svg_id, instruction.predicate, instruction.operation)] += 1
    assert all(count == 1 for count in seen.values())


# ---------------------------------------------------------------------------
# C1 - the instruction must not leak the answer
# ---------------------------------------------------------------------------


def test_instruction_text_never_contains_an_identifier(instructions, corpus) -> None:  # type: ignore[no-untyped-def]
    by_svg = {s.svg_id: s for s in corpus}
    for instruction in instructions:
        sample = by_svg[instruction.svg_id]
        for element in sample.elements:
            assert element.element_id not in instruction.text
            assert element.geometry_token not in instruction.text


def test_instruction_text_never_mentions_a_fill_in_the_document(instructions, corpus) -> None:  # type: ignore[no-untyped-def]
    """Naming the shared fill would let a model filter the candidate set by string
    match, turning a reference-resolution task into a grep."""
    by_svg = {s.svg_id: s for s in corpus}
    for instruction in instructions:
        fills = {e.fill.lower() for e in by_svg[instruction.svg_id].elements}
        assert not any(fill in instruction.text.lower() for fill in fills)


def test_instruction_text_never_reveals_document_position(instructions) -> None:  # type: ignore[no-untyped-def]
    """`third_largest` legitimately contains an ordinal word. Document-order phrasing
    ("the first element") would instead hand over a position in the markup.

    Word-boundary matched. A bare substring check rejects "outline" for containing
    "line" - the same bug this test originally shared with the lint it was meant to
    independently verify, which is a good argument for the check being written twice
    rather than imported.
    """
    pattern = re.compile(r"\b(first element|last element|index|line|nth|attribute)\b")
    for instruction in instructions:
        assert not pattern.search(instruction.text.lower()), instruction.text


def test_recolour_target_colour_is_absent_from_the_document(instructions, corpus) -> None:  # type: ignore[no-untyped-def]
    """If the requested colour were already used, scoring could not distinguish a new
    edit from a pre-existing fill."""
    by_svg = {s.svg_id: s for s in corpus}
    for instruction in instructions:
        if instruction.operation != "recolor_fill":
            continue
        fills = {e.fill.lower() for e in by_svg[instruction.svg_id].elements}
        assert instruction.operation_params["fill"].lower() not in fills


def test_lint_rejects_a_leaking_instruction() -> None:
    """A lint that cannot fail is decoration."""
    with pytest.raises(LeakageError, match="e0d63fea4"):
        lint_instruction_text(
            "make e0d63fea4 blue",
            forbidden={"e0d63fea4"},
        )


# ---------------------------------------------------------------------------
# Phrasing diversity
# ---------------------------------------------------------------------------


def test_each_used_predicate_appears_in_more_than_one_phrasing(instructions) -> None:  # type: ignore[no-untyped-def]
    """Guards against the result being an artifact of one wording.

    CanItEdit (arXiv 2312.12450) showed instruction register alone changes measured
    edit accuracy, so a single phrasing per predicate would confound wording with
    capability.
    """
    phrasings: dict[str, set[str]] = {}
    for instruction in instructions:
        phrasings.setdefault(instruction.predicate, set()).add(instruction.template_id)
    thin = {p: v for p, v in phrasings.items() if len(v) < 2}
    assert not thin, f"predicates used with only one phrasing: {thin}"


def test_template_ids_are_recorded(instructions) -> None:  # type: ignore[no-untyped-def]
    """Needed to report per-template variance later."""
    for instruction in instructions:
        assert instruction.template_id


# ---------------------------------------------------------------------------
# Allocation - balanced across the corpus, adaptive within a sample
# ---------------------------------------------------------------------------


def test_allocation_fills_the_budget_where_availability_allows(
    instructions, truths, config
) -> None:  # type: ignore[no-untyped-def]
    """Each SVG should reach `instructions_per_svg` unless it genuinely cannot."""
    per_svg = Counter(i.svg_id for i in instructions)
    budget = config.instructions.instructions_per_svg
    for truth in truths:
        capacity = len(truth.valid_predicates) * len(config.instructions.operations)
        assert per_svg[truth.svg_id] == min(budget, capacity), (
            f"{truth.svg_id}: emitted {per_svg[truth.svg_id]}, capacity {capacity}"
        )


def test_every_svg_contributes_to_both_families(instructions) -> None:  # type: ignore[no-untyped-def]
    """The SVG is the resampling unit, so a sample supplying one family would
    contribute to one side of the family comparison and not the other."""
    families: dict[str, set[str]] = {}
    for instruction in instructions:
        families.setdefault(instruction.svg_id, set()).add(instruction.family)
    for svg_id, seen in families.items():
        assert seen == {"SPATIAL", "ORDINAL_SIZE"}, f"{svg_id}: only {seen}"


def test_families_are_balanced_across_the_corpus(instructions) -> None:  # type: ignore[no-untyped-def]
    """Balance is a corpus property, deliberately not a per-sample one (FA-008)."""
    counts = Counter(i.family for i in instructions)
    share = counts["SPATIAL"] / sum(counts.values())
    assert 0.40 <= share <= 0.60, f"family split {counts}"


def test_operations_are_balanced_across_the_corpus(instructions, config) -> None:  # type: ignore[no-untyped-def]
    counts = Counter(i.operation for i in instructions)
    assert set(counts) == set(config.instructions.operations)
    assert max(counts.values()) - min(counts.values()) <= max(3, len(instructions) // 12)


def test_predicate_diversity_varies_across_samples(instructions) -> None:  # type: ignore[no-untyped-def]
    """Where FA-008's unevenness actually surfaces.

    Family COUNTS are near-uniform by design - each sample owes its quota to both
    families, and a sample with a single surviving spatial predicate still fills that
    quota by pairing it with different operations. What genuinely varies is how many
    distinct predicates a sample can offer, which is the constraint the ground-truth
    gate imposes and the allocator works around rather than erases.
    """
    distinct: dict[str, set[str]] = {}
    for instruction in instructions:
        if instruction.family == "SPATIAL":
            distinct.setdefault(instruction.svg_id, set()).add(instruction.predicate)
    spread = {svg: len(names) for svg, names in distinct.items()}
    assert len(set(spread.values())) > 1, (
        f"every sample offered the same number of distinct spatial predicates ({spread}), "
        "so the adaptive path is unexercised by this corpus"
    )


# ---------------------------------------------------------------------------
# Provenance - why this instruction exists and not another
# ---------------------------------------------------------------------------


def test_every_instruction_records_why_it_was_accepted(instructions) -> None:  # type: ignore[no-untyped-def]
    for instruction in instructions:
        assert instruction.provenance.accepted_because, instruction.instruction_id
        assert instruction.provenance.margin > 0


def test_provenance_records_the_rejected_alternatives(instructions, truths) -> None:  # type: ignore[no-untyped-def]
    """Six months from now, "why did this one survive and that one not" must be
    answerable from the record rather than by re-deriving it."""
    by_svg = {t.svg_id: t for t in truths}
    for instruction in instructions:
        truth = by_svg[instruction.svg_id]
        refused = {name: r.invalid_reason for name, r in truth.predicates.items() if not r.is_valid}
        recorded = {c.predicate: c.reason for c in instruction.provenance.rejected_candidates}
        assert recorded == refused, f"{instruction.instruction_id}: provenance drifted"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_instruction_generation_is_deterministic(corpus, truths, config) -> None:  # type: ignore[no-untyped-def]
    first = build_instructions(corpus, truths, config)
    second = build_instructions(corpus, truths, config)
    assert [i.case_id for i in first] == [i.case_id for i in second]
    assert [i.text for i in first] == [i.text for i in second]


def test_case_id_is_a_function_of_svg_and_instruction(instructions) -> None:  # type: ignore[no-untyped-def]
    for instruction in instructions:
        assert re.match(r"^case_[0-9a-f]{12}$", instruction.case_id)
