"""Evaluation records."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Frozen in docs/02-experiment-design.md §3, before any model output existed.
Outcome = Literal[
    "CORRECT_STRICT",
    "CORRECT_LOOSE",
    "WRONG_TARGET",
    "ABSTAINED",
    "NO_EDIT",
    "MALFORMED",
]

# How the returned document was matched to the original. Recorded per case so reliance
# on a weaker tier is visible in the results rather than invisible in the code.
AlignmentTier = Literal["TOKEN", "ID", "POSITION", "FAILED"]

_FROZEN = ConfigDict(extra="forbid", frozen=True)


class EvaluationResult(BaseModel):
    """One scored response.

    Identification, execution and collateral are recorded separately rather than
    collapsed into one correct/incorrect bit. A model that finds the right element and
    performs the wrong edit has succeeded at the thing this instrument measures and
    failed at something else; a single bit would blame reference resolution for an
    execution error (ADR-0006).
    """

    model_config = _FROZEN

    case_id: str
    outcome: Outcome

    # Did the model act on the intended element at all. The primary signal.
    target_edited: bool
    # Did that edit match the operation's specification.
    target_edit_correct: bool
    # Everything else that changed. The hedging measure.
    collateral_element_ids: tuple[str, ...] = ()
    # Elements the model appears to have acted on, target included.
    predicted_target_ids: tuple[str, ...] = ()

    alignment_tier: AlignmentTier
    malformed_reason: str | None = None

    @property
    def n_modified(self) -> int:
        """Total elements changed. `1` is ideal; larger values are hedging."""
        return len(self.predicted_target_ids)

    @property
    def identified(self) -> bool:
        """The primary metric's per-case value (ADR-0006)."""
        return self.target_edited


class ScoringConfig(BaseModel):
    """Scoring rules, frozen before the first model output was observed."""

    model_config = _FROZEN

    numeric_tolerance: float = Field(gt=0.0)
    abstention_rule_version: str
