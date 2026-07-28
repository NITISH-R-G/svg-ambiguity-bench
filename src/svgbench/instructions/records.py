"""Instruction records."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_FROZEN = ConfigDict(extra="forbid", frozen=True)


class RejectedCandidate(BaseModel):
    """A predicate this sample could not host, and why."""

    model_config = _FROZEN

    predicate: str
    reason: str


class InstructionProvenance(BaseModel):
    """Why this instruction exists, and what was refused alongside it.

    Not required by the experiment. Required by the person who, months from now, looks
    at one instruction that seems odd and needs to know why it survived while another
    did not - without re-deriving the whole ground-truth pass to find out.
    """

    model_config = _FROZEN

    accepted_because: tuple[str, ...]
    margin: float
    # Every predicate refused for this sample, with its reason. The counterfactual is
    # the informative part: "this one, and not those, and here is why".
    rejected_candidates: tuple[RejectedCandidate, ...]


class Instruction(BaseModel):
    """One edit request, resolving to exactly one element under ground truth."""

    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())

    instruction_id: str
    case_id: str
    svg_id: str

    family: str
    predicate: str
    operation: str
    operation_params: dict[str, Any]

    # What the model receives.
    text: str
    # Which wording, so per-template variance can be reported rather than assumed absent.
    template_id: str

    # GROUND TRUTH. Never present in any model-visible artefact.
    target_element_id: str
    # Ambiguity-set size, denormalised so the per-case 1/K reference needs no join.
    k: int = Field(ge=2)

    provenance: InstructionProvenance
