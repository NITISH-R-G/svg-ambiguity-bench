"""Raster geometry: what the renderer actually draws.

This is the independent witness. `resvg` is a Rust implementation sharing no code with
the analytic path and no code with the generator, so agreement between the two is
evidence rather than tautology.

Per-element measurement works by rendering each element ALONE in an otherwise empty
document. Segmenting a full render by colour is not an option here: ambiguity-set
members share a fill by construction, which is the entire premise of the benchmark.

Isolated rendering assumes shapes do not occlude one another. That assumption is not
taken on trust - `document_coverage` measures the whole document so the isolated
coverages can be checked to sum to it.
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET

import numpy as np
import resvg_py
from PIL import Image

from svgbench.geometry.records import PlaneGeometry

SVG_NS = "http://www.w3.org/2000/svg"

# Alpha below this is treated as background when computing the bounding box. Coverage
# and centroid use the full alpha weighting instead, which is unbiased under
# anti-aliasing; a threshold there would systematically discard partial edge pixels and
# shrink every shape by roughly half its perimeter.
_BBOX_ALPHA_THRESHOLD = 8


def _alpha_mask(svg_text: str, canvas_size: int, scale: int) -> np.ndarray:
    """Render and return the alpha channel as a float array in [0, 1]."""
    scaled = _rescale(svg_text, canvas_size, scale)
    png = bytes(resvg_py.svg_to_bytes(svg_string=scaled))
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    return np.asarray(image, dtype=np.float64)[:, :, 3] / 255.0


def _rescale(svg_text: str, canvas_size: int, scale: int) -> str:
    """Raise render resolution while leaving the coordinate system untouched.

    Only `width`/`height` change; `viewBox` is preserved, so user units are unchanged
    and measurements convert back by dividing by `scale`.
    """
    if scale == 1:
        return svg_text
    pixels = canvas_size * scale
    svg_text = re.sub(r'width="\d+"', f'width="{pixels}"', svg_text, count=1)
    return re.sub(r'height="\d+"', f'height="{pixels}"', svg_text, count=1)


def _geometry_from_mask(alpha: np.ndarray, scale: int) -> PlaneGeometry:
    total = float(alpha.sum())
    if total == 0.0:
        return PlaneGeometry(area=0.0, centroid_x=0.0, centroid_y=0.0, bbox=(0.0, 0.0, 0.0, 0.0))

    rows, cols = np.nonzero(alpha > _BBOX_ALPHA_THRESHOLD / 255.0)
    ys, xs = np.nonzero(alpha)
    weights = alpha[ys, xs]

    # +0.5 puts the centroid at pixel centres rather than corners; without it every
    # measurement carries a half-pixel bias that would show up as a systematic centroid
    # offset against the analytic value.
    centroid_x = float((weights * (xs + 0.5)).sum() / total) / scale
    centroid_y = float((weights * (ys + 0.5)).sum() / total) / scale

    return PlaneGeometry(
        # Divide by scale^2: coverage is measured in device pixels, reported in
        # square user units, so it is comparable across resolutions.
        area=total / (scale * scale),
        centroid_x=centroid_x,
        centroid_y=centroid_y,
        bbox=(
            float(cols.min()) / scale,
            float(rows.min()) / scale,
            float(cols.max() + 1) / scale,
            float(rows.max() + 1) / scale,
        ),
    )


def _isolate(svg_text: str, element_id: str) -> str:
    """Return the document with every shape except `element_id` removed."""
    ET.register_namespace("", SVG_NS)
    root = ET.fromstring(svg_text)
    for child in list(root):
        if child.get("id") != element_id:
            root.remove(child)
    if len(root) != 1:
        raise KeyError(f"element {element_id!r} not found in document")
    return ET.tostring(root, encoding="unicode")


def raster_geometry(
    svg_text: str,
    element_id: str,
    canvas_size: int,
    scale: int = 1,
) -> PlaneGeometry:
    """Measure one element by rendering it alone."""
    return _geometry_from_mask(
        _alpha_mask(_isolate(svg_text, element_id), canvas_size, scale), scale
    )


def document_coverage(svg_text: str, canvas_size: int, scale: int = 1) -> float:
    """Total covered area of the whole document, in square user units.

    Used to verify that isolated per-element coverages sum to the whole. If they exceed
    it, shapes occlude one another and every isolated measurement is contaminated -
    which the generator's centre-distance non-overlap check cannot detect, because it
    reasons about bounding radii rather than rendered pixels.
    """
    alpha = _alpha_mask(svg_text, canvas_size, scale)
    return float(alpha.sum()) / (scale * scale)
