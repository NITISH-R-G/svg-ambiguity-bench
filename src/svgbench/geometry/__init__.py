"""Two independent measurement services.

  - analytic : exact bbox / centroid / area from path algebra (svgelements)
  - raster   : pixel coverage at fixed resolution (resvg, a Rust implementation)

They are deliberately different implementations. Ground truth is only meaningful
because two independent witnesses agree; two views of one code path would not be
validation, merely consistency.

Supports claim C7 (see CLAIMS.md): ground truth is correct, not merely asserted.

Scope note on independence: the analytic path and the generator's intent share the
shoelace formula, differing only in whether vertices come from the generator or from
parsing the serialised `d` string. That comparison is a serialisation check. The
genuinely independent witness is the rasteriser.
"""

from svgbench.geometry.analytic import analytic_geometry
from svgbench.geometry.engine import (
    DEFAULT_AREA_TOLERANCE,
    DEFAULT_CENTROID_TOLERANCE,
    area_ranking,
    measure_document,
    witnesses_agree_on_ranking,
)
from svgbench.geometry.raster import document_coverage, raster_geometry
from svgbench.geometry.records import (
    ElementGeometry,
    GeometryDisagreementError,
    PlaneGeometry,
)

__all__ = [
    "DEFAULT_AREA_TOLERANCE",
    "DEFAULT_CENTROID_TOLERANCE",
    "ElementGeometry",
    "GeometryDisagreementError",
    "PlaneGeometry",
    "analytic_geometry",
    "area_ranking",
    "document_coverage",
    "measure_document",
    "raster_geometry",
    "witnesses_agree_on_ranking",
]
