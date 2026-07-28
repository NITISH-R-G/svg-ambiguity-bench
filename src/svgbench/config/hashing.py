"""Canonical hashing of a resolved configuration.

Two hashes, because they answer different questions:

  config_hash        - identity of an EXPERIMENT. Distinguishes arms, so their stored
                       responses cannot collide.
  corpus_config_hash - identity of a CORPUS. Must be equal across arms, or each arm
                       would generate its own dataset and the paired comparison in
                       ADR-0007 would be comparing different cases.

Keeping these separate is not tidiness. If corpus identity depended on model or
context settings, the pairing that the central claim rests on would be invalid while
every individual run still looked correct.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from svgbench.config.schema import Config

# The label of an experiment is not one of its parameters. Excluding it preserves the
# property that identical parameters produce an identical hash, which is what allows
# the arm-fairness audit to detect drift between arms.
_EXCLUDED_FROM_CONFIG_HASH = ("experiment_id",)

# Corpus identity derives from these sections only. Everything else happens after the
# dataset is frozen and cannot change which cases exist.
_CORPUS_FIELDS = ("schema_version", "seed", "generation", "instructions")


def canonical_json(payload: Any) -> str:
    """Serialise deterministically.

    Sorted keys and fixed separators so that formatting or key order cannot change a
    hash. `allow_nan=False` because NaN has no canonical representation and would
    make a hash unstable across platforms.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def config_hash(config: Config) -> str:
    """Identity of an experiment: every result-affecting value except the label."""
    dumped: dict[str, Any] = config.model_dump(mode="json")
    for field in _EXCLUDED_FROM_CONFIG_HASH:
        dumped.pop(field, None)
    return _sha256(dumped)


def corpus_config_hash(config: Config) -> str:
    """Identity of a corpus: seed plus the sections that determine which cases exist."""
    dumped: dict[str, Any] = config.model_dump(mode="json")
    return _sha256({field: dumped[field] for field in _CORPUS_FIELDS})
