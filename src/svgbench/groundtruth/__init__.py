"""Derives per-element geometric facts and evaluates the predicate registry.

Enforces the separability guarantees. A case whose intended target does not beat
the runner-up by the configured margin is rejected and regenerated - never
shipped with a contested answer. Rejections are logged, because rejection
sampling biases the corpus and the size of that bias must be publishable.

Supports claims C7 and C8 (see CLAIMS.md). C8 is the one added here: ground truth must
match what a reasonable person would say, not merely be self-consistent. A sample whose
answer changes depending on which reasonable definition you pick is refused.
"""

from svgbench.groundtruth.engine import build_corpus_ground_truth, build_ground_truth
from svgbench.groundtruth.predicates import REGISTRY, PredicateSpec, quadrant_of
from svgbench.groundtruth.records import (
    InvalidReason,
    PredicateResult,
    SampleGroundTruth,
)

__all__ = [
    "REGISTRY",
    "InvalidReason",
    "PredicateResult",
    "PredicateSpec",
    "SampleGroundTruth",
    "build_corpus_ground_truth",
    "build_ground_truth",
    "quadrant_of",
]
