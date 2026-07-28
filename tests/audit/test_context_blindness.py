"""Audit: the arms differ in exactly one variable, and `permuted` is a real control.

Supports C2 and C3. These are the checks the central claim rests on, so they are
mechanical rather than conventional.

The load-bearing one is `test_permuted_and_enhanced_are_format_identical`. `enhanced`
changes two things at once - it adds geometric facts, and it adds an enumerated list
giving every element a referential handle. If `permuted` differed in format as well as
content, it would not isolate the second, and `enhanced > permuted` would support
"a structured list helps" just as well as "geometry helps". Only the second is claimed.
"""

from __future__ import annotations

import re

import pytest

from svgbench.config import load_config
from svgbench.context import build_provider
from svgbench.geometry import ElementGeometry, PlaneGeometry
from svgbench.instructions import TARGET_PHRASES
from svgbench.runner import build_prompt

CONFIG_ROOT = None  # resolved per test via load_config


def _geometry(n: int = 5) -> dict[str, ElementGeometry]:
    """Distinct, unmistakable values so a permutation is detectable by eye."""
    out: dict[str, ElementGeometry] = {}
    for i in range(n):
        plane = PlaneGeometry(
            area=1000.0 * (i + 1),
            centroid_x=50.0 * (i + 1),
            centroid_y=70.0 * (i + 1),
            bbox=(0.0, 0.0, 10.0 * (i + 1), 10.0 * (i + 1)),
        )
        out[f"e{i:08d}"] = ElementGeometry(element_id=f"e{i:08d}", analytic=plane, raster=plane)
    return out


@pytest.mark.audit
def test_permuted_and_enhanced_are_format_identical() -> None:
    """Same shape, same columns, same row count - only the values move.

    If this fails, `permuted` stops being a format-matched control and C3 becomes
    untestable.
    """
    geometry = _geometry()
    enhanced = build_provider("enhanced", 0).provide("svg_x", geometry)
    permuted = build_provider("permuted", 991).provide("svg_x", geometry)

    assert enhanced.splitlines()[:2] == permuted.splitlines()[:2], "headers differ"
    assert len(enhanced.splitlines()) == len(permuted.splitlines()), "row counts differ"

    # Same element ids, in the same order, on the same lines.
    ids = re.compile(r"^\s+(e\d{8})")
    enhanced_ids = [m.group(1) for line in enhanced.splitlines() if (m := ids.match(line))]
    permuted_ids = [m.group(1) for line in permuted.splitlines() if (m := ids.match(line))]
    assert enhanced_ids == permuted_ids

    # Token counts must be close, or prompt length itself becomes a confound.
    assert abs(len(enhanced) - len(permuted)) <= 4


@pytest.mark.audit
def test_permuted_preserves_the_values_but_not_the_mapping() -> None:
    """The multiset of facts is identical; who owns them is destroyed."""
    geometry = _geometry()
    enhanced = build_provider("enhanced", 0).provide("svg_x", geometry)
    permuted = build_provider("permuted", 991).provide("svg_x", geometry)

    numbers = re.compile(r"-?\d+\.?\d*")
    assert sorted(numbers.findall(enhanced)) == sorted(numbers.findall(permuted))
    assert enhanced != permuted, "permutation was the identity - this arm is not a control"


@pytest.mark.audit
def test_permutation_is_never_the_identity() -> None:
    """A permutation that happens to be the identity silently turns this arm into
    `enhanced`, and the control would vanish without any test failing."""
    geometry = _geometry(4)
    for svg_id in [f"svg_{i:04d}" for i in range(40)]:
        enhanced = build_provider("enhanced", 0).provide(svg_id, geometry)
        permuted = build_provider("permuted", 991).provide(svg_id, geometry)
        assert enhanced != permuted, f"{svg_id}: permutation collapsed to identity"


@pytest.mark.audit
def test_context_is_identical_across_instructions_for_one_svg() -> None:
    """Blindness in practice.

    The provider signature has no instruction parameter, so this cannot fail by
    construction - which is exactly why it is worth asserting: if the signature ever
    gains one, this fails immediately.
    """
    geometry = _geometry()
    for name in ("null", "enhanced", "permuted", "ceiling"):
        provider = build_provider(name, 991)
        blocks = {provider.provide("svg_x", geometry) for _ in range(5)}
        assert len(blocks) == 1, f"{name}: context varied between calls"


@pytest.mark.audit
def test_enhanced_context_contains_no_predicate_vocabulary() -> None:
    """`enhanced` emits primitive facts only.

    Emitting "top-left" or "second largest" would turn the task into a dictionary
    lookup and measure the provider rather than the model. That condition exists
    separately as `ceiling`, excluded from the headline.
    """
    context = build_provider("enhanced", 0).provide("svg_x", _geometry()).lower()
    for predicate, phrases in TARGET_PHRASES.items():
        assert predicate.replace("_", " ") not in context, predicate
        for phrase in phrases:
            assert phrase.lower() not in context, phrase
    for word in ("largest", "smallest", "leftmost", "rightmost", "top-left", "rank"):
        assert word not in context, word


@pytest.mark.audit
def test_ceiling_does_leak_labels_and_is_therefore_excluded() -> None:
    """Confirms `ceiling` is what it claims to be.

    If it did NOT contain labels it would be a second `enhanced` arm masquerading as a
    diagnostic, and the residual-error analysis would be meaningless.
    """
    context = build_provider("ceiling", 0).provide("svg_x", _geometry()).lower()
    assert "rank" in context
    assert "leftmost" in context


@pytest.mark.audit
def test_prompts_differ_only_in_the_context_slot() -> None:
    """A mechanical diff between arms, which is the strongest form of the C2 guarantee.

    Every line outside the injected block must be identical across arms.
    """
    geometry = _geometry()
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><path id="e1" d="{{GEOM_aaaaaaaa}}"/></svg>'
    instruction = "Change the fill of the top-left shape to #ff0000."

    baseline = build_prompt(svg, instruction, "")

    for name in ("enhanced", "permuted", "ceiling"):
        context = build_provider(name, 991).provide("s", geometry)
        prompt = build_prompt(svg, instruction, context)

        # Excise exactly the injected block, including the newlines the template wraps
        # it in. What remains must be byte-identical to the baseline prompt. This is
        # stronger than comparing filtered lines: it proves the template contributed
        # nothing beyond the slot.
        assert f"\n{context}\n" in prompt, f"{name}: context block not found verbatim"
        stripped = prompt.replace(f"\n{context}\n", "", 1)
        assert stripped == baseline, (
            f"{name} differs from baseline outside the context slot:\n"
            f"  stripped: {stripped!r}\n  baseline: {baseline!r}"
        )


@pytest.mark.audit
def test_baseline_prompt_carries_no_context_at_all() -> None:
    geometry = _geometry()
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><path id="e1" d="{{GEOM_aaaaaaaa}}"/></svg>'
    prompt = build_prompt(
        svg, "Delete the largest shape.", build_provider("null", 0).provide("s", geometry)
    )
    assert "centre_x" not in prompt
    assert "Element geometry" not in prompt


@pytest.mark.audit
def test_shipped_arm_configs_select_distinct_providers() -> None:
    """The config files and the provider registry must agree."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    base = root / "configs" / "base.yaml"
    providers = {}
    for path in sorted((root / "configs" / "experiments").glob("main-*.yaml")):
        config = load_config(base, path).config
        providers[path.stem] = build_provider(
            config.context.provider, config.context.permutation_seed
        ).name
    assert len(set(providers.values())) == len(providers), providers
