"""Freezing: the boundary between a corpus that can change and one that cannot.

Everything upstream of this module is stochastic. Everything downstream loads by
`dataset_hash` and refuses to run on a mismatch, so an arm can never be compared against
a corpus it did not see.

The output directory is self-describing on purpose. A reviewer who clones the repository
and opens `data/frozen/<hash>/` should find the exact bytes the model will receive, the
answer key, the distributions that characterise the instrument, and a certificate saying
what was checked and whether any model output had been observed - without running
anything.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

from svgbench.config import Config, canonical_json, config_hash, corpus_config_hash
from svgbench.dataset.checks import run_all
from svgbench.dataset.distributions import compute_distributions
from svgbench.dataset.records import DatasetManifest
from svgbench.generation import SVGSample, generate_corpus
from svgbench.groundtruth import SampleGroundTruth, build_corpus_ground_truth
from svgbench.instructions import Instruction, build_instructions

MANIFEST_NAME = "manifest.json"
CERTIFICATE_NAME = "CERTIFICATE.txt"
DISTRIBUTIONS_NAME = "distributions.json"

# Excluded from the ROOT hash, though still covered by per-file hashes so tampering is
# still detected.
#
# `dataset_hash` means "the cases the model will see". The manifest and certificate
# describe the corpus rather than being part of it, and including them would be
# circular. `distributions.json` is a derived summary: adding a new distribution later
# would change the dataset identity while every case stayed byte-identical, which would
# spuriously invalidate stored results and break the rule that all arms must share one
# dataset hash. Identity has to track the cases, not the commentary on them.
_NOT_IN_ROOT_HASH = frozenset({MANIFEST_NAME, CERTIFICATE_NAME, DISTRIBUTIONS_NAME})


class FreezeError(RuntimeError):
    """Raised when a corpus fails its own checks and must not be frozen."""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" so a corpus frozen on Windows hashes identically to one frozen on
    # POSIX. Without it the dataset hash would be platform-dependent, and the
    # determinism guarantee would silently hold only within one operating system.
    path.write_text(content, encoding="utf-8", newline="\n")


def _discard(directory: Path) -> None:
    """Remove a directory tree if present. Used only for staging, never for a frozen set."""
    if not directory.exists():
        return
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    directory.rmdir()


def _hash_tree(root: Path) -> tuple[str, dict[str, str]]:
    """Root hash over the case-defining artefacts, plus per-file hashes for everything.

    The two scopes differ deliberately. `file_hashes` covers derived files as well, so
    integrity verification still catches an edited `distributions.json`. `root_hash`
    covers only what defines a case, so the dataset identity is stable against changes
    to the commentary.
    """
    file_hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in {MANIFEST_NAME, CERTIFICATE_NAME}:
            continue
        relative = path.relative_to(root).as_posix()
        file_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()

    identity = {
        path: digest
        for path, digest in file_hashes.items()
        if Path(path).name not in _NOT_IN_ROOT_HASH
    }
    root_hash = hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()
    return root_hash, file_hashes


def build_artifacts(
    config: Config,
) -> tuple[list[SVGSample], list[SampleGroundTruth], list[Instruction]]:
    """Run the whole upstream pipeline. Deterministic given `config.seed`."""
    samples = generate_corpus(config)
    truths, _ = build_corpus_ground_truth(samples, config)
    instructions = build_instructions(samples, truths, config)
    return samples, truths, instructions


def freeze_dataset(config: Config, output_root: Path, repo_root: Path) -> DatasetManifest:
    """Write a frozen corpus and its manifest.

    Raises:
        FreezeError: if any instrument check fails. A corpus that does not satisfy its
            own guarantees must not become the thing every later number depends on.
    """
    samples, truths, instructions = build_artifacts(config)

    checks = run_all(samples, truths, instructions, config, repo_root)
    failed = [c for c in checks if not c.passed]
    if failed:
        raise FreezeError(
            "refusing to freeze; failed checks:\n"
            + "\n".join(f"  {c.name}: {c.detail}" for c in failed)
        )

    staging = output_root / "_staging"
    _discard(staging)

    # Model-visible SVGs: exactly what the model receives.
    for sample in samples:
        _write(staging / "svgs" / f"{sample.svg_id}.svg", sample.model_visible_svg)
        # Real geometry, for audit and regeneration. Never shown to a model.
        _write(staging / "resolved" / f"{sample.svg_id}.svg", sample.resolved_svg)
        _write(
            staging / "groundtruth" / f"{sample.svg_id}.json",
            json.dumps(truths_by_id(truths)[sample.svg_id].model_dump(mode="json"), indent=2),
        )

    _write(
        staging / "instructions.json",
        json.dumps([i.model_dump(mode="json") for i in instructions], indent=2),
    )
    _write(
        staging / "distributions.json",
        json.dumps(compute_distributions(samples, truths, instructions), indent=2),
    )

    dataset_hash, file_hashes = _hash_tree(staging)

    manifest = DatasetManifest(
        schema_version=config.schema_version,
        dataset_hash=dataset_hash,
        config_hash=config_hash(config),
        corpus_config_hash=corpus_config_hash(config),
        seed=config.seed,
        created_by={
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "renderer": _renderer_version(),
        },
        counts={
            "svgs": len(samples),
            "instructions": len(instructions),
            "ambiguity_elements": sum(s.k for s in samples),
        },
        file_hashes=file_hashes,
        checks=tuple(checks),
        model_outputs_observed=False,
    )

    final = output_root / dataset_hash
    if final.exists():
        # A frozen corpus is issued once. Re-freezing to the same hash is harmless -
        # the content is identical by definition - but silently rewriting it would let
        # a directory be replaced without anyone noticing, which is exactly what
        # content-addressing exists to prevent. Verify and keep the original instead.
        _discard(staging)
        existing = DatasetManifest.model_validate_json(
            (final / MANIFEST_NAME).read_text(encoding="utf-8")
        )
        if existing.dataset_hash != dataset_hash:
            raise FreezeError(
                f"{final} exists but its manifest claims {existing.dataset_hash}; "
                "refusing to overwrite a corpus that does not match its own name"
            )
        return existing

    staging.rename(final)

    _write(final / MANIFEST_NAME, json.dumps(manifest.model_dump(mode="json"), indent=2))
    _write(final / CERTIFICATE_NAME, render_certificate(manifest))
    return manifest


def truths_by_id(truths: list[SampleGroundTruth]) -> dict[str, SampleGroundTruth]:
    return {t.svg_id: t for t in truths}


def _renderer_version() -> str:
    try:
        import resvg_py

        return getattr(resvg_py, "__version__", "unknown")
    except ImportError:  # pragma: no cover - renderer is a hard dependency
        return "absent"


def render_certificate(manifest: DatasetManifest) -> str:
    """A human-readable statement of what was checked and what was observed.

    The hashes prove two corpora are the same. This states what kind of corpus it is and,
    critically, that no model output had been seen when it was sealed. That claim is the
    one a sceptical reader most needs and can least verify from a hash.
    """
    width = 72
    lines = [
        "=" * width,
        "INSTRUMENT CERTIFICATE".center(width),
        "=" * width,
        "",
        "  Instrument version   instrument-freeze-v1",
        f"  Dataset hash         {manifest.dataset_hash}",
        f"  Config hash          {manifest.config_hash}",
        f"  Corpus config hash   {manifest.corpus_config_hash}",
        f"  Seed                 {manifest.seed}",
        "",
        f"  SVGs                 {manifest.counts['svgs']}",
        f"  Instructions         {manifest.counts['instructions']}",
        f"  Ambiguity elements   {manifest.counts['ambiguity_elements']}",
        "",
        "-" * width,
        "  CHECKS",
        "-" * width,
        "",
    ]
    for check in manifest.checks:
        status = "PASS" if check.passed else "FAIL"
        lines.append(f"  [{status}]  {check.name}")
        lines.append(f"          {check.detail}")
        lines.append("")

    lines += [
        "-" * width,
        "",
        f"  Python               {manifest.created_by['python']}",
        f"  Platform             {manifest.created_by['platform']}",
        f"  Renderer             {manifest.created_by['renderer']}",
        "",
        "  This corpus is immutable. Any change mints a new dataset hash and",
        "  invalidates prior results rather than silently overwriting them.",
        "",
        "  Verify with:  svgbench verify",
        "",
        "=" * width,
        "",
    ]
    return "\n".join(lines)
