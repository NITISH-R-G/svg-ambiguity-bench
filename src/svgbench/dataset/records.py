"""Frozen-dataset records."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

_FROZEN = ConfigDict(extra="forbid", frozen=True)


class CheckResult(BaseModel):
    """One instrument check performed at freeze time."""

    model_config = _FROZEN

    name: str
    passed: bool
    detail: str


class DatasetManifest(BaseModel):
    """Everything needed to identify, verify and re-derive a frozen corpus.

    `dataset_hash` is a content hash over every artefact file, so it changes if any byte
    of any SVG, ground-truth record or instruction changes. It deliberately excludes the
    manifest and certificate themselves, which describe the corpus rather than being
    part of it.
    """

    model_config = _FROZEN

    schema_version: str
    dataset_hash: str
    config_hash: str
    corpus_config_hash: str
    seed: int

    created_by: dict[str, Any]
    counts: dict[str, Any]
    file_hashes: dict[str, str]
    checks: tuple[CheckResult, ...]

    # Recorded as a fact about the corpus at freeze time. The certificate states it in
    # plain language; the manifest keeps it machine-checkable.
    model_outputs_observed: bool
