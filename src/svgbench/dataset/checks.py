"""Instrument checks performed at freeze time.

These are the claims the certificate asserts. Each one is executed against the artefacts
actually being frozen - not against a fresh in-memory object that happens to be lying
around - so a PASS means the bytes on disk have the property, not that the generator
intended them to.

Every check returns a result rather than raising, so the certificate can report a
complete picture instead of stopping at the first failure. `freeze` refuses to write a
manifest when any check fails.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from svgbench.config import Config
from svgbench.dataset.records import CheckResult
from svgbench.generation import SVGSample
from svgbench.groundtruth import SampleGroundTruth
from svgbench.instructions import Instruction

SVG_NS = "{http://www.w3.org/2000/svg}"
POSITIONAL_ATTRIBUTES = frozenset(
    {"transform", "x", "y", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2", "points"}
)
TOKEN_PATTERN = re.compile(r"^\{\{GEOM_[0-9a-f]{8}\}\}$")


def check_generator_invariants(samples: list[SVGSample]) -> CheckResult:
    """C1: markup carries nothing that distinguishes ambiguity-set members."""
    problems: list[str] = []
    token_lengths: set[int] = set()

    for sample in samples:
        members = {e.element_id for e in sample.ambiguity_elements}
        signatures: set[tuple[str, tuple[str, ...], str | None]] = set()
        for element in ET.fromstring(sample.model_visible_svg).iter():
            if element.tag == f"{SVG_NS}svg":
                continue
            offending = POSITIONAL_ATTRIBUTES & set(element.attrib)
            if offending:
                problems.append(f"{sample.svg_id}: positional attribute {sorted(offending)}")
            data = element.get("d", "")
            if not TOKEN_PATTERN.match(data):
                problems.append(f"{sample.svg_id}: unredacted geometry {data[:24]!r}")
            token_lengths.add(len(data))
            if element.get("id") in members:
                signatures.add((element.tag, tuple(sorted(element.attrib)), element.get("fill")))
        if len(signatures) != 1:
            problems.append(f"{sample.svg_id}: ambiguity members differ in markup")

    if len(token_lengths) > 1:
        problems.append(f"geometry token lengths vary: {sorted(token_lengths)}")

    return CheckResult(
        name="Generator invariants",
        passed=not problems,
        detail=(
            f"{len(samples)} samples: identical tag/fill, no positional attributes, "
            f"fixed-length tokens ({token_lengths.pop() if len(token_lengths) == 1 else '?'} chars)"
            if not problems
            else "; ".join(problems[:3])
        ),
    )


def check_geometry_witnesses(truths: list[SampleGroundTruth]) -> CheckResult:
    """C7: two independent measurements agree on the ordering the ordinal family uses."""
    disagreeing = [t.svg_id for t in truths if not t.witnesses_agree_on_ranking]
    return CheckResult(
        name="Geometry witnesses",
        passed=not disagreeing,
        detail=(
            f"raster and analytic agree on ranking in {len(truths)}/{len(truths)} samples"
            if not disagreeing
            else f"rank disagreement in {disagreeing[:3]}"
        ),
    )


def check_ground_truth(
    truths: list[SampleGroundTruth], instructions: list[Instruction]
) -> CheckResult:
    """C8: every shipped instruction rests on a predicate the sample can defensibly host."""
    by_svg = {t.svg_id: t for t in truths}
    problems = [
        f"{i.instruction_id} uses refused predicate {i.predicate}"
        for i in instructions
        if i.predicate not in by_svg[i.svg_id].valid_predicates
    ]
    refused = sum(1 for t in truths for r in t.predicates.values() if not r.is_valid)
    total = sum(len(t.predicates) for t in truths)
    return CheckResult(
        name="Ground truth",
        passed=not problems,
        detail=(
            f"{total - refused}/{total} predicate slots admitted; {refused} refused as contested"
            if not problems
            else "; ".join(problems[:3])
        ),
    )


def check_instruction_allocation(instructions: list[Instruction], config: Config) -> CheckResult:
    """Balance is a corpus property; every sample must reach both families."""
    problems: list[str] = []
    families = Counter(i.family for i in instructions)
    total = sum(families.values())
    share = families["SPATIAL"] / total if total else 0.0
    if not 0.40 <= share <= 0.60:
        problems.append(f"family split {dict(families)}")

    per_svg: dict[str, set[str]] = {}
    for instruction in instructions:
        per_svg.setdefault(instruction.svg_id, set()).add(instruction.family)
    missing = [svg for svg, seen in per_svg.items() if len(seen) < 2]
    if missing:
        problems.append(f"samples missing a family: {missing[:3]}")

    operations = Counter(i.operation for i in instructions)
    return CheckResult(
        name="Instruction allocation",
        passed=not problems,
        detail=(
            f"{total} instructions, {families['SPATIAL']} spatial / "
            f"{families['ORDINAL_SIZE']} ordinal, operations {dict(sorted(operations.items()))}"
            if not problems
            else "; ".join(problems)
        ),
    )


def check_leakage(samples: list[SVGSample], instructions: list[Instruction]) -> CheckResult:
    """C1: instruction text carries nothing matchable against the markup."""
    by_svg = {s.svg_id: s for s in samples}
    problems: list[str] = []
    for instruction in instructions:
        sample = by_svg[instruction.svg_id]
        lowered = instruction.text.lower()
        for element in sample.elements:
            for token in (element.element_id, element.geometry_token, element.fill):
                if token.lower() in lowered:
                    problems.append(f"{instruction.instruction_id} leaks {token!r}")
    return CheckResult(
        name="Leakage audit",
        passed=not problems,
        detail=(
            f"{len(instructions)} instructions carry no id, geometry token or document fill"
            if not problems
            else "; ".join(problems[:3])
        ),
    )


def check_no_model_outputs(repo_root: Path) -> CheckResult:
    """The claim the certificate exists to make: nothing has been observed yet.

    Checked against the filesystem rather than asserted, because the whole point of the
    pre-registration boundary is that this statement can be verified by someone who does
    not trust the author.
    """
    experiments = repo_root / "experiments"
    responses = (
        sorted(experiments.rglob("*.jsonl")) + sorted(experiments.rglob("responses/*"))
        if experiments.exists()
        else []
    )
    return CheckResult(
        name="Model outputs observed",
        passed=not responses,
        detail=(
            "NO - experiments/ contains no stored responses"
            if not responses
            else f"YES - {len(responses)} response artefacts already present"
        ),
    )


def run_all(
    samples: list[SVGSample],
    truths: list[SampleGroundTruth],
    instructions: list[Instruction],
    config: Config,
    repo_root: Path,
) -> list[CheckResult]:
    return [
        check_generator_invariants(samples),
        check_geometry_witnesses(truths),
        check_ground_truth(truths, instructions),
        check_instruction_allocation(instructions, config),
        check_leakage(samples, instructions),
        check_no_model_outputs(repo_root),
    ]
