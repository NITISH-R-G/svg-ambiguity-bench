"""The reference implementation must satisfy its own specification.

`conformance_vectors.json` is the artefact an independent implementation - Rust, Go, R,
TypeScript - is checked against. If the Python drifts from the committed vectors, the
vectors stop describing anything and every downstream implementation inherits the drift
silently.

These tests read the vectors as data. They deliberately do not import the generator, so a
bug in generation cannot cancel out against a matching bug in checking - the failure mode
recorded in `docs/verification-policy.md`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fmtcontrol import check_control, permute

VECTORS_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "fmtcontrol" / "conformance_vectors.json"
)


def _payload() -> dict[str, Any]:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _vectors() -> list[dict[str, Any]]:
    return list(_payload()["vectors"])


def _must_raise() -> list[dict[str, Any]]:
    return list(_payload()["must_raise"])


def test_vectors_file_is_present_and_populated() -> None:
    payload = _payload()
    assert payload["spec_version"] == "1.0"
    assert len(payload["vectors"]) >= 10
    assert len(payload["must_raise"]) >= 2
    assert "MT19937" in payload["algorithm"]["rng"], "the RNG must be pinned, not implied"


@pytest.mark.parametrize("vector", _vectors(), ids=lambda v: str(v["id"]))
def test_reference_implementation_matches_vector(vector: dict[str, Any]) -> None:
    """Level 2 conformance for the reference implementation itself."""
    facts = dict(zip(vector["entities"], vector["values"], strict=True))
    result = permute(facts, key=vector["key"], seed=vector["seed"])
    actual = [result[e] for e in vector["entities"]]
    assert actual == vector["expected_permuted_values"], (
        f"{vector['id']}: reference implementation no longer reproduces its own vector. "
        "Either this is an unintended behaviour change, or the vectors must be "
        "regenerated and the spec version bumped."
    )


@pytest.mark.parametrize("vector", _vectors(), ids=lambda v: str(v["id"]))
def test_every_vector_satisfies_the_invariants(vector: dict[str, Any]) -> None:
    """I1-I4 and I8, checked against the stored expectation rather than a fresh call.

    This catches a vector file that is internally inconsistent - for instance one edited
    by hand - independently of whether the implementation agrees with it.
    """
    entities = vector["entities"]
    facts = dict(zip(entities, vector["values"], strict=True))
    permuted = dict(zip(entities, vector["expected_permuted_values"], strict=True))

    report = check_control(facts, permuted)
    assert report.ok, f"{vector['id']}: stored vector violates the spec: {report.failures}"


@pytest.mark.parametrize("case", _must_raise(), ids=lambda c: str(c["id"]))
def test_boundary_cases_raise(case: dict[str, Any]) -> None:
    """I9: refusal over degradation. Returning a value here would be the silent failure."""
    facts = dict(zip(case["entities"], case["values"], strict=True))
    with pytest.raises(ValueError, match=case["error"]):
        permute(facts, key=case["key"], seed=case["seed"])


def test_determinism_across_repeated_calls() -> None:
    """I5, over every vector at once."""
    for vector in _vectors():
        facts = dict(zip(vector["entities"], vector["values"], strict=True))
        first = permute(facts, key=vector["key"], seed=vector["seed"])
        for _ in range(5):
            assert permute(facts, key=vector["key"], seed=vector["seed"]) == first


def test_inputs_are_not_mutated_by_any_vector() -> None:
    """I8, over every vector."""
    for vector in _vectors():
        facts = dict(zip(vector["entities"], vector["values"], strict=True))
        snapshot = json.dumps(facts, sort_keys=True)
        permute(facts, key=vector["key"], seed=vector["seed"])
        assert json.dumps(facts, sort_keys=True) == snapshot, vector["id"]


def test_key_and_seed_both_change_the_permutation() -> None:
    """I6 and I7 are asserted by the vector set itself, so check the set has the pairs."""
    by_id = {v["id"]: v for v in _vectors()}
    base = by_id["basic-3"]
    same_key_new_seed = by_id["same-key-different-seed"]
    same_seed_new_key = by_id["same-seed-different-key"]

    assert same_key_new_seed["key"] == base["key"]
    assert same_key_new_seed["seed"] != base["seed"]
    assert same_seed_new_key["seed"] == base["seed"]
    assert same_seed_new_key["key"] != base["key"]

    assert (
        same_key_new_seed["expected_permuted_values"] != base["expected_permuted_values"]
        or same_seed_new_key["expected_permuted_values"] != base["expected_permuted_values"]
    ), "neither seed nor key changed the permutation; I6/I7 are not being exercised"
