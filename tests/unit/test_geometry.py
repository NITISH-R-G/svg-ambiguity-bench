"""Geometry engine tests, written as falsification attempts.

Supports claim C7: ground truth is correct, not merely asserted.

This is the first module that can invalidate the entire benchmark. Every predicate -
`top_left`, `second_largest`, `leftmost` - resolves against numbers this module
produces. If they are wrong, every downstream measurement is wrong in a way no later
test would catch, because the benchmark would be internally consistent and externally
false.

So these tests do not ask "does it work". They ask what observation would convince us
it is broken:

  F1  a known shape returns the wrong answer
  F2  analytic and raster disagree on the RANKING of one ambiguity set
  F3  translating a shape changes its measured area or bbox size
  F4  area rank changes with raster resolution
  F5  isolated per-element coverage does not sum to full-document coverage
  F6  area-centroid confused with vertex mean or bbox centre
  F7  relative error correlates with shape size (size-dependent AA bias)
  F8  witnesses disagree on the real corpus

F2 is the one that matters most: the ordinal family needs an ORDERING, not an area.
Two engines could agree on ranks while differing by 2% on every absolute value, and the
benchmark would be entirely sound.

A note on independence. Generator intent and analytic geometry both use the shoelace
formula, differing only in whether the vertices came from the generator or from parsing
the serialised path string. That pair is a SERIALISATION check. The genuinely
independent witness is the rasteriser: different language, different algorithm,
different failure modes.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.generation import generate_corpus
from svgbench.geometry import (
    GeometryDisagreementError,
    analytic_geometry,
    measure_document,
    raster_geometry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"

SQUARE = "M 10 10 L 60 10 L 60 60 L 10 60 Z"
# Right triangle, legs 40. Area 800. Area-centroid is at (1/3, 1/3) of the legs from
# the right angle - deliberately NOT the vertex mean, which is the same here, so a
# second asymmetric shape is used for F6.
TRIANGLE = "M 0 0 L 40 0 L 0 40 Z"
# Thin L-shape. Vertex mean and area centroid differ substantially.
ELL = "M 0 0 L 60 0 L 60 10 L 10 10 L 10 60 L 0 60 Z"


def _document(paths: list[str], size: int = 128) -> str:
    shapes = "\n".join(f'  <path id="p{i}" d="{d}" fill="#3b6ea5"/>' for i, d in enumerate(paths))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">\n{shapes}\n</svg>\n'
    )


# ---------------------------------------------------------------------------
# F1 - known answers
# ---------------------------------------------------------------------------


def test_analytic_square_is_exact() -> None:
    g = analytic_geometry(SQUARE)
    assert g.area == pytest.approx(2500.0, abs=1e-6)
    assert g.bbox == pytest.approx((10.0, 10.0, 60.0, 60.0), abs=1e-6)
    assert (g.centroid_x, g.centroid_y) == pytest.approx((35.0, 35.0), abs=1e-6)


def test_analytic_triangle_is_exact() -> None:
    g = analytic_geometry(TRIANGLE)
    assert g.area == pytest.approx(800.0, abs=1e-6)
    # Centroid of a triangle is the mean of its vertices: (40/3, 40/3).
    assert (g.centroid_x, g.centroid_y) == pytest.approx((40 / 3, 40 / 3), abs=1e-6)


def test_raster_square_is_exact_to_a_pixel() -> None:
    """The probe that justified this rendering stack in ADR-0001."""
    g = raster_geometry(_document([SQUARE]), "p0", canvas_size=128, scale=1)
    assert g.area == pytest.approx(2500.0, rel=0.02)
    assert (g.centroid_x, g.centroid_y) == pytest.approx((35.0, 35.0), abs=0.5)
    assert g.bbox == pytest.approx((10.0, 10.0, 60.0, 60.0), abs=1.0)


# ---------------------------------------------------------------------------
# F6 - centroid definition
# ---------------------------------------------------------------------------


def test_area_centroid_is_not_the_vertex_mean() -> None:
    """`leftmost` uses the centroid, so the definition has to be the right one.

    For the L-shape the two differ by a wide margin. An engine returning the vertex
    mean would pass every symmetric-shape test and be wrong on exactly the asymmetric
    shapes this corpus generates.
    """
    g = analytic_geometry(ELL)
    vertices = [(0, 0), (60, 0), (60, 10), (10, 10), (10, 60), (0, 60)]
    vertex_mean_x = sum(x for x, _ in vertices) / len(vertices)

    # Area centroid of the L: two rectangles, 60x10 at (30,5) and 10x50 at (5,35).
    expected_x = (600 * 30 + 500 * 5) / 1100
    expected_y = (600 * 5 + 500 * 35) / 1100

    assert g.area == pytest.approx(1100.0, abs=1e-6)
    assert g.centroid_x == pytest.approx(expected_x, abs=1e-6)
    assert g.centroid_y == pytest.approx(expected_y, abs=1e-6)
    assert abs(g.centroid_x - vertex_mean_x) > 1.0, "test shape fails to separate the definitions"


def test_raster_centroid_agrees_with_the_area_centroid() -> None:
    """Pixel coverage is an area measure, so its centroid must be the area centroid."""
    analytic = analytic_geometry(ELL)
    raster = raster_geometry(_document([ELL]), "p0", canvas_size=128, scale=4)
    assert raster.centroid_x == pytest.approx(analytic.centroid_x, abs=0.5)
    assert raster.centroid_y == pytest.approx(analytic.centroid_y, abs=0.5)


# ---------------------------------------------------------------------------
# F3 - invariance under transformations that must not change the measurement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("offset", [1.0, 7.5, 23.25, 40.0])
def test_translation_does_not_change_measured_area(offset: float) -> None:
    """If area moves with position, the engine is measuring a grid artifact.

    The instrument analogue of SGP-Bench's semantic-consistency perturbation
    (arXiv 2408.08313): apply a transformation that must preserve the quantity, and
    check that it does.
    """
    base = raster_geometry(_document([SQUARE]), "p0", canvas_size=128, scale=2)
    moved_path = " ".join(
        f"{float(t) + offset:.3f}" if t.replace(".", "").isdigit() else t for t in SQUARE.split()
    )
    moved = raster_geometry(_document([moved_path]), "p0", canvas_size=128, scale=2)

    assert moved.area == pytest.approx(base.area, rel=0.02)
    assert moved.bbox[2] - moved.bbox[0] == pytest.approx(base.bbox[2] - base.bbox[0], abs=1.0)
    assert moved.centroid_x == pytest.approx(base.centroid_x + offset, abs=0.5)


def test_doubling_linear_size_quadruples_area() -> None:
    small = analytic_geometry("M 0 0 L 10 0 L 10 10 L 0 10 Z")
    large = analytic_geometry("M 0 0 L 20 0 L 20 20 L 0 20 Z")
    assert large.area == pytest.approx(4 * small.area, rel=1e-9)


# ---------------------------------------------------------------------------
# F2 and F4 - ranking, which is what the ordinal family actually needs
# ---------------------------------------------------------------------------


def test_analytic_and_raster_agree_on_ranking(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """The falsifier that matters most.

    Absolute areas may differ by a couple of percent without harming anything. A single
    rank disagreement means `second_largest` has no well-defined answer for that sample.
    """
    for sample in shipped_corpus:
        measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
        members = [e.element_id for e in sample.ambiguity_elements]

        by_analytic = sorted(members, key=lambda i: measured[i].analytic.area, reverse=True)
        by_raster = sorted(members, key=lambda i: measured[i].raster.area, reverse=True)
        assert by_analytic == by_raster, f"{sample.svg_id}: rank disagreement"


def test_ranking_is_independent_of_raster_resolution(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """If rank moves with resolution, canonical area is a rendering artifact."""
    for sample in shipped_corpus[:8]:
        members = [e.element_id for e in sample.ambiguity_elements]
        rankings = []
        for scale in (1, 2):
            measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=scale)
            rankings.append(sorted(members, key=lambda i: measured[i].raster.area, reverse=True))
        assert rankings[0] == rankings[1], f"{sample.svg_id}: rank changed with resolution"


# ---------------------------------------------------------------------------
# F5 - attribution and pixel-level non-overlap
# ---------------------------------------------------------------------------


def test_isolated_coverages_sum_to_the_whole_document(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """Turns the non-overlap guarantee into a rendered-pixel fact.

    The generator checks non-overlap by centre distance against bounding radii, which
    is conservative but blind to what the renderer actually draws. If isolated
    coverages exceed the whole-document coverage, shapes overlap in pixels and every
    rasterised area is contaminated by occlusion.
    """
    from svgbench.geometry import document_coverage

    for sample in shipped_corpus[:8]:
        measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
        summed = sum(m.raster.area for m in measured.values())
        whole = document_coverage(sample.resolved_svg, sample.canvas_size, scale=1)
        assert summed == pytest.approx(whole, rel=0.01), (
            f"{sample.svg_id}: isolated sum {summed:.0f} vs document {whole:.0f} - shapes overlap"
        )


# ---------------------------------------------------------------------------
# F7 - size-dependent bias would compress the ranking
# ---------------------------------------------------------------------------


def test_relative_error_does_not_grow_with_shape_size(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """Anti-aliasing error scales with perimeter, so small shapes have a worse
    perimeter-to-area ratio. A systematic size-dependent bias could flip adjacent
    ranks, which is precisely what the ordinal family cannot tolerate.
    """
    small_errors: list[float] = []
    large_errors: list[float] = []
    for sample in shipped_corpus[:10]:
        measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
        for element in sample.ambiguity_elements:
            m = measured[element.element_id]
            error = (m.raster.area - m.analytic.area) / m.analytic.area
            (small_errors if m.analytic.area < 4000 else large_errors).append(error)

    assert small_errors, "corpus contained no small shapes, so the test proves nothing"
    assert large_errors, "corpus contained no large shapes, so the test proves nothing"
    drift = abs(sum(small_errors) / len(small_errors) - sum(large_errors) / len(large_errors))
    assert drift < 0.02, f"relative error drifts with size by {drift:.4f}"


# ---------------------------------------------------------------------------
# F8 - witness agreement on the real corpus
# ---------------------------------------------------------------------------


def test_serialisation_preserves_generator_intent(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """Intent vs analytic. Both use the shoelace formula, so this checks that the
    emitted path STRING faithfully encodes what the generator meant - a serialisation
    and rounding check, not an independent geometric one."""
    for sample in shipped_corpus[:10]:
        measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
        for element in sample.elements:
            analytic = measured[element.element_id].analytic
            assert analytic.area == pytest.approx(element.area, rel=1e-6)


def test_area_centroid_differs_from_the_placement_anchor(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """The generator's placement anchor is NOT the area centroid, and must not be
    mistaken for one.

    Vertex radii are jittered, so an irregular blob's area centroid drifts from the
    point it was constructed around. Asserting equality here is what surfaced the
    original `center_x` misnaming: every spatial predicate would have used the anchor,
    been wrong by a few user units, and stayed internally consistent while doing so.

    The true invariant is weaker and actually holds: the centroid lies inside the
    shape's bounding circle. It is asserted so a future change that decouples the two
    entirely still fails.
    """
    drifts: list[float] = []
    for sample in shipped_corpus[:10]:
        measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
        for element in sample.elements:
            analytic = measured[element.element_id].analytic
            drift = math.dist(
                (analytic.centroid_x, analytic.centroid_y),
                (element.placement_x, element.placement_y),
            )
            assert drift < element.bounding_radius, f"{element.element_id}: centroid outside shape"
            drifts.append(drift)

    assert max(drifts) > 1.0, (
        "placement anchor and area centroid never diverge in this corpus, so this test "
        "cannot catch the confusion it exists to catch"
    )


def test_engine_rejects_a_sample_whose_witnesses_disagree() -> None:
    """A tolerance that never triggers is not a tolerance.

    Feeds a document whose analytic and rasterised areas cannot agree - a shape far
    outside the viewBox, so the renderer sees almost nothing while the path algebra
    sees a full-size polygon.
    """
    offscreen = "M 900 900 L 960 900 L 960 960 L 900 960 Z"
    with pytest.raises(GeometryDisagreementError):
        measure_document(_document([offscreen]), canvas_size=128, scale=1, strict=True)


@pytest.fixture(scope="module")
def shipped_corpus():  # type: ignore[no-untyped-def]
    return generate_corpus(load_config(BASE, overrides={"generation.n_svgs": 10}).config)
