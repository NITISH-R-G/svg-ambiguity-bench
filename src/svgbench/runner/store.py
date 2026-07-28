"""Append-only response store.

Every request and response is written to disk verbatim, keyed by
`(experiment_id, case_id, replicate)`. Three properties follow, and all three matter:

  - **Resumable.** An interrupted run continues exactly; a completed one is free to
    re-verify. Nothing is recomputed that already exists.
  - **Tier-1 and Tier-2 reproduction.** A reviewer with no model re-derives every
    published number from these files. A sceptical one writes their own scorer and checks
    whether it reproduces ours - the strongest verification this project can offer.
  - **No silent drops.** Errors and timeouts are stored as outcomes. Denominators are
    fixed at freeze time, so a failed call must consume a case rather than vanish from it.

Keys include `experiment_id`, which derives from the config hash, so two arms can never
collide in the store even though they share every case.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ResponseStore:
    """One JSONL file per experiment, one line per call."""

    def __init__(self, root: Path, experiment_id: str) -> None:
        self._path = root / experiment_id / "responses.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: set[tuple[str, int]] = set()
        self._load_existing()

    def _load_existing(self) -> None:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                self._seen.add((record["case_id"], record["replicate"]))

    def has(self, case_id: str, replicate: int) -> bool:
        return (case_id, replicate) in self._seen

    def append(self, record: dict[str, Any]) -> None:
        """Write one call. Append-only: a stored response is never rewritten."""
        key = (record["case_id"], record["replicate"])
        if key in self._seen:
            raise ValueError(f"refusing to overwrite stored response for {key}")
        with self._path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._seen.add(key)

    def read_all(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    @property
    def path(self) -> Path:
        return self._path

    def __len__(self) -> int:
        return len(self._seen)
