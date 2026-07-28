"""Verification of a frozen corpus.

Two independent questions, deliberately separated:

  INTEGRITY   do the bytes on disk still match the manifest?
              Cheap, needs nothing but Python. Catches a hand-edited SVG.

  DETERMINISM does regenerating from the seed reproduce the same hash?
              Needs the renderer. Catches a corpus that cannot actually be re-derived,
              which is the stronger claim and the one Tier-3 reproduction rests on.

Integrity failing means the frozen directory was tampered with. Determinism failing
means the generator is not reproducible, which is a much worse problem and invalidates
every claim about re-derivability.
"""

from __future__ import annotations

import json
from pathlib import Path

from svgbench.config import Config
from svgbench.dataset.freeze import MANIFEST_NAME, _hash_tree, build_artifacts
from svgbench.dataset.records import DatasetManifest


class VerificationError(RuntimeError):
    """Raised when a frozen corpus does not match its manifest."""


def load_manifest(dataset_dir: Path) -> DatasetManifest:
    path = dataset_dir / MANIFEST_NAME
    if not path.exists():
        raise VerificationError(f"no manifest at {path}")
    return DatasetManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def verify_integrity(dataset_dir: Path) -> DatasetManifest:
    """Recompute every file hash and the root hash from the bytes on disk.

    Raises:
        VerificationError: naming the first files that differ, so a tampered corpus
            reports *what* changed rather than only that something did.
    """
    manifest = load_manifest(dataset_dir)
    recomputed_hash, recomputed_files = _hash_tree(dataset_dir)

    missing = sorted(set(manifest.file_hashes) - set(recomputed_files))
    extra = sorted(set(recomputed_files) - set(manifest.file_hashes))
    changed = sorted(
        path
        for path, digest in recomputed_files.items()
        if path in manifest.file_hashes and manifest.file_hashes[path] != digest
    )

    if missing or extra or changed:
        raise VerificationError(
            f"frozen corpus does not match its manifest\n"
            f"  missing: {missing[:5]}\n"
            f"  extra:   {extra[:5]}\n"
            f"  changed: {changed[:5]}"
        )

    if recomputed_hash != manifest.dataset_hash:
        raise VerificationError(
            f"dataset hash mismatch: manifest {manifest.dataset_hash}, recomputed {recomputed_hash}"
        )

    # The directory is named for its own hash, so a renamed or copied corpus is caught
    # as well as an edited one.
    if dataset_dir.name != manifest.dataset_hash:
        raise VerificationError(
            f"directory {dataset_dir.name!r} does not match its own hash {manifest.dataset_hash!r}"
        )

    return manifest


def verify_determinism(config: Config, dataset_dir: Path) -> None:
    """Regenerate from the seed and confirm the artefacts are byte-identical.

    Compares the artefact content rather than re-freezing, so this does not depend on
    directory layout or on the manifest being writable.

    Raises:
        VerificationError: if any regenerated artefact differs.
    """
    manifest = load_manifest(dataset_dir)
    samples, _, instructions = build_artifacts(config)

    for sample in samples:
        for subdir, expected in (
            ("svgs", sample.model_visible_svg),
            ("resolved", sample.resolved_svg),
        ):
            path = dataset_dir / subdir / f"{sample.svg_id}.svg"
            if not path.exists():
                raise VerificationError(f"regeneration produced an unknown sample: {path.name}")
            on_disk = path.read_text(encoding="utf-8")
            if on_disk != expected:
                raise VerificationError(f"{subdir}/{sample.svg_id}.svg differs on regeneration")

    frozen_instructions = json.loads(
        (dataset_dir / "instructions.json").read_text(encoding="utf-8")
    )
    regenerated = [i.model_dump(mode="json") for i in instructions]
    if frozen_instructions != regenerated:
        raise VerificationError("instructions differ on regeneration")

    if manifest.counts["svgs"] != len(samples):
        raise VerificationError("sample count differs on regeneration")


def find_frozen_datasets(root: Path) -> list[Path]:
    """Frozen corpora present, newest first by directory name."""
    if not root.exists():
        return []
    return sorted(
        (p for p in root.iterdir() if p.is_dir() and (p / MANIFEST_NAME).exists()),
        key=lambda p: p.name,
    )
