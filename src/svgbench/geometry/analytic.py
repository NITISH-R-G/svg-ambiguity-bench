"""Analytic geometry: exact path algebra, no rendering.

Path data is parsed with `svgelements` rather than by hand, so this measurement starts
from an independent reading of the serialised document rather than from the generator's
own vertex list.

Honest scope note. The area and centroid formulas here are the same shoelace algebra
the generator uses. What differs is where the vertices come from: the generator's
in-memory blob, versus `svgelements` parsing the emitted `d` string. So comparing this
against generator intent is a SERIALISATION check - it catches rounding, formatting and
path-emission bugs. It is not an independent geometric witness. That role belongs to
the rasteriser.
"""

from __future__ import annotations

from svgelements import Path as SvgPath

from svgbench.geometry.records import PlaneGeometry


def _vertices(path_data: str) -> list[tuple[float, float]]:
    """Extract polygon vertices from a path.

    The corpus emits closed polylines (`M ... L ... Z`) only, so every segment endpoint
    is a vertex. Curves would need flattening; encountering one means the generator
    changed and this function must be revisited rather than silently approximating.
    """
    parsed = SvgPath(path_data)
    points: list[tuple[float, float]] = []
    for segment in parsed:
        end = getattr(segment, "end", None)
        if end is None:
            continue
        point = (float(end.x), float(end.y))
        if not points or point != points[-1]:
            points.append(point)

    # A closing `Z` repeats the start point; drop it so the polygon is not degenerate.
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()

    if len(points) < 3:
        raise ValueError(f"path does not describe a polygon: {path_data!r}")
    return points


def analytic_geometry(path_data: str) -> PlaneGeometry:
    """Exact area, area-centroid and bounding box.

    The centroid is the AREA centroid, not the vertex mean. They coincide for symmetric
    shapes and diverge for the asymmetric ones this corpus generates, and the spatial
    predicates (`leftmost`, `top_left`) are defined against the area centroid.
    """
    points = _vertices(path_data)

    doubled_area = 0.0
    cx = 0.0
    cy = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1], strict=True):
        cross = x1 * y2 - x2 * y1
        doubled_area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross

    if doubled_area == 0.0:
        raise ValueError(f"degenerate polygon with zero area: {path_data!r}")

    area = abs(doubled_area) / 2.0
    centroid_x = cx / (3.0 * doubled_area)
    centroid_y = cy / (3.0 * doubled_area)

    xs = [x for x, _ in points]
    ys = [y for _, y in points]

    return PlaneGeometry(
        area=area,
        centroid_x=centroid_x,
        centroid_y=centroid_y,
        bbox=(min(xs), min(ys), max(xs), max(ys)),
    )
