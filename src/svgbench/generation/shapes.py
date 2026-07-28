"""Shape synthesis and placement.

Shapes are irregular polygons ("blobs") rather than rectangles or circles, for two
reasons that both serve claim C1:

  - A rectangle's path data is trivially readable as a position by anyone who glances
    at it, so redaction would be doing more work than the design admits.
  - Irregular outlines make analytic and rasterised area genuinely distinct
    measurements, which is what gives the two-witness check at step 5 something to
    disagree about.

Area is controlled directly: a unit blob is generated, its area computed by the
shoelace formula, then scaled to hit a target. Ordinal predicates need an uncontested
ordering, and sampling radii and hoping for well-separated areas would reject far too
often.

This module deliberately does not import the geometry engine. The generator's beliefs
must stay independent of the measurement that will later be used to verify them.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# Vertex count range. Few enough to stay convex-ish and non-self-intersecting, many
# enough that the outline is not recognisably a regular polygon.
_MIN_VERTICES = 5
_MAX_VERTICES = 9

# Angular jitter as a fraction of the gap between evenly spaced vertices. Below 0.5,
# so vertices cannot reorder and produce a self-intersecting path - a self-intersecting
# outline would make analytic and rasterised area disagree by construction and would
# fail the step-5 witness check for a reason unrelated to the corpus.
_ANGLE_JITTER = 0.35
_RADIUS_JITTER = (0.75, 1.25)

# Coordinates are emitted at fixed precision so the corpus hashes identically across
# platforms. Three decimals is far finer than the raster grid.
_COORD_PRECISION = 3


@dataclass(frozen=True)
class Blob:
    """A placed polygon, with the generator's belief about its own geometry."""

    vertices: tuple[tuple[float, float], ...]
    placement_x: float
    placement_y: float
    area: float
    bounding_radius: float

    def to_path_data(self) -> str:
        head, *rest = self.vertices
        parts = [f"M {_fmt(head[0])} {_fmt(head[1])}"]
        parts.extend(f"L {_fmt(x)} {_fmt(y)}" for x, y in rest)
        parts.append("Z")
        return " ".join(parts)


def _fmt(value: float) -> str:
    return f"{value:.{_COORD_PRECISION}f}"


def polygon_area(vertices: tuple[tuple[float, float], ...]) -> float:
    """Shoelace formula. Absolute value, so winding direction does not matter."""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(vertices, vertices[1:] + vertices[:1], strict=True):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def _unit_blob(rng: random.Random) -> tuple[tuple[float, float], ...]:
    """A closed polygon centred near the origin, with area on the order of 1."""
    n = rng.randint(_MIN_VERTICES, _MAX_VERTICES)
    step = 2.0 * math.pi / n
    vertices: list[tuple[float, float]] = []
    for i in range(n):
        angle = i * step + rng.uniform(-_ANGLE_JITTER, _ANGLE_JITTER) * step
        radius = rng.uniform(*_RADIUS_JITTER)
        vertices.append((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(vertices)


def make_blob(rng: random.Random, target_area: float, center: tuple[float, float]) -> Blob:
    """Generate a blob with the requested area, centred at `center`."""
    unit = _unit_blob(rng)
    scale = math.sqrt(target_area / polygon_area(unit))

    cx, cy = center
    placed = tuple((cx + x * scale, cy + y * scale) for x, y in unit)

    # Rounded exactly as they will be serialised, so the recorded intent describes the
    # emitted document rather than an unrounded ideal of it.
    placed = tuple((round(x, _COORD_PRECISION), round(y, _COORD_PRECISION)) for x, y in placed)

    return Blob(
        vertices=placed,
        placement_x=cx,
        placement_y=cy,
        area=polygon_area(placed),
        bounding_radius=max(math.dist((cx, cy), v) for v in placed),
    )


def target_areas(rng: random.Random, count: int, min_ratio: float, base: float) -> list[float]:
    """Areas guaranteed to be separated by at least `min_ratio` between adjacent ranks.

    Constructed rather than sampled. Rejection sampling for a well-separated ordering
    succeeds rarely as `count` grows, and the rejections would bias which layouts
    survive in a way that is hard to characterise.
    """
    areas = [base]
    for _ in range(count - 1):
        # A margin above the minimum, so the ordering survives the small difference
        # between intended and rasterised area.
        areas.append(areas[-1] * rng.uniform(min_ratio * 1.08, min_ratio * 1.45))
    return areas


class PlacementError(RuntimeError):
    """Raised when non-overlapping placement could not be achieved.

    Handled by regenerating the whole sample with a fresh attempt seed, never by
    relaxing the separation requirement.
    """


def place_without_overlap(
    rng: random.Random,
    radii: list[float],
    canvas_size: int,
    max_tries_per_shape: int = 400,
) -> list[tuple[float, float]]:
    """Choose centres so no two shapes touch, and none leaves the canvas.

    Largest first: big shapes are hardest to fit, and placing them once the canvas is
    already crowded is the main cause of placement failure.

    Overlap matters because occlusion changes the rendered area of a shape, which
    would silently corrupt the ordinal ground truth that `largest`/`smallest` depend on.
    """
    order = sorted(range(len(radii)), key=lambda i: radii[i], reverse=True)
    centers: dict[int, tuple[float, float]] = {}

    for index in order:
        radius = radii[index]
        low, high = radius, canvas_size - radius
        if low >= high:
            raise PlacementError(f"shape of radius {radius:.1f} exceeds canvas {canvas_size}")

        for _ in range(max_tries_per_shape):
            candidate = (rng.uniform(low, high), rng.uniform(low, high))
            if all(
                math.dist(candidate, other) > radius + radii[other_index]
                for other_index, other in centers.items()
            ):
                centers[index] = candidate
                break
        else:
            raise PlacementError(f"could not place shape {index} of radius {radius:.1f}")

    return [centers[i] for i in range(len(radii))]
