"""Renders metrics into tables and figures.

Contains no analysis logic. It must be impossible to compute a number here that does
not already exist in the metrics output.

This is Tier-1 reproduction: reads committed evaluation rows, needs no model and no
renderer, and regenerates every published number in about a second.
"""

from svgbench.reporting.report import (
    ARM_ORDER,
    COMPARISONS,
    build_report,
    render_summary,
    write_report,
)

__all__ = [
    "ARM_ORDER",
    "COMPARISONS",
    "build_report",
    "render_summary",
    "write_report",
]
