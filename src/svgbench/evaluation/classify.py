"""Operation effects and outcome classification.

The scoring rules, frozen before any model output was observed. After the
`pre-registration` tag these may change only as a disclosed amendment affecting every
arm identically (`RESULTS.md`).
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Any

from svgbench.evaluation.canonical import normalise_colour, normalise_rotation, values_equal
from svgbench.evaluation.records import Outcome


def edit_is_correct(
    operation: str,
    params: dict[str, Any],
    original: ET.Element | None,
    returned: ET.Element | None,
    tolerance: float,
) -> bool:
    """Whether the requested operation was performed on this element.

    Deliberately distinct from "did this element change". A model that recolours an
    element it was asked to outline has changed it without performing the edit, and
    conflating those would credit an execution failure as success.
    """
    if operation == "delete":
        # Absence IS the edit. Without this branch every successful deletion would look
        # like a missing element and score MALFORMED.
        return returned is None

    if returned is None:
        return False

    if operation == "recolor_fill":
        return normalise_colour(returned.get("fill", "")) == normalise_colour(str(params["fill"]))

    if operation == "add_stroke":
        stroke_matches = normalise_colour(returned.get("stroke", "")) == normalise_colour(
            str(params["stroke"])
        )
        width_matches = values_equal(
            "stroke-width",
            returned.get("stroke-width", ""),
            str(params["stroke_width"]),
            tolerance,
        )
        return stroke_matches and width_matches

    if operation == "rotate":
        rotation = normalise_rotation(returned.get("transform", ""))
        if rotation is None:
            return False
        requested = float(params["degrees"]) % 360.0
        return math.isclose(rotation, requested, abs_tol=1e-6)

    raise ValueError(f"unknown operation {operation!r}")


def classify(
    target_edit_correct: bool,
    target_changed: bool,
    collateral: list[str],
) -> Outcome:
    """Assign the outcome class.

    `target_changed` and `target_edit_correct` differ: the first asks whether the model
    acted on the intended element, the second whether it did the right thing to it.
    Reporting only their conjunction would blame reference resolution for execution
    errors (ADR-0006).
    """
    if target_edit_correct:
        return "CORRECT_LOOSE" if collateral else "CORRECT_STRICT"

    # The requested edit did not happen. Either the model acted somewhere - on the wrong
    # element, or on the right one in the wrong way - or it acted nowhere.
    if collateral or target_changed:
        return "WRONG_TARGET"

    return "NO_EDIT"
