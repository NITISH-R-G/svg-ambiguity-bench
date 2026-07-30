"""Study V3 must feed other models exactly what V1 fed the reference model.

V3 compares new models against `qwen2.5-coder:3b`'s committed V1 numbers rather than
re-running that model. That comparison is only valid if the V3 harness reconstructs V1's
prompts exactly. It rebuilds them from the frozen ground truth through a separate code
path, so "exactly" is an assumption until asserted.

The failure this guards against is silent by construction: a geometry value differing in
the last decimal, or the analytic witness used where the raster one is canonical, would
produce a plausible context block, a plausible number, and an invalid comparison. Nothing
would error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from svgbench.context import build_provider
from svgbench.runner.prompt import build_prompt

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

pytestmark = pytest.mark.audit


def _v3_inputs():  # type: ignore[no-untyped-def]
    from study_v3_models import _load_frozen

    return _load_frozen()


def _v1_rows(arm: str) -> list[dict[str, object]]:
    root = REPO_ROOT / "experiments"
    matches = [p for p in root.iterdir() if p.is_dir() and p.name.startswith(f"main-{arm}")]
    if not matches:
        pytest.skip(f"no committed V1 responses for {arm}")
    with (matches[0] / "responses.jsonl").open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


@pytest.mark.parametrize(
    ("arm", "provider_name"), [("enhanced", "enhanced"), ("permuted", "permuted")]
)
def test_v3_reconstructs_v1_prompts_exactly(arm: str, provider_name: str) -> None:
    instructions, model_visible, geometry = _v3_inputs()
    by_case = {i.case_id: i for i in instructions}

    provider = build_provider(provider_name, 991)
    context = {svg_id: provider.provide(svg_id, g) for svg_id, g in geometry.items()}

    rows = _v1_rows(arm)
    assert rows, f"{arm}: no rows"

    for row in rows:
        instruction = by_case[str(row["case_id"])]
        rebuilt = build_prompt(
            svg=model_visible[instruction.svg_id],
            instruction=instruction.text,
            context=context[instruction.svg_id],
        )
        assert rebuilt == row["prompt"], (
            f"{arm}/{instruction.case_id}: V3 prompt differs from the committed V1 prompt. "
            "The cross-model comparison is invalid until this matches."
        )


def test_v3_baseline_reconstructs_v1_prompts_exactly() -> None:
    """Baseline carries no context, so this isolates the template and the SVG bytes."""
    instructions, model_visible, _ = _v3_inputs()
    by_case = {i.case_id: i for i in instructions}

    for row in _v1_rows("baseline"):
        instruction = by_case[str(row["case_id"])]
        rebuilt = build_prompt(
            svg=model_visible[instruction.svg_id], instruction=instruction.text, context=""
        )
        assert rebuilt == row["prompt"], f"baseline/{instruction.case_id}: prompt differs"


def test_permuted_differs_from_enhanced_on_every_svg() -> None:
    """The control must be a control. An identity permutation is a silent second treatment."""
    _, _, geometry = _v3_inputs()
    enhanced = build_provider("enhanced", 991)
    permuted = build_provider("permuted", 991)

    identical = [
        svg_id
        for svg_id, g in geometry.items()
        if enhanced.provide(svg_id, g) == permuted.provide(svg_id, g)
    ]
    assert not identical, f"permuted == enhanced for {identical}"


def test_frozen_geometry_uses_the_canonical_witness() -> None:
    """Canonical area is RASTER, not analytic (ADR-0004).

    Loading only the analytic witness would still produce a well-formed table, and the
    ordinal predicates would then be computed against a quantity the ground truth does
    not treat as canonical.
    """
    _, _, geometry = _v3_inputs()
    for elements in geometry.values():
        for element in elements.values():
            assert element.area == element.raster.area
            assert element.centroid == (element.raster.centroid_x, element.raster.centroid_y)
