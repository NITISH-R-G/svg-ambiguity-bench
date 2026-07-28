"""The predicate registry.

Supports claim C8: ground truth matches human judgement, not merely itself.

Every predicate carries a PRIMARY operational definition and a set of ALTERNATIVE
definitions that a reasonable person might equally well have chosen. A sample may only
host a predicate when every definition picks the same winner.

The reasoning: measurement error is not what makes a benchmark case contested. Competing
reasonable interpretations are. Asked for "the leftmost shape", one person reads the
left-most *edge* and another reads the shape sitting furthest left overall. Both are
correct readings of the phrase. When those readings disagree, a model choosing either is
arguably right, and marking one wrong measures the benchmark's arbitrariness rather than
the model's ability.

Measured on this corpus, that disagreement is not hypothetical:
  - `leftmost`  centroid vs left edge      - 1/15 SVGs
  - `leftmost`  centroid vs bbox midpoint  - 2/15 SVGs
  - `top_left`  euclidean vs manhattan     - 2/15 SVGs

Roughly one sample in eight is humanly contested while being mathematically unambiguous.

Deliberately NOT gated: shape elongation. Equal-area shapes of differing aspect ratio are
not perceived as equal, which would threaten the ordinal family - but this corpus's blobs
have median bbox aspect ratio 1.11 and maximum 1.53, and bbox-area ranking agrees with
true-area ranking in 15/15 SVGs. The threat does not materialise here, so no gate is
built for it. A gate that can never fire is decoration.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from svgbench.geometry import ElementGeometry

# A scorer maps one element's geometry to a number; lower always wins. Ordinal
# predicates negate area so the convention holds everywhere.
Scorer = Callable[[ElementGeometry, int], float]


def _centroid_x(g: ElementGeometry, _canvas: int) -> float:
    return g.centroid[0]


def _centroid_y(g: ElementGeometry, _canvas: int) -> float:
    return g.centroid[1]


def _left_edge(g: ElementGeometry, _canvas: int) -> float:
    return g.analytic.bbox[0]


def _right_edge(g: ElementGeometry, canvas: int) -> float:
    return canvas - g.analytic.bbox[2]


def _top_edge(g: ElementGeometry, _canvas: int) -> float:
    return g.analytic.bbox[1]


def _bottom_edge(g: ElementGeometry, canvas: int) -> float:
    return canvas - g.analytic.bbox[3]


def _bbox_mid_x(g: ElementGeometry, _canvas: int) -> float:
    return (g.analytic.bbox[0] + g.analytic.bbox[2]) / 2.0


def _bbox_mid_y(g: ElementGeometry, _canvas: int) -> float:
    return (g.analytic.bbox[1] + g.analytic.bbox[3]) / 2.0


def _mirror_x(scorer: Scorer) -> Scorer:
    return lambda g, canvas: canvas - scorer(g, canvas)


def _corner_scorers(corner: tuple[int, int]) -> list[Scorer]:
    """Distance to a canvas corner, under three reasonable readings.

    Euclidean and Manhattan disagree when one shape is further left and another further
    up - exactly the case where a person might decline to answer.
    """
    cx, cy = corner

    def euclidean(g: ElementGeometry, canvas: int) -> float:
        x, y = g.centroid
        return math.dist((x, y), (cx * canvas, cy * canvas))

    def manhattan(g: ElementGeometry, canvas: int) -> float:
        x, y = g.centroid
        return abs(x - cx * canvas) + abs(y - cy * canvas)

    def nearest_bbox_corner(g: ElementGeometry, canvas: int) -> float:
        x0, y0, x1, y1 = g.analytic.bbox
        x = x0 if cx == 0 else x1
        y = y0 if cy == 0 else y1
        return math.dist((x, y), (cx * canvas, cy * canvas))

    return [euclidean, manhattan, nearest_bbox_corner]


@dataclass(frozen=True)
class PredicateSpec:
    """One visual predicate: how to score it, and which quadrant it must land in."""

    name: str
    family: str
    # scorers[0] is primary; the rest are alternative readings that must agree with it.
    scorers: tuple[Scorer, ...]
    # For corner predicates, the winner must also sit in that quadrant. Nearest-corner
    # alone can crown a shape near the middle of the canvas, which nobody would call
    # "the top-left one".
    required_quadrant: tuple[str, str] | None = None
    # Rank among the ambiguity set by descending area. None for spatial predicates.
    area_rank: int | None = None


def _spatial(name: str, scorers: list[Scorer], quadrant: tuple[str, str] | None = None):  # type: ignore[no-untyped-def]
    return PredicateSpec(
        name=name, family="SPATIAL", scorers=tuple(scorers), required_quadrant=quadrant
    )


def _ordinal(name: str, rank: int) -> PredicateSpec:
    # Ordinal agreement is checked as RANKING agreement between the two measurement
    # witnesses rather than via alternative scorers, because "second largest" has only
    # one sensible reading - what varies is which measurement you trust.
    return PredicateSpec(
        name=name,
        family="ORDINAL_SIZE",
        scorers=(lambda g, _c: -g.area,),
        area_rank=rank,
    )


REGISTRY: dict[str, PredicateSpec] = {
    "leftmost": _spatial("leftmost", [_centroid_x, _left_edge, _bbox_mid_x]),
    "rightmost": _spatial(
        "rightmost", [_mirror_x(_centroid_x), _right_edge, _mirror_x(_bbox_mid_x)]
    ),
    "topmost": _spatial("topmost", [_centroid_y, _top_edge, _bbox_mid_y]),
    "bottommost": _spatial(
        "bottommost", [_mirror_x(_centroid_y), _bottom_edge, _mirror_x(_bbox_mid_y)]
    ),
    "top_left": _spatial("top_left", _corner_scorers((0, 0)), ("left", "top")),
    "top_right": _spatial("top_right", _corner_scorers((1, 0)), ("right", "top")),
    "bottom_left": _spatial("bottom_left", _corner_scorers((0, 1)), ("left", "bottom")),
    "bottom_right": _spatial("bottom_right", _corner_scorers((1, 1)), ("right", "bottom")),
    "largest": _ordinal("largest", 1),
    "second_largest": _ordinal("second_largest", 2),
    "third_largest": _ordinal("third_largest", 3),
    "smallest": _ordinal("smallest", -1),
}


def quadrant_of(geometry: ElementGeometry, canvas: int) -> tuple[str, str]:
    """Which half of the canvas the centroid sits in, horizontally and vertically."""
    x, y = geometry.centroid
    return (
        "left" if x < canvas / 2 else "right",
        "top" if y < canvas / 2 else "bottom",
    )
