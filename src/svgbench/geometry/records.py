"""Geometry records."""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

_FROZEN = ConfigDict(extra="forbid", frozen=True)


class PlaneGeometry(BaseModel):
    """One measurement of one shape, from one witness."""

    model_config = _FROZEN

    area: float = Field(ge=0.0)
    centroid_x: float
    centroid_y: float
    # (x_min, y_min, x_max, y_max)
    bbox: tuple[float, float, float, float]


class ElementGeometry(BaseModel):
    """Both witnesses for one element, plus their disagreement.

    Canonical area is the RASTER measurement (ADR-0004): the ordinal predicates are
    perceptual - "second largest" means looks second largest - and pixel coverage is
    what a viewer's eye integrates, while signed analytic area diverges from perception
    for concave outlines.

    The analytic value is retained rather than discarded so the disagreement stays
    inspectable. A ground truth with no recorded uncertainty is an assertion.
    """

    model_config = _FROZEN

    element_id: str
    analytic: PlaneGeometry
    raster: PlaneGeometry

    @property
    def area(self) -> float:
        """Canonical area."""
        return self.raster.area

    @property
    def centroid(self) -> tuple[float, float]:
        """Canonical centroid."""
        return (self.raster.centroid_x, self.raster.centroid_y)

    @property
    def relative_area_disagreement(self) -> float:
        if self.analytic.area == 0.0:
            return float("inf")
        return float(abs(self.raster.area - self.analytic.area) / self.analytic.area)

    @property
    def centroid_disagreement(self) -> float:
        return math.dist(
            (self.raster.centroid_x, self.raster.centroid_y),
            (self.analytic.centroid_x, self.analytic.centroid_y),
        )


class GeometryDisagreementError(ValueError):
    """Raised when the witnesses disagree beyond tolerance.

    Handled by rejecting the sample, never by widening the tolerance. A tolerance that
    is relaxed whenever it fires is not measuring anything.
    """
