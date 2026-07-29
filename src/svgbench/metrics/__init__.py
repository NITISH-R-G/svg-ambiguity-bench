"""Aggregation and inference over evaluation rows.

Resampling is done at the SVG level, not the case level: instructions sharing an SVG
share a layout and are not independent, so case-level resampling would understate
variance and manufacture false precision (ADR-0007).

Consumes evaluation rows only. Touches no model and no renderer.
"""

from svgbench.metrics.analysis import (
    ArmMetrics,
    Interval,
    arm_metrics,
    cluster_bootstrap,
    load_rows,
    minimum_detectable_effect,
    paired_permutation,
)

__all__ = [
    "ArmMetrics",
    "Interval",
    "arm_metrics",
    "cluster_bootstrap",
    "load_rows",
    "minimum_detectable_effect",
    "paired_permutation",
]
