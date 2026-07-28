"""Cross-validated measurement of a whole document.

Supports claim C7: ground truth is correct, not merely asserted.

Both witnesses measure every element and must agree. Disagreement beyond tolerance
rejects the sample rather than widening the tolerance - the guarantee is only worth
something if it can fail.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from svgbench.geometry.analytic import analytic_geometry
from svgbench.geometry.raster import raster_geometry
from svgbench.geometry.records import ElementGeometry, GeometryDisagreementError

SVG_NS = "{http://www.w3.org/2000/svg}"

# Tolerances are properties of the INSTRUMENT, calibrated against known shapes and the
# observed agreement distribution, and fixed before any model runs. Calibrating a
# measuring device against its own noise is not the same as tuning a scoring rule to a
# result; moving these later is an amendment under DESIGN_FREEZE.md.
#
# Measured on 110 elements: median relative area disagreement 0.0001, max 0.0014;
# median centroid disagreement 0.005 user units, max 0.030. The bounds below leave
# roughly 14x headroom over the observed maximum - loose enough to absorb renderer
# version differences and shapes with worse perimeter-to-area ratios, tight enough that
# a genuinely broken measurement cannot slip through. An earlier 0.05 bound was 35x the
# observed maximum, which would have accepted almost any degradation.
#
# These are a backstop, not the operative gate. The gate that matters is rank
# agreement: the ordinal family needs an ORDERING, and two witnesses can differ on
# every absolute value while agreeing completely on the ordering.
DEFAULT_AREA_TOLERANCE = 0.02
DEFAULT_CENTROID_TOLERANCE = 0.5


def measure_document(
    svg_text: str,
    canvas_size: int,
    scale: int = 1,
    strict: bool = False,
    area_tolerance: float = DEFAULT_AREA_TOLERANCE,
    centroid_tolerance: float = DEFAULT_CENTROID_TOLERANCE,
) -> dict[str, ElementGeometry]:
    """Measure every shape with both witnesses, keyed by element id.

    Args:
        strict: raise `GeometryDisagreementError` when the witnesses disagree beyond
            tolerance. Off by default so callers can inspect disagreement; the
            ground-truth engine turns it on, because a contested measurement must not
            become a benchmark case.

    Raises:
        GeometryDisagreementError: under `strict`, when a witness pair disagrees.
    """
    root = ET.fromstring(svg_text)
    measured: dict[str, ElementGeometry] = {}

    for child in root:
        if child.tag != f"{SVG_NS}path":
            continue
        element_id = child.get("id")
        path_data = child.get("d")
        if element_id is None or path_data is None:
            raise ValueError("every shape must carry both an id and path data")

        geometry = ElementGeometry(
            element_id=element_id,
            analytic=analytic_geometry(path_data),
            raster=raster_geometry(svg_text, element_id, canvas_size, scale),
        )

        if strict:
            _check_agreement(geometry, area_tolerance, centroid_tolerance)

        measured[element_id] = geometry

    return measured


def _check_agreement(
    geometry: ElementGeometry,
    area_tolerance: float,
    centroid_tolerance: float,
) -> None:
    if geometry.relative_area_disagreement > area_tolerance:
        raise GeometryDisagreementError(
            f"{geometry.element_id}: area disagreement "
            f"{geometry.relative_area_disagreement:.4f} exceeds {area_tolerance} "
            f"(analytic {geometry.analytic.area:.1f}, raster {geometry.raster.area:.1f})"
        )
    if geometry.centroid_disagreement > centroid_tolerance:
        raise GeometryDisagreementError(
            f"{geometry.element_id}: centroid disagreement "
            f"{geometry.centroid_disagreement:.3f} exceeds {centroid_tolerance}"
        )


def area_ranking(measured: dict[str, ElementGeometry], element_ids: list[str]) -> list[str]:
    """Element ids ordered largest first by canonical area.

    The ordinal predicates need this ordering, not the areas themselves. Two witnesses
    may differ by a few percent on every absolute value and still agree completely here,
    which is the agreement that actually matters.
    """
    return sorted(element_ids, key=lambda i: measured[i].area, reverse=True)


def witnesses_agree_on_ranking(
    measured: dict[str, ElementGeometry],
    element_ids: list[str],
) -> bool:
    """Whether both witnesses produce the same ordering.

    A single disagreement means `second_largest` has no well-defined answer for that
    sample, so the sample cannot become a benchmark case.
    """
    by_raster = sorted(element_ids, key=lambda i: measured[i].raster.area, reverse=True)
    by_analytic = sorted(element_ids, key=lambda i: measured[i].analytic.area, reverse=True)
    return by_raster == by_analytic
