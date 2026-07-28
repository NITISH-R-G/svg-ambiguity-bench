"""Audit: can the scorer be wrong while every fixture still passes?

The review gate for Step 9, from `docs/verification-policy.md`. "The fixtures pass" is
not evidence that the fixtures are adequate - a fixture set can pass against a scorer
that is wrong in ways no fixture happens to exercise.

So the scorer is deliberately broken, nine ways, and each break must be caught by at
least one fixture. A surviving mutation is a hole in the fixture set and must be closed
by adding a fixture, not by narrowing the mutation.

This matters more than the fixture count. Every claim after the pre-registration tag
depends on the scorer being right, and unlike a lint, a wrong scorer does not crash -
it produces a plausible number.

Patching note: the modules use `from X import Y`, which copies the reference. A mutation
has to replace the binding in every module that imported it, not only where it was
defined. Getting that wrong yields false "not caught" results - which understates the
fixtures rather than overstating them, but is still wrong, and did happen while writing
this.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "scoring" / "cases.json"

canonical = importlib.import_module("svgbench.evaluation.canonical")
classify_module = importlib.import_module("svgbench.evaluation.classify")
engine = importlib.import_module("svgbench.evaluation.engine")
extract = importlib.import_module("svgbench.evaluation.extract")
align_module = importlib.import_module("svgbench.evaluation.align")

DATA = json.loads(FIXTURES.read_text(encoding="utf-8"))
CASES: list[dict[str, Any]] = DATA["cases"]
DOCUMENTS: dict[str, str] = DATA["documents"]


def _fixture_failures() -> list[str]:
    """Names of fixtures whose expectations the current scorer violates."""
    failures: list[str] = []
    for case in CASES:
        try:
            result = engine.evaluate_response(
                case_id=case["name"],
                original_svg=DOCUMENTS[case["base"]],
                response=case["response"],
                operation=case["operation"],
                params=case["params"],
                target_element_id=case["target"],
            )
            ok = (
                result.outcome == case["expected"] and result.target_edited == case["target_edited"]
            )
            if "collateral" in case:
                actual = sorted(i for i in result.collateral_element_ids if not i.startswith("__"))
                ok = ok and actual == sorted(case["collateral"])
            if "target_edit_correct" in case:
                ok = ok and result.target_edit_correct == case["target_edit_correct"]
            if "alignment_tier" in case:
                ok = ok and result.alignment_tier == case["alignment_tier"]
        except Exception:
            # A crash counts as the mutation being caught: the scorer must fail
            # visibly rather than return a plausible number.
            ok = False
        if not ok:
            failures.append(case["name"])
    return failures


def _patch(modules: list[Any], name: str, replacement: Any) -> Callable[[], None]:
    saved = [(m, getattr(m, name)) for m in modules if hasattr(m, name)]
    for module, _ in saved:
        setattr(module, name, replacement)

    def undo() -> None:
        for module, original in saved:
            setattr(module, name, original)

    return undo


def _mutate_no_colour_normalisation() -> Callable[[], None]:
    return _patch([canonical, classify_module], "normalise_colour", lambda v: v.strip().lower())


def _mutate_no_rotation_modulo() -> Callable[[], None]:
    def raw(transform: str) -> float | None:
        if "rotate(" not in transform.lower():
            return None
        return float(transform.lower().split("rotate(")[1].split(")")[0].split(",")[0])

    return _patch([canonical, classify_module], "normalise_rotation", raw)


def _mutate_compare_all_attributes() -> Callable[[], None]:
    original = canonical.RENDERING_ATTRIBUTES
    canonical.RENDERING_ATTRIBUTES = frozenset(original | {"data-note", "id", "class"})

    def undo() -> None:
        canonical.RENDERING_ATTRIBUTES = original

    return undo


def _mutate_abstention_checked_last() -> Callable[[], None]:
    original = engine.detects_abstention
    return _patch(
        [engine],
        "detects_abstention",
        lambda r: original(r) and extract.extract_svg(r) is None,
    )


def _mutate_silence_is_abstention() -> Callable[[], None]:
    original = engine.detects_abstention
    return _patch([engine], "detects_abstention", lambda r: original(r) or not r.strip())


def _mutate_execution_folded_into_identification() -> Callable[[], None]:
    def loose(operation: str, params: Any, original: Any, returned: Any, tol: float) -> bool:
        if operation == "delete":
            return returned is None
        return returned is not None and canonical.differs(
            dict(original.attrib), dict(returned.attrib), tol
        )

    return _patch([classify_module, engine], "edit_is_correct", loose)


def _mutate_deletion_is_absence() -> Callable[[], None]:
    original = classify_module.edit_is_correct

    def strict(operation: str, params: Any, source: Any, returned: Any, tol: float) -> bool:
        if operation == "delete":
            return False
        return bool(original(operation, params, source, returned, tol))

    return _patch([classify_module, engine], "edit_is_correct", strict)


def _mutate_ignore_numeric_tolerance() -> Callable[[], None]:
    def strict(name: str, left: str, right: str, _tol: float) -> bool:
        if name in {"fill", "stroke"}:
            return bool(canonical.normalise_colour(left) == canonical.normalise_colour(right))
        return left.strip() == right.strip()

    return _patch([canonical, classify_module], "values_equal", strict)


def _mutate_align_by_position_only() -> Callable[[], None]:
    def positional(original: list[Any], returned: list[Any]) -> tuple[dict[str, Any], str]:
        mapping = {
            source.get("id", f"__index_{i}"): (returned[i] if i < len(returned) else None)
            for i, source in enumerate(original)
        }
        return mapping, "POSITION"

    return _patch([align_module, engine], "align", positional)


MUTATIONS: list[tuple[str, Callable[[], Callable[[], None]]]] = [
    ("no colour normalisation", _mutate_no_colour_normalisation),
    ("no rotation modulo", _mutate_no_rotation_modulo),
    ("compare all attributes", _mutate_compare_all_attributes),
    ("abstention checked last", _mutate_abstention_checked_last),
    ("silence counts as abstention", _mutate_silence_is_abstention),
    ("execution folded into identification", _mutate_execution_folded_into_identification),
    ("deletion treated as absence", _mutate_deletion_is_absence),
    ("numeric tolerance ignored", _mutate_ignore_numeric_tolerance),
    ("align by position only", _mutate_align_by_position_only),
]


@pytest.mark.audit
def test_fixtures_pass_against_the_real_scorer() -> None:
    """The baseline the mutation results are measured against."""
    assert _fixture_failures() == []


@pytest.mark.audit
@pytest.mark.parametrize(("label", "mutate"), MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_mutation_is_caught(label: str, mutate: Callable[[], Callable[[], None]]) -> None:
    """Each deliberate break must be noticed by at least one fixture."""
    undo = mutate()
    try:
        failures = _fixture_failures()
    finally:
        undo()

    assert failures, (
        f"mutation '{label}' survived: the scorer can be wrong this way while every "
        f"fixture still passes. Add a fixture that distinguishes it."
    )


@pytest.mark.audit
def test_undo_restores_the_scorer() -> None:
    """Guards the harness itself.

    If a mutation leaked, later tests in the session would score against a broken
    scorer and the whole suite would be measuring the wrong thing.
    """
    for _, mutate in MUTATIONS:
        mutate()()
    assert _fixture_failures() == []
