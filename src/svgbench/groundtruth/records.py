"""Ground-truth records."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from svgbench.geometry import ElementGeometry

InvalidReason = Literal[
    # Two reasonable readings of the instruction pick different elements. The sample is
    # well measured; there simply is no single answer a person would give.
    "definition_disagreement",
    # The winner does not beat the runner-up decisively enough to be obvious.
    "margin_too_small",
    # An element outside the ambiguity set wins the predicate, so the instruction does
    # not refer to what the benchmark intends.
    "distractor_outranks_target",
    # Nearest-corner alone can crown a shape near the middle of the canvas.
    "winner_outside_quadrant",
    # The two measurement witnesses order the ambiguity set differently, so the named
    # rank is not a fact about the picture.
    "witness_rank_disagreement",
    # e.g. `third_largest` on an ambiguity set of two.
    "rank_out_of_range",
]

_FROZEN = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


class PredicateResult(BaseModel):
    """Whether one predicate has a defensible answer on one sample."""

    model_config = _FROZEN

    predicate: str
    family: str
    winner: str
    runner_up: str
    # Spatial: normalised gap to the runner-up. Ordinal: area ratio to the closest
    # adjacent rank. Retained even when invalid, so the margin distribution can be
    # reported rather than only the pass/fail outcome.
    margin: float
    is_valid: bool
    invalid_reason: InvalidReason | None = None


class SampleGroundTruth(BaseModel):
    """The answer key for one sample, and the record of what it cannot answer."""

    model_config = _FROZEN

    svg_id: str
    geometry: dict[str, ElementGeometry]
    ambiguity_ids: tuple[str, ...]
    predicates: dict[str, PredicateResult]
    witnesses_agree_on_ranking: bool

    @property
    def valid_predicates(self) -> list[str]:
        """Predicates this sample may host. Only these can become instructions."""
        return sorted(name for name, r in self.predicates.items() if r.is_valid)

    def target_of(self, predicate: str) -> str:
        """The intended element, refusing to answer where there is no defensible answer."""
        result = self.predicates[predicate]
        if not result.is_valid:
            raise KeyError(f"{self.svg_id} cannot host {predicate!r}: {result.invalid_reason}")
        return result.winner
