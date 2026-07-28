"""Evaluation engine tests, driven entirely by hand-authored fixtures.

Supports C4 (identification separable from execution) and C5 (abstention measured, not
punished).

Per `docs/verification-policy.md`, every expected verdict in `cases.json` was written
down - with its reasoning - before the scorer existed. The reasoning is asserted too, in
the sense that a fixture failing reports its own `reason`, so it is possible to tell
whether the scorer changed or the intent did.

The review question this suite has to answer is not "do the fixtures pass" but
**"can the scorer be wrong while every fixture still passes?"**
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from svgbench.evaluation import evaluate_response
from svgbench.evaluation.canonical import normalise_colour, normalise_rotation
from svgbench.evaluation.extract import detects_abstention, extract_svg

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "scoring" / "cases.json"
DATA = json.loads(FIXTURES.read_text(encoding="utf-8"))
CASES: list[dict[str, Any]] = DATA["cases"]
DOCUMENTS: dict[str, str] = DATA["documents"]


def _score(case: dict[str, Any]):  # type: ignore[no-untyped-def]
    return evaluate_response(
        case_id=case["name"],
        original_svg=DOCUMENTS[case["base"]],
        response=case["response"],
        operation=case["operation"],
        params=case["params"],
        target_element_id=case["target"],
    )


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_fixture_outcome(case: dict[str, Any]) -> None:
    result = _score(case)
    assert result.outcome == case["expected"], (
        f"{case['name']}: expected {case['expected']}, got {result.outcome}\n"
        f"  intent: {case['reason']}"
    )


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_fixture_target_edited(case: dict[str, Any]) -> None:
    result = _score(case)
    assert result.target_edited == case["target_edited"], (
        f"{case['name']}: target_edited\n  intent: {case['reason']}"
    )


@pytest.mark.parametrize("case", [c for c in CASES if "collateral" in c], ids=lambda c: c["name"])
def test_fixture_collateral(case: dict[str, Any]) -> None:
    result = _score(case)
    expected = sorted(case["collateral"])
    actual = sorted(i for i in result.collateral_element_ids if not i.startswith("__"))
    assert actual == expected, f"{case['name']}: collateral\n  intent: {case['reason']}"


@pytest.mark.parametrize(
    "case", [c for c in CASES if "target_edit_correct" in c], ids=lambda c: c["name"]
)
def test_fixture_execution_flag(case: dict[str, Any]) -> None:
    """The identification/execution split - the reason a single bit is not reported."""
    result = _score(case)
    assert result.target_edit_correct == case["target_edit_correct"], (
        f"{case['name']}: target_edit_correct\n  intent: {case['reason']}"
    )


@pytest.mark.parametrize(
    "case", [c for c in CASES if "alignment_tier" in c], ids=lambda c: c["name"]
)
def test_fixture_alignment_tier(case: dict[str, Any]) -> None:
    """Reliance on a weaker identity anchor must be visible, not silent."""
    result = _score(case)
    assert result.alignment_tier == case["alignment_tier"], (
        f"{case['name']}: alignment tier\n  intent: {case['reason']}"
    )


# ---------------------------------------------------------------------------
# Coverage of the fixture set itself
# ---------------------------------------------------------------------------


def test_every_outcome_class_has_a_fixture() -> None:
    """A class with no fixture is a class whose scoring is unverified."""
    covered = {c["expected"] for c in CASES}
    assert covered == {
        "CORRECT_STRICT",
        "CORRECT_LOOSE",
        "WRONG_TARGET",
        "ABSTAINED",
        "NO_EDIT",
        "MALFORMED",
    }, f"uncovered outcome classes: {covered}"


def test_every_operation_has_a_fixture() -> None:
    covered = {c["operation"] for c in CASES}
    assert covered == {"recolor_fill", "add_stroke", "delete", "rotate"}


def test_every_fixture_states_its_reasoning() -> None:
    """The reason is what lets a future failure be attributed to the scorer or the
    intent. A fixture without one is an assertion nobody can review."""
    for case in CASES:
        assert case.get("reason", "").strip(), f"{case['name']} has no reason"
        assert len(case["reason"]) > 40, f"{case['name']}: reason is too thin to be useful"


# ---------------------------------------------------------------------------
# Trying to make the scorer wrong while the fixtures still pass
# ---------------------------------------------------------------------------


def test_abstention_does_not_fire_on_ordinary_commentary() -> None:
    """The most dangerous false positive.

    If explanatory prose tripped the detector, every well-explained correct answer would
    be scored as a refusal - and the arm with the most verbose model would look the most
    calibrated.
    """
    for text in (
        "Here is the edited SVG. I changed the second path's fill to red.",
        "I have outlined the requested shape in black.",
        "Done - the smallest shape is now blue.",
        "The top-left shape has been rotated 90 degrees clockwise.",
    ):
        assert not detects_abstention(text), text


def test_abstention_fires_on_every_fixture_phrasing() -> None:
    for case in CASES:
        if case["expected"] == "ABSTAINED":
            assert detects_abstention(case["response"]), case["name"]


def test_colour_normalisation_is_not_overly_permissive() -> None:
    """Guards the opposite failure: treating distinct colours as equal would make every
    recolour succeed."""
    assert normalise_colour("#ff0000") != normalise_colour("#00ff00")
    assert normalise_colour("red") != normalise_colour("blue")
    assert normalise_colour("#00f") == normalise_colour("blue")
    assert normalise_colour("rgb(255, 0, 0)") == normalise_colour("red")


def test_rotation_modulo_does_not_collapse_distinct_angles() -> None:
    assert normalise_rotation("rotate(90)") == normalise_rotation("rotate(450)")
    assert normalise_rotation("rotate(90)") != normalise_rotation("rotate(45)")
    assert normalise_rotation("rotate(-90)") == normalise_rotation("rotate(270)")
    assert normalise_rotation("translate(10,10)") is None


def test_extraction_takes_the_last_complete_document() -> None:
    """A model that revises leaves the corrected version last."""
    response = "First attempt:\n<svg><path id='a'/></svg>\nActually:\n<svg><path id='b'/></svg>"
    extracted = extract_svg(response)
    assert extracted is not None
    assert "id='b'" in extracted


def test_scoring_is_deterministic() -> None:
    for case in CASES:
        assert _score(case).model_dump() == _score(case).model_dump()


def test_engine_signature_has_no_arm_parameter() -> None:
    """Arm-blindness enforced by the interface, not by discipline.

    An arm-dependent scoring rule cannot be written without changing this signature,
    which would be visible in review rather than buried in a branch.
    """
    import inspect

    parameters = set(inspect.signature(evaluate_response).parameters)
    for forbidden in ("arm", "provider", "context", "experiment_id", "config_hash"):
        assert forbidden not in parameters, f"scorer can see {forbidden!r}"
