"""Records produced by the generator.

These carry the generator's *intent* - where it meant to put each shape and how large
it meant each to be. Intent is deliberately not ground truth. It is one of three
witnesses (intent, analytic geometry, rendered coverage) that must agree at step 5
before a sample is accepted.

Keeping intent separate from measurement is what makes that agreement meaningful. If
the generator placed shapes by consulting the geometry engine, the two would agree by
construction and the check would be vacuous.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ElementRole = Literal["ambiguity", "distractor"]

_FROZEN = ConfigDict(extra="forbid", frozen=True)


class ElementIntent(BaseModel):
    """What the generator believes about one shape it placed."""

    model_config = _FROZEN

    element_id: str
    geometry_token: str
    role: ElementRole
    fill: str
    document_index: int = Field(ge=0)

    # Intent, not measurement. Compared against the geometry engine at step 5.
    #
    # NAMING IS LOAD-BEARING. These are the PLACEMENT ANCHOR the blob was constructed
    # around - not its area centroid. Vertex radii are jittered, so an irregular blob's
    # area centroid drifts from its construction centre by a few user units.
    #
    # Spatial predicates (`leftmost`, `top_left`) are defined against the area
    # centroid and must use the measured value from `svgbench.geometry`, never these.
    # An earlier version called these `center_x`/`center_y`, which reads as "centroid"
    # and would have made every spatial predicate systematically wrong while remaining
    # internally consistent.
    placement_x: float
    placement_y: float
    area: float = Field(gt=0.0)
    bounding_radius: float = Field(gt=0.0)


class SVGSample(BaseModel):
    """One generated scene, in both the resolved and model-visible forms."""

    model_config = _FROZEN

    svg_id: str
    sample_index: int = Field(ge=0)
    sample_seed: int
    attempts: int = Field(ge=1)

    shared_fill: str
    canvas_size: int

    elements: tuple[ElementIntent, ...]

    # Real geometry. Used for rendering and ground truth; never shown to a model.
    resolved_svg: str
    # Redacted. Exactly what the model sees.
    model_visible_svg: str
    # Sidecar only. Its presence in any model-visible artefact would be a leak.
    token_to_path: dict[str, str]

    @property
    def ambiguity_elements(self) -> list[ElementIntent]:
        return [e for e in self.elements if e.role == "ambiguity"]

    @property
    def distractor_elements(self) -> list[ElementIntent]:
        return [e for e in self.elements if e.role == "distractor"]

    @property
    def k(self) -> int:
        """Ambiguity-set size. Sets this sample's random-selection floor at 1/k."""
        return len(self.ambiguity_elements)
