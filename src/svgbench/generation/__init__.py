"""Scene synthesis and geometry redaction.

Owns the invariant that every piece of positional information lives inside the
path `d` attribute. A `transform`, `x` or `cx` on an ambiguity-set member would
silently reintroduce readable position and destroy the premise of the benchmark.

Supports claim C1 (see CLAIMS.md): the corpus is genuinely under-determined.
"""

from svgbench.generation.document import geometry_token, render_document
from svgbench.generation.generator import generate_corpus, generate_sample
from svgbench.generation.records import ElementIntent, ElementRole, SVGSample
from svgbench.generation.shapes import Blob, PlacementError, polygon_area

__all__ = [
    "Blob",
    "ElementIntent",
    "ElementRole",
    "PlacementError",
    "SVGSample",
    "generate_corpus",
    "generate_sample",
    "geometry_token",
    "polygon_area",
    "render_document",
]
