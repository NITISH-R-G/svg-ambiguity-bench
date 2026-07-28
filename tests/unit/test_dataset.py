"""Dataset freezing and verification tests.

Supports C6: every reported number is independently verifiable.

Per `docs/verification-policy.md`, the oracle here is deliberately not a second copy of
the hashing code. Integrity is tested by *tampering* - editing a byte, deleting a file,
adding one, renaming the directory - and requiring verification to notice. That fails
for a different reason than a re-implementation of the hash would.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.dataset import (
    CERTIFICATE_NAME,
    MANIFEST_NAME,
    FreezeError,
    VerificationError,
    freeze_dataset,
    load_manifest,
    verify_determinism,
    verify_integrity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"


@pytest.fixture(scope="module")
def config():  # type: ignore[no-untyped-def]
    # Small corpus for speed; freezing behaviour is size-independent.
    return load_config(BASE, overrides={"generation.n_svgs": 5}).config


@pytest.fixture(scope="module")
def frozen(tmp_path_factory, config):  # type: ignore[no-untyped-def]
    root = tmp_path_factory.mktemp("frozen")
    manifest = freeze_dataset(config, root, REPO_ROOT)
    return root / manifest.dataset_hash, manifest


# ---------------------------------------------------------------------------
# What freezing produces
# ---------------------------------------------------------------------------


def test_frozen_directory_is_self_describing(frozen) -> None:  # type: ignore[no-untyped-def]
    """A reviewer should find everything needed to understand the corpus without
    running anything."""
    directory, manifest = frozen
    assert (directory / MANIFEST_NAME).exists()
    assert (directory / CERTIFICATE_NAME).exists()
    assert (directory / "instructions.json").exists()
    assert (directory / "distributions.json").exists()
    assert len(list((directory / "svgs").glob("*.svg"))) == manifest.counts["svgs"]
    assert len(list((directory / "resolved").glob("*.svg"))) == manifest.counts["svgs"]
    assert len(list((directory / "groundtruth").glob("*.json"))) == manifest.counts["svgs"]


def test_directory_is_named_for_its_own_hash(frozen) -> None:  # type: ignore[no-untyped-def]
    directory, manifest = frozen
    assert directory.name == manifest.dataset_hash


def test_manifest_records_both_hashes(frozen, config) -> None:  # type: ignore[no-untyped-def]
    """`corpus_config_hash` is what every arm must share; `config_hash` is what they
    must differ on."""
    _, manifest = frozen
    assert manifest.corpus_config_hash
    assert manifest.config_hash
    assert manifest.seed == config.seed


def test_every_check_passed_and_is_recorded(frozen) -> None:  # type: ignore[no-untyped-def]
    _, manifest = frozen
    names = {c.name for c in manifest.checks}
    assert names == {
        "Generator invariants",
        "Geometry witnesses",
        "Ground truth",
        "Instruction allocation",
        "Leakage audit",
        "Model outputs observed",
    }
    assert all(c.passed for c in manifest.checks)
    assert all(c.detail for c in manifest.checks)


def test_certificate_states_no_model_outputs_observed(frozen) -> None:  # type: ignore[no-untyped-def]
    """The claim a hash cannot make, and the one a sceptical reader most needs."""
    directory, manifest = frozen
    text = (directory / CERTIFICATE_NAME).read_text(encoding="utf-8")
    assert manifest.model_outputs_observed is False
    assert "Model outputs observed" in text
    assert "NO" in text
    assert manifest.dataset_hash in text


def test_model_visible_svgs_carry_no_geometry(frozen) -> None:  # type: ignore[no-untyped-def]
    """The files on disk, not the in-memory objects, are what the model will read."""
    directory, _ = frozen
    for path in (directory / "svgs").glob("*.svg"):
        assert "{{GEOM_" in path.read_text(encoding="utf-8")


def test_distributions_capture_the_instrument(frozen) -> None:  # type: ignore[no-untyped-def]
    """Archived so a future v2 corpus has a baseline to be compared against."""
    directory, _ = frozen
    distributions = json.loads((directory / "distributions.json").read_text(encoding="utf-8"))
    for key in (
        "k",
        "aspect_ratio",
        "adjacent_area_ratio",
        "spatial_margin",
        "ordinal_margin",
        "predicate_refusal_reasons",
        "valid_predicates_per_svg",
        "instruction_family",
        "instruction_operation",
        "mean_random_reference",
        "target_document_position",
    ):
        assert key in distributions, f"missing distribution: {key}"
    assert 0.0 < distributions["mean_random_reference"] < 1.0


# ---------------------------------------------------------------------------
# Integrity - verified by tampering, not by re-implementing the hash
# ---------------------------------------------------------------------------


def test_untouched_corpus_verifies(frozen) -> None:  # type: ignore[no-untyped-def]
    directory, manifest = frozen
    assert verify_integrity(directory).dataset_hash == manifest.dataset_hash


def test_edited_svg_is_detected(tmp_path, config) -> None:  # type: ignore[no-untyped-def]
    """One character changed in one file must break verification."""
    manifest = freeze_dataset(config, tmp_path, REPO_ROOT)
    directory = tmp_path / manifest.dataset_hash

    victim = next(iter(sorted((directory / "svgs").glob("*.svg"))))
    victim.write_text(
        victim.read_text(encoding="utf-8").replace('fill="#', 'fill="#0', 1),
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(VerificationError, match="changed"):
        verify_integrity(directory)


def test_deleted_file_is_detected(tmp_path, config) -> None:  # type: ignore[no-untyped-def]
    manifest = freeze_dataset(config, tmp_path, REPO_ROOT)
    directory = tmp_path / manifest.dataset_hash
    next(iter(sorted((directory / "groundtruth").glob("*.json")))).unlink()
    with pytest.raises(VerificationError, match="missing"):
        verify_integrity(directory)


def test_added_file_is_detected(tmp_path, config) -> None:  # type: ignore[no-untyped-def]
    """An extra artefact is as much a change as a missing one."""
    manifest = freeze_dataset(config, tmp_path, REPO_ROOT)
    directory = tmp_path / manifest.dataset_hash
    (directory / "svgs" / "smuggled.svg").write_text("<svg/>", encoding="utf-8", newline="\n")
    with pytest.raises(VerificationError, match="extra"):
        verify_integrity(directory)


def test_renamed_directory_is_detected(tmp_path, config) -> None:  # type: ignore[no-untyped-def]
    """A corpus copied under another name is no longer content-addressed."""
    manifest = freeze_dataset(config, tmp_path, REPO_ROOT)
    directory = tmp_path / manifest.dataset_hash
    renamed = tmp_path / "some_other_name"
    directory.rename(renamed)
    with pytest.raises(VerificationError, match="does not match its own hash"):
        verify_integrity(renamed)


def test_tampered_manifest_hash_is_detected(tmp_path, config) -> None:  # type: ignore[no-untyped-def]
    """Editing the manifest to match tampered files must not rescue it."""
    manifest = freeze_dataset(config, tmp_path, REPO_ROOT)
    directory = tmp_path / manifest.dataset_hash
    path = directory / MANIFEST_NAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["dataset_hash"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
    with pytest.raises(VerificationError):
        verify_integrity(directory)


# ---------------------------------------------------------------------------
# Determinism - the claim Tier-3 reproduction rests on
# ---------------------------------------------------------------------------


def test_regeneration_reproduces_the_frozen_corpus(frozen, config) -> None:  # type: ignore[no-untyped-def]
    directory, _ = frozen
    verify_determinism(config, directory)


def test_regeneration_from_a_different_seed_is_detected(frozen) -> None:  # type: ignore[no-untyped-def]
    """Guards against determinism passing vacuously."""
    directory, _ = frozen
    other = load_config(BASE, overrides={"generation.n_svgs": 5, "seed": 4242}).config
    with pytest.raises(VerificationError):
        verify_determinism(other, directory)


def test_freezing_twice_produces_the_same_hash(tmp_path, config) -> None:  # type: ignore[no-untyped-def]
    first = freeze_dataset(config, tmp_path / "a", REPO_ROOT)
    second = freeze_dataset(config, tmp_path / "b", REPO_ROOT)
    assert first.dataset_hash == second.dataset_hash
    assert first.file_hashes == second.file_hashes


# ---------------------------------------------------------------------------
# Refusal to freeze
# ---------------------------------------------------------------------------


def test_freeze_refuses_when_a_check_fails(tmp_path, config, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A corpus that fails its own guarantees must not become the thing every later
    number depends on."""
    from svgbench.dataset import checks as checks_module
    from svgbench.dataset import freeze as freeze_module
    from svgbench.dataset.records import CheckResult

    def failing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return [CheckResult(name="Leakage audit", passed=False, detail="planted failure")]

    monkeypatch.setattr(freeze_module, "run_all", failing)
    with pytest.raises(FreezeError, match="planted failure"):
        freeze_dataset(config, tmp_path, REPO_ROOT)
    assert not list(tmp_path.glob("*/manifest.json")), "wrote a manifest despite failing"
    assert checks_module is not None


def test_manifest_round_trips(frozen) -> None:  # type: ignore[no-untyped-def]
    directory, manifest = frozen
    assert load_manifest(directory).model_dump() == manifest.model_dump()
