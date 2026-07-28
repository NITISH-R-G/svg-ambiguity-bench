"""The freeze point: content-addressed hashing, manifest generation, verification.

Everything upstream of this module is stochastic. Everything downstream loads by
dataset hash and refuses to run on a mismatch, so an arm can never be compared
against a corpus it did not see.

Supports C6 (every reported number is independently verifiable). The frozen directory
is self-describing: the exact bytes the model receives, the answer key, the
distributions that characterise the instrument, and a certificate stating what was
checked and whether any model output had been observed at freeze time.
"""

from svgbench.dataset.checks import run_all
from svgbench.dataset.distributions import compute_distributions
from svgbench.dataset.freeze import (
    CERTIFICATE_NAME,
    MANIFEST_NAME,
    FreezeError,
    build_artifacts,
    freeze_dataset,
    render_certificate,
)
from svgbench.dataset.records import CheckResult, DatasetManifest
from svgbench.dataset.verify import (
    VerificationError,
    find_frozen_datasets,
    load_manifest,
    verify_determinism,
    verify_integrity,
)

__all__ = [
    "CERTIFICATE_NAME",
    "MANIFEST_NAME",
    "CheckResult",
    "DatasetManifest",
    "FreezeError",
    "VerificationError",
    "build_artifacts",
    "compute_distributions",
    "find_frozen_datasets",
    "freeze_dataset",
    "load_manifest",
    "render_certificate",
    "run_all",
    "verify_determinism",
    "verify_integrity",
]
