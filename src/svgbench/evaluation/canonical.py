"""Canonical comparison of SVG elements.

Comparison happens on a normalised view, because the alternative is measuring
serialisation habits. `#00f`, `#0000ff` and `blue` are one colour; `3` and `3.0` are one
width; attribute order is meaningless in XML. Counting any of those as an edit would
attribute a formatting difference to a reasoning failure - the exact misattribution
ADR-0006 exists to prevent.

Only RENDERING-RELEVANT attributes are compared. An added `data-note` changes nothing a
viewer sees, and the instruction is about the picture.
"""

from __future__ import annotations

import math
import re

# Attributes that change what is drawn. Anything outside this set is ignored entirely,
# including `id` - identity is handled by alignment, not by diffing.
RENDERING_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "d",
        "fill",
        "fill-opacity",
        "stroke",
        "stroke-width",
        "stroke-opacity",
        "stroke-dasharray",
        "stroke-linecap",
        "stroke-linejoin",
        "opacity",
        "transform",
        "style",
        "visibility",
        "display",
    }
)

# Enough of the CSS keyword set to cover the edit palette and common model choices.
_NAMED_COLOURS: dict[str, str] = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "lime": "#00ff00",
    "green": "#008000",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "aqua": "#00ffff",
    "magenta": "#ff00ff",
    "fuchsia": "#ff00ff",
    "silver": "#c0c0c0",
    "gray": "#808080",
    "grey": "#808080",
    "maroon": "#800000",
    "olive": "#808000",
    "purple": "#800080",
    "teal": "#008080",
    "navy": "#000080",
    "orange": "#ffa500",
    "none": "none",
    "transparent": "none",
}

_RGB_PATTERN = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", re.IGNORECASE)
_ROTATE_PATTERN = re.compile(r"rotate\(\s*(-?[\d.]+)", re.IGNORECASE)
_NUMBER_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")


def normalise_colour(value: str) -> str:
    """One canonical form per colour, so notation cannot masquerade as an edit."""
    text = value.strip().lower()
    if text in _NAMED_COLOURS:
        return _NAMED_COLOURS[text]

    match = _RGB_PATTERN.fullmatch(text)
    if match:
        return "#" + "".join(f"{int(part):02x}" for part in match.groups())

    if text.startswith("#"):
        digits = text[1:]
        if len(digits) == 3:  # #abc -> #aabbcc
            return "#" + "".join(c * 2 for c in digits)
        if len(digits) == 6:
            return f"#{digits}"
    return text


def normalise_rotation(transform: str) -> float | None:
    """Net rotation in degrees, reduced modulo 360.

    `rotate(450)` renders identically to `rotate(90)`. This instrument exists to
    distinguish the rendered layer from the source layer, so rejecting a
    rendering-identical edit on a notation technicality would contradict its own premise.
    """
    match = _ROTATE_PATTERN.search(transform)
    if not match:
        return None
    return float(match.group(1)) % 360.0


def values_equal(name: str, left: str, right: str, tolerance: float) -> bool:
    """Compare one attribute under the rules appropriate to it."""
    if left == right:
        return True

    if name in {"fill", "stroke"}:
        return normalise_colour(left) == normalise_colour(right)

    if name == "transform":
        left_rotation = normalise_rotation(left)
        right_rotation = normalise_rotation(right)
        if left_rotation is not None and right_rotation is not None:
            return math.isclose(left_rotation, right_rotation, abs_tol=1e-6)
        return left.strip() == right.strip()

    if _NUMBER_PATTERN.match(left.strip()) and _NUMBER_PATTERN.match(right.strip()):
        return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)

    return left.strip() == right.strip()


def rendering_view(attributes: dict[str, str]) -> dict[str, str]:
    """Only the attributes that affect what is drawn."""
    return {k: v for k, v in attributes.items() if k in RENDERING_ATTRIBUTES}


def differs(
    original: dict[str, str],
    returned: dict[str, str],
    tolerance: float,
) -> bool:
    """Whether two elements differ in any rendering-relevant way."""
    left = rendering_view(original)
    right = rendering_view(returned)
    for name in set(left) | set(right):
        if name not in left or name not in right:
            return True
        if not values_equal(name, left[name], right[name], tolerance):
            return True
    return False
