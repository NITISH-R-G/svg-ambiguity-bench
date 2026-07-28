"""Distributions archived alongside the frozen corpus.

These are not needed to run the experiment. They are archived because they *define the
instrument*: a hash proves two corpora are identical, but says nothing about what kind
of corpus it is. If someone deliberately builds a v2 with a different seed or different
thresholds, these are the baseline that makes the two comparable.

Several of these already appear in `EVIDENCE.md`. The difference is that those tables
describe the corpus at the moment the document was written, while these are sealed
inside the frozen dataset directory and content-hashed with it.
"""

from __future__ import annotations

import itertools
from collections import Counter
from typing import Any

from svgbench.generation import SVGSample
from svgbench.groundtruth import SampleGroundTruth
from svgbench.instructions import Instruction


def _summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    n = len(ordered)
    return {
        "n": float(n),
        "min": ordered[0],
        "p10": ordered[int(0.10 * (n - 1))],
        "median": ordered[n // 2],
        "p90": ordered[int(0.90 * (n - 1))],
        "max": ordered[-1],
        "mean": sum(ordered) / n,
    }


def compute_distributions(
    samples: list[SVGSample],
    truths: list[SampleGroundTruth],
    instructions: list[Instruction],
) -> dict[str, Any]:
    """Every distribution that characterises this corpus."""
    by_svg_truth = {t.svg_id: t for t in truths}

    aspect_ratios: list[float] = []
    area_ratios: list[float] = []
    centroids_x: list[float] = []
    centroids_y: list[float] = []
    for truth in truths:
        for element_id in truth.ambiguity_ids:
            geometry = truth.geometry[element_id]
            x0, y0, x1, y1 = geometry.analytic.bbox
            width, height = x1 - x0, y1 - y0
            if min(width, height) > 0:
                aspect_ratios.append(max(width, height) / min(width, height))
            centroids_x.append(geometry.centroid[0])
            centroids_y.append(geometry.centroid[1])
        areas = sorted((truth.geometry[i].area for i in truth.ambiguity_ids), reverse=True)
        area_ratios.extend(larger / smaller for larger, smaller in itertools.pairwise(areas))

    spatial_margins = [
        r.margin for t in truths for r in t.predicates.values() if r.family == "SPATIAL"
    ]
    ordinal_margins = [
        r.margin for t in truths for r in t.predicates.values() if r.family == "ORDINAL_SIZE"
    ]

    refusals: Counter[str] = Counter()
    accepted_by_predicate: Counter[str] = Counter()
    for truth in truths:
        for name, result in truth.predicates.items():
            if result.is_valid:
                accepted_by_predicate[name] += 1
            else:
                refusals[str(result.invalid_reason)] += 1

    # Where in document order the intended target sits. If targets clustered at a
    # particular position, a fixed-position policy would beat the 1/K floor for a reason
    # unrelated to reference resolution, and C1 would be false.
    target_document_positions: Counter[int] = Counter()
    for instruction in instructions:
        truth = by_svg_truth[instruction.svg_id]
        # `ambiguity_ids` is already in document order - it is filtered from the
        # sample's elements, which are stored as emitted. Re-sorting it (by element id,
        # say) would silently measure position in some other ordering, and this
        # distribution exists precisely to test whether a fixed-position policy could
        # beat the 1/K floor. A wrong ordering here would look entirely plausible.
        members = truth.ambiguity_ids
        if instruction.target_element_id in members:
            target_document_positions[members.index(instruction.target_element_id)] += 1

    return {
        "k": dict(sorted(Counter(s.k for s in samples).items())),
        "distractors": dict(sorted(Counter(len(s.distractor_elements) for s in samples).items())),
        "generation_attempts": dict(sorted(Counter(s.attempts for s in samples).items())),
        "aspect_ratio": _summary(aspect_ratios),
        "adjacent_area_ratio": _summary(area_ratios),
        "centroid_x": _summary(centroids_x),
        "centroid_y": _summary(centroids_y),
        "spatial_margin": _summary(spatial_margins),
        "ordinal_margin": _summary(ordinal_margins),
        "predicate_refusal_reasons": dict(refusals.most_common()),
        "predicate_accepted_counts": dict(sorted(accepted_by_predicate.items())),
        "valid_predicates_per_svg": dict(
            sorted(Counter(len(t.valid_predicates) for t in truths).items())
        ),
        "instructions_per_svg": dict(
            sorted(Counter(Counter(i.svg_id for i in instructions).values()).items())
        ),
        "instruction_family": dict(Counter(i.family for i in instructions)),
        "instruction_operation": dict(sorted(Counter(i.operation for i in instructions).items())),
        "instruction_predicate": dict(sorted(Counter(i.predicate for i in instructions).items())),
        "distinct_templates_used": len({i.template_id for i in instructions}),
        "case_k": dict(sorted(Counter(i.k for i in instructions).items())),
        "mean_random_reference": (
            sum(1.0 / i.k for i in instructions) / len(instructions) if instructions else 0.0
        ),
        "target_document_position": dict(sorted(target_document_positions.items())),
    }
