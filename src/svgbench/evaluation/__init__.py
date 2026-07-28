"""Deterministic, offline, arm-blind scoring: parse, align, diff, classify.

Touches no model and no renderer, which is what allows every published number to
be re-derived from committed responses by a reviewer with neither.

Supports C4 (identification separable from execution) and C5 (abstention measured, not
punished). The scoring rules here are frozen before the first model output is observed;
after the `pre-registration` tag they may change only as a disclosed amendment
affecting every arm identically (see `RESULTS.md`).
"""

from svgbench.evaluation.align import align
from svgbench.evaluation.canonical import (
    RENDERING_ATTRIBUTES,
    differs,
    normalise_colour,
    normalise_rotation,
    values_equal,
)
from svgbench.evaluation.classify import classify, edit_is_correct
from svgbench.evaluation.engine import evaluate_response
from svgbench.evaluation.extract import detects_abstention, extract_svg, parse_elements
from svgbench.evaluation.records import (
    AlignmentTier,
    EvaluationResult,
    Outcome,
    ScoringConfig,
)

__all__ = [
    "RENDERING_ATTRIBUTES",
    "AlignmentTier",
    "EvaluationResult",
    "Outcome",
    "ScoringConfig",
    "align",
    "classify",
    "detects_abstention",
    "differs",
    "edit_is_correct",
    "evaluate_response",
    "extract_svg",
    "normalise_colour",
    "normalise_rotation",
    "parse_elements",
    "values_equal",
]
