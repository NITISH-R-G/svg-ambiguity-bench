"""The evaluation engine: parse, align, diff, classify.

Supports C4 (identification separable from execution) and C5 (abstention measured, not
punished).

Deterministic, offline, and **arm-blind**: nothing here receives or can infer which
context provider produced a response. That is not a convention - the function signature
has no arm parameter, so an arm-dependent scoring rule cannot be written without
changing the interface, which would be visible in review.

Malformed and abstained responses are scored, never discarded. Denominators are fixed
at freeze time, so a response that cannot be parsed consumes a case rather than
vanishing from it.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from svgbench.evaluation.align import align, unmatched_returned
from svgbench.evaluation.canonical import differs
from svgbench.evaluation.classify import classify, edit_is_correct
from svgbench.evaluation.extract import detects_abstention, extract_svg, parse_elements
from svgbench.evaluation.records import EvaluationResult


def evaluate_response(
    case_id: str,
    original_svg: str,
    response: str,
    operation: str,
    params: dict[str, Any],
    target_element_id: str,
    numeric_tolerance: float = 1e-6,
) -> EvaluationResult:
    """Score one response against the original document and the intended edit."""
    # Abstention first, deliberately. A model that explains why it cannot answer and
    # returns the document unedited has refused, not produced a no-op. Checking the
    # document first would downgrade that to NO_EDIT and penalise a model for
    # explaining itself.
    if detects_abstention(response):
        return EvaluationResult(
            case_id=case_id,
            outcome="ABSTAINED",
            target_edited=False,
            target_edit_correct=False,
            alignment_tier="FAILED",
        )

    extracted = extract_svg(response)
    if extracted is None:
        return _malformed(case_id, "no <svg> element in the response")

    returned_elements = parse_elements(extracted)
    if returned_elements is None:
        return _malformed(case_id, "response is not well-formed XML")

    original_elements = parse_elements(original_svg)
    if original_elements is None:  # pragma: no cover - the corpus is validated at freeze
        raise ValueError(f"{case_id}: the frozen original does not parse")

    mapping, tier = align(original_elements, returned_elements)

    if all(match is None for match in mapping.values()):
        return _malformed(case_id, "no element could be matched to the original")

    by_id: dict[str, ET.Element] = {
        element.get("id", f"__index_{index}"): element
        for index, element in enumerate(original_elements)
    }
    if target_element_id not in by_id:  # pragma: no cover - guaranteed by the corpus
        raise ValueError(f"{case_id}: target {target_element_id} absent from the original")

    target_returned = mapping[target_element_id]
    target_edit_correct = edit_is_correct(
        operation, params, by_id[target_element_id], target_returned, numeric_tolerance
    )
    target_changed = _changed(
        by_id[target_element_id], target_returned, operation, numeric_tolerance
    )

    collateral = [
        element_id
        for element_id, returned in mapping.items()
        if element_id != target_element_id
        and _changed(by_id[element_id], returned, "none", numeric_tolerance)
    ]
    # An element the model invented is a change to the document too.
    invented = unmatched_returned(original_elements, returned_elements, mapping)
    collateral.extend(f"__invented_{i}" for i in range(len(invented)))

    predicted = ([target_element_id] if target_changed else []) + collateral

    return EvaluationResult(
        case_id=case_id,
        outcome=classify(target_edit_correct, target_changed, collateral),
        target_edited=target_changed,
        target_edit_correct=target_edit_correct,
        collateral_element_ids=tuple(sorted(collateral)),
        predicted_target_ids=tuple(sorted(predicted)),
        alignment_tier=tier,
    )


def _changed(
    original: ET.Element,
    returned: ET.Element | None,
    operation: str,
    tolerance: float,
) -> bool:
    """Whether an element differs in any rendering-relevant way.

    Absence counts as a change everywhere except where deletion was requested, which is
    handled by `edit_is_correct` rather than here.
    """
    if returned is None:
        return True
    if operation == "delete":
        return False
    return differs(dict(original.attrib), dict(returned.attrib), tolerance)


def _malformed(case_id: str, reason: str) -> EvaluationResult:
    return EvaluationResult(
        case_id=case_id,
        outcome="MALFORMED",
        target_edited=False,
        target_edit_correct=False,
        alignment_tier="FAILED",
        malformed_reason=reason,
    )
