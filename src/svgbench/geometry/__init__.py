"""Two independent measurement services.

  - analytic  : exact bbox / centroid / area from path algebra (svgelements)
  - raster    : pixel coverage at fixed DPI (resvg, a Rust implementation)

They are deliberately different implementations. Ground truth is only meaningful
because two independent witnesses agree; two views of one code path would not be
validation, merely consistency.
"""
