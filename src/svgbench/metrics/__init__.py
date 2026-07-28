"""Aggregation and inference over evaluation rows.

Resampling is done at the SVG level, not the case level: instructions sharing an
SVG share a layout and are not independent, so case-level resampling would
understate variance and manufacture false precision.
"""
