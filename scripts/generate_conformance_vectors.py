"""Generate the canonical conformance vectors for the format-matched control.

An independent implementation - in Rust, Go, R, TypeScript - can be checked against these
without reading the Python. That is the point: it separates the idea from this code.

The vectors are generated rather than hand-written so they cannot drift from the
implementation, and they are committed so a future change to the implementation that
alters them shows up as a diff in a data file rather than as a silent behaviour change.

Usage:
    python scripts/generate_conformance_vectors.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fmtcontrol import __version__, permute

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "src" / "fmtcontrol" / "conformance_vectors.json"

SPEC_VERSION = "1.0"

# Chosen to exercise the properties the specification actually constrains, not to be
# pretty: the K range the benchmark uses, ties, negatives, mixed types, unicode keys, a
# long key, and the two boundary cases that must raise.
_CASES: list[dict[str, Any]] = [
    {
        "id": "basic-3",
        "why": "smallest case with a meaningful permutation",
        "seed": 991,
        "key": "item-1",
        "entities": ["a", "b", "c"],
        "values": [1, 2, 3],
    },
    {
        "id": "k4-tuples",
        "why": "K=4, tuple-valued facts - the benchmark's minimum ambiguity set",
        "seed": 991,
        "key": "svg_029f05e8",
        "entities": ["e1", "e2", "e3", "e4"],
        "values": [
            [184.8, 207.7, 17506],
            [77.7, 297.4, 972],
            [186.5, 411.8, 10993],
            [426.6, 292.5, 6306],
        ],
    },
    {
        "id": "k7-tuples",
        "why": "K=7, the benchmark's maximum ambiguity set",
        "seed": 991,
        "key": "svg_1b314fd2",
        "entities": [f"e{i}" for i in range(7)],
        "values": [[float(i) * 11.5, float(i) * 7.25, i * 1000] for i in range(7)],
    },
    {
        "id": "same-key-different-seed",
        "why": "seed must change the permutation; it is not decorative",
        "seed": 12345,
        "key": "item-1",
        "entities": ["a", "b", "c"],
        "values": [1, 2, 3],
    },
    {
        "id": "same-seed-different-key",
        "why": "key must change the permutation, so items do not share one shuffle",
        "seed": 991,
        "key": "item-2",
        "entities": ["a", "b", "c"],
        "values": [1, 2, 3],
    },
    {
        "id": "partial-ties",
        "why": "equal values must not break determinism or the displacement check",
        "seed": 991,
        "key": "ties",
        "entities": ["a", "b", "c", "d"],
        "values": [5, 5, 9, 1],
    },
    {
        "id": "strings",
        "why": "values are moved wholesale, so their type is unconstrained",
        "seed": 7,
        "key": "docs",
        "entities": ["doc_1", "doc_2", "doc_3"],
        "values": ["Paris", "Berlin", "Rome"],
    },
    {
        "id": "unicode-key",
        "why": "the key is hashed as UTF-8; a locale-dependent encoding would diverge here",
        "seed": 42,
        "key": "запрос-42",
        "entities": ["x", "y", "z"],
        "values": [10, 20, 30],
    },
    {
        "id": "negatives-and-floats",
        "why": "no assumption that values are positive or integral",
        "seed": 3,
        "key": "mixed",
        "entities": ["p", "q", "r", "s"],
        "values": [-1.5, 0.0, 2.25, -99.75],
    },
    {
        "id": "large-16",
        "why": "beyond the benchmark's range, to pin behaviour a reimplementer may extrapolate",
        "seed": 991,
        "key": "wide",
        "entities": [f"n{i:02d}" for i in range(16)],
        "values": list(range(16)),
    },
]

_MUST_RAISE: list[dict[str, Any]] = [
    {
        "id": "single-entity",
        "why": "one row has no format-matched control; returning it unchanged would be invalid",
        "seed": 1,
        "key": "k",
        "entities": ["only"],
        "values": [1],
        "error": "fewer than two entities",
    },
    {
        "id": "all-values-equal",
        "why": "no permutation displaces anything, so the control would equal the treatment",
        "seed": 1,
        "key": "k",
        "entities": ["a", "b", "c"],
        "values": [5, 5, 5],
        "error": "no displacing permutation",
    },
]


def _as_key(value: Any) -> Any:
    """JSON round-trips tuples to lists; compare in the JSON domain throughout."""
    return json.loads(json.dumps(value))


def main() -> int:
    vectors: list[dict[str, Any]] = []
    for case in _CASES:
        facts = dict(zip(case["entities"], map(_as_key, case["values"]), strict=True))
        result = permute(facts, key=case["key"], seed=case["seed"])
        vectors.append(
            {
                "id": case["id"],
                "why": case["why"],
                "seed": case["seed"],
                "key": case["key"],
                "entities": case["entities"],
                "values": _as_key(case["values"]),
                "expected_permuted_values": [result[e] for e in case["entities"]],
            }
        )

    errors: list[dict[str, Any]] = []
    for case in _MUST_RAISE:
        facts = dict(zip(case["entities"], map(_as_key, case["values"]), strict=True))
        try:
            permute(facts, key=case["key"], seed=case["seed"])
        except ValueError:
            errors.append(
                {k: v for k, v in case.items() if k != "values"}
                | {"values": _as_key(case["values"])}
            )
        else:  # pragma: no cover - a regression would be caught by the conformance test
            print(f"ERROR: {case['id']} did not raise", file=sys.stderr)
            return 1

    payload = {
        "spec_version": SPEC_VERSION,
        "fmtcontrol_version": __version__,
        "algorithm": {
            "digest": "SHA-256 of the UTF-8 bytes of f'{seed}:{key}'",
            "rng_seed": "big-endian integer from the first 8 bytes of that digest",
            "rng": "Mersenne Twister MT19937, as CPython random.Random",
            "shuffle": "CPython random.shuffle: Fisher-Yates descending, j = _randbelow(i + 1)",
            "displacement": (
                "reshuffle until at least one position differs by value; max 64 attempts"
            ),
            "note": (
                "Level 2 conformance requires bit-exact reproduction of this pipeline. "
                "See SPEC.md for why the RNG is pinned to MT19937 and why that is a "
                "known wart rather than a design choice."
            ),
        },
        "vectors": vectors,
        "must_raise": errors,
    }

    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {OUT.relative_to(REPO_ROOT)}: {len(vectors)} vectors, {len(errors)} error cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
