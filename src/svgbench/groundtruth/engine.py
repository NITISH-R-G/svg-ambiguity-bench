"""The ground-truth engine.

Supports claims C7 and C8. This is where measured geometry becomes the answer key, and
where samples that cannot host an uncontested answer are refused.

Two kinds of refusal, and the distinction matters:

  MEASUREMENT invalidity - the two witnesses disagree, so we do not know the answer.
  CONSTRUCT invalidity   - the witnesses agree, but two reasonable readings of the
                           instruction pick different elements, so there IS no single
                           answer a person would give.

A benchmark that only checks the first is merely correct. Checking the second is what
makes the answer key defensible, and roughly one sample in eight in this corpus is
construct-invalid while being perfectly well measured.

Every refusal is recorded with its reason and published. Rejection sampling biases the
corpus toward easy cases, and the size of that bias is a number reviewers are entitled to.
"""

from __future__ import annotations

from collections import Counter

from svgbench.config import Config
from svgbench.generation import SVGSample
from svgbench.geometry import ElementGeometry, measure_document, witnesses_agree_on_ranking
from svgbench.groundtruth.predicates import REGISTRY, PredicateSpec, quadrant_of
from svgbench.groundtruth.records import (
    InvalidReason,
    PredicateResult,
    SampleGroundTruth,
)


def build_ground_truth(sample: SVGSample, config: Config) -> SampleGroundTruth:
    """Measure a sample and decide which predicates it can host."""
    measured = measure_document(
        sample.resolved_svg,
        sample.canvas_size,
        scale=config.generation.raster_scale,
        strict=True,
    )

    ambiguity_ids = [e.element_id for e in sample.ambiguity_elements]
    all_ids = [e.element_id for e in sample.elements]
    ranking_is_sound = witnesses_agree_on_ranking(measured, ambiguity_ids)

    wanted: list[str] = list(config.instructions.spatial_predicates) + list(
        config.instructions.ordinal_predicates
    )
    results: dict[str, PredicateResult] = {
        name: _evaluate(
            REGISTRY[name],
            measured,
            ambiguity_ids,
            all_ids,
            sample.canvas_size,
            config,
            ranking_is_sound,
        )
        for name in wanted
    }

    return SampleGroundTruth(
        svg_id=sample.svg_id,
        geometry=measured,
        ambiguity_ids=tuple(ambiguity_ids),
        predicates=results,
        witnesses_agree_on_ranking=ranking_is_sound,
    )


def _evaluate(
    spec: PredicateSpec,
    measured: dict[str, ElementGeometry],
    ambiguity_ids: list[str],
    all_ids: list[str],
    canvas: int,
    config: Config,
    ranking_is_sound: bool,
) -> PredicateResult:
    if spec.area_rank is not None:
        return _evaluate_ordinal(spec, measured, ambiguity_ids, config, ranking_is_sound)
    return _evaluate_spatial(spec, measured, ambiguity_ids, all_ids, canvas, config)


def _evaluate_spatial(
    spec: PredicateSpec,
    measured: dict[str, ElementGeometry],
    ambiguity_ids: list[str],
    all_ids: list[str],
    canvas: int,
    config: Config,
) -> PredicateResult:
    primary, *alternatives = spec.scorers
    scores = {i: primary(measured[i], canvas) for i in ambiguity_ids}
    ordered = sorted(ambiguity_ids, key=lambda i: scores[i])
    winner, runner_up = ordered[0], ordered[1]

    # Normalised so the threshold means the same thing on any canvas.
    margin = (scores[runner_up] - scores[winner]) / canvas

    def result(valid: bool, reason: InvalidReason | None) -> PredicateResult:
        return PredicateResult(
            predicate=spec.name,
            family=spec.family,
            winner=winner,
            runner_up=runner_up,
            margin=margin,
            is_valid=valid,
            invalid_reason=reason,
        )

    # CONSTRUCT validity: would a different reasonable reading pick someone else?
    for alternative in alternatives:
        alt_scores = {i: alternative(measured[i], canvas) for i in ambiguity_ids}
        if min(ambiguity_ids, key=lambda i: alt_scores[i]) != winner:
            return result(False, "definition_disagreement")

    if margin < config.generation.min_spatial_margin:
        return result(False, "margin_too_small")

    # A distractor beating the intended target would make the instruction genuinely
    # ambiguous to a person, and a model picking the distractor would be marked wrong
    # while being arguably right.
    outsiders = [i for i in all_ids if i not in ambiguity_ids]
    if any(primary(measured[i], canvas) < scores[winner] for i in outsiders):
        return result(False, "distractor_outranks_target")

    if (
        spec.required_quadrant is not None
        and quadrant_of(measured[winner], canvas) != spec.required_quadrant
    ):
        return result(False, "winner_outside_quadrant")

    return result(True, None)


def _evaluate_ordinal(
    spec: PredicateSpec,
    measured: dict[str, ElementGeometry],
    ambiguity_ids: list[str],
    config: Config,
    ranking_is_sound: bool,
) -> PredicateResult:
    by_area = sorted(ambiguity_ids, key=lambda i: measured[i].area, reverse=True)
    rank = spec.area_rank
    assert rank is not None

    index = len(by_area) - 1 if rank == -1 else rank - 1
    if not 0 <= index < len(by_area):
        return PredicateResult(
            predicate=spec.name,
            family=spec.family,
            winner=by_area[0],
            runner_up=by_area[0],
            margin=0.0,
            is_valid=False,
            invalid_reason="rank_out_of_range",
        )

    winner = by_area[index]
    # The contested neighbour is whichever adjacent rank is closest in area: a rank is
    # only as safe as its tightest boundary.
    neighbours = [by_area[j] for j in (index - 1, index + 1) if 0 <= j < len(by_area)]
    runner_up = min(neighbours, key=lambda i: abs(measured[i].area - measured[winner].area))

    larger = max(measured[winner].area, measured[runner_up].area)
    smaller = min(measured[winner].area, measured[runner_up].area)
    margin = larger / smaller if smaller > 0 else 0.0

    def result(valid: bool, reason: InvalidReason | None) -> PredicateResult:
        return PredicateResult(
            predicate=spec.name,
            family=spec.family,
            winner=winner,
            runner_up=runner_up,
            margin=margin,
            is_valid=valid,
            invalid_reason=reason,
        )

    # MEASUREMENT validity: if the two witnesses order the set differently, the rank
    # this predicate names is not a fact about the picture.
    if not ranking_is_sound:
        return result(False, "witness_rank_disagreement")

    if margin < config.generation.min_area_ratio:
        return result(False, "margin_too_small")

    return result(True, None)


def build_corpus_ground_truth(
    samples: list[SVGSample], config: Config
) -> tuple[list[SampleGroundTruth], Counter[str]]:
    """Ground truth for a whole corpus, plus a tally of why predicates were refused.

    The tally is published rather than kept internal: it is the direct measure of how
    much easier rejection sampling has made this corpus than an arbitrary one.
    """
    truths = [build_ground_truth(sample, config) for sample in samples]
    tally: Counter[str] = Counter()
    for truth in truths:
        for result in truth.predicates.values():
            key = result.invalid_reason if result.invalid_reason else "valid"
            tally[f"{result.predicate}:{key}"] += 1
            tally[key] += 1
    return truths, tally
