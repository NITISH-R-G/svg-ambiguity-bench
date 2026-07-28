"""SVG serialisation and geometry redaction.

Documents are written by hand rather than through an XML library, because the exact
bytes matter: the corpus is content-addressed, and a library that reorders attributes
or normalises whitespace between versions would change the dataset hash without
changing the experiment.

Every shape is a `<path>` carrying only `id`, `d`, and `fill`. Nothing else. A
`transform`, an `x`, or a `class` naming the shape would put identifying information
back into the markup and break claim C1, so the emitter simply has no way to write one.
"""

from __future__ import annotations

# Fixed-length token. Variable length would leak path complexity - which correlates
# with shape size - through byte count alone (ADR-0002).
_TOKEN_TEMPLATE = "{{{{GEOM_{digest}}}}}"
_TOKEN_DIGEST_LENGTH = 8


def geometry_token(digest: str) -> str:
    """Build the opaque placeholder that replaces a `d` attribute."""
    if len(digest) != _TOKEN_DIGEST_LENGTH:
        raise ValueError(f"token digest must be {_TOKEN_DIGEST_LENGTH} chars, got {digest!r}")
    return _TOKEN_TEMPLATE.format(digest=digest)


def render_document(
    canvas_size: int,
    shapes: list[tuple[str, str, str]],
) -> str:
    """Serialise a document from `(element_id, path_data, fill)` triples, in order.

    The only numeric values outside `d` are the canvas dimensions, which are identical
    across every sample and therefore carry no per-element information.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{canvas_size}" height="{canvas_size}" '
        f'viewBox="0 0 {canvas_size} {canvas_size}">',
    ]
    lines.extend(
        f'  <path id="{element_id}" d="{path_data}" fill="{fill}"/>'
        for element_id, path_data, fill in shapes
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"
