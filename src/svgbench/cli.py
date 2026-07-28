"""Command-line entry point.

This is the canonical way to run anything in this project. `Makefile` and `tasks.ps1`
are thin wrappers over it so that Windows and POSIX reviewers run identical code paths.

Subcommands are registered as the pipeline steps that implement them land. A command
for an unimplemented step exits with a clear message and a non-zero status rather than
a traceback, so a reviewer running ahead of the build gets told what is missing.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from svgbench import __version__
from svgbench.config import ConfigError, config_hash, corpus_config_hash, load_config

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_CONFIG = REPO_ROOT / "configs" / "base.yaml"
EXPERIMENTS_DIR = REPO_ROOT / "configs" / "experiments"

# Pipeline steps in frozen implementation order (see DESIGN_FREEZE.md). A step is
# listed here from the moment it has a CLI surface; `None` means not yet built.
_PLANNED_COMMANDS: dict[str, str] = {
    "generate": "Generate the SVG corpus, ground truth and instructions (steps 3-7)",
    "run": "Execute one experiment arm against a model (steps 10-13)",
    "evaluate": "Score stored responses into evaluation rows (step 9)",
    "report": "Compute metrics and render the report (step 14)",
    "audit": "Run leakage, blindness and determinism checks",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="svgbench",
        description=("Benchmark for visual-reference resolution in under-determined SVG markup."),
        epilog="Design is frozen; see DESIGN_FREEZE.md for the implementation order.",
    )
    parser.add_argument("--version", action="version", version=f"svgbench {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    status = subparsers.add_parser("status", help="Show which pipeline steps are implemented")
    status.set_defaults(handler=_cmd_status)

    config = subparsers.add_parser(
        "config",
        help="Resolve a configuration and print it with its hashes",
    )
    config.add_argument(
        "experiment",
        nargs="?",
        help="Experiment name under configs/experiments (omit for base only)",
    )
    config.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Dotted-key override, e.g. --set generation.n_svgs=5",
    )
    config.set_defaults(handler=_cmd_config)

    freeze = subparsers.add_parser(
        "freeze", help="Freeze the corpus, write its manifest and print the certificate"
    )
    freeze.set_defaults(handler=_cmd_freeze)

    verify = subparsers.add_parser(
        "verify", help="Re-verify the frozen dataset against its manifest"
    )
    verify.add_argument(
        "--determinism",
        action="store_true",
        help="Also regenerate from the seed and compare (needs the renderer)",
    )
    verify.set_defaults(handler=_cmd_verify)

    for name, help_text in _PLANNED_COMMANDS.items():
        planned = subparsers.add_parser(name, help=f"[not yet implemented] {help_text}")
        planned.set_defaults(handler=_make_unimplemented_handler(name, help_text))

    return parser


def _make_unimplemented_handler(name: str, help_text: str):  # type: ignore[no-untyped-def]
    def handler(_args: argparse.Namespace) -> int:
        print(f"svgbench {name}: not implemented yet.", file=sys.stderr)
        print(f"  Planned: {help_text}", file=sys.stderr)
        print("  See DESIGN_FREEZE.md for the frozen implementation order.", file=sys.stderr)
        return 2

    return handler


def _cmd_config(args: argparse.Namespace) -> int:
    """Resolve a config and print it with both hashes.

    The two hashes are the point of this command: `corpus` must match across arms
    (so the paired comparison is valid) while `config` must differ (so their stored
    responses cannot collide). Printing them makes that checkable by hand as well as
    by the audit suite.
    """
    import yaml

    overrides: dict[str, object] = {}
    for item in args.overrides:
        key, separator, raw = item.partition("=")
        if not separator:
            print(f"invalid --set (expected KEY=VALUE): {item!r}", file=sys.stderr)
            return 2
        overrides[key.strip()] = yaml.safe_load(raw)

    experiment_path = None
    if args.experiment:
        name = args.experiment
        experiment_path = EXPERIMENTS_DIR / (name if name.endswith(".yaml") else f"{name}.yaml")
        if not experiment_path.exists():
            available = sorted(p.stem for p in EXPERIMENTS_DIR.glob("*.yaml"))
            print(f"unknown experiment {name!r}; available: {available}", file=sys.stderr)
            return 2

    try:
        loaded = load_config(DEFAULT_BASE_CONFIG, experiment_path, overrides)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(yaml.safe_dump(loaded.config.model_dump(mode="json"), sort_keys=True).rstrip())
    print()
    print(f"sources:     {' + '.join(Path(s).name for s in loaded.sources)}")
    if loaded.overrides:
        print(f"overrides:   {loaded.overrides}")
    print(f"config_hash: {config_hash(loaded.config)}")
    print(f"corpus_hash: {corpus_config_hash(loaded.config)}")
    return 0


def _cmd_freeze(_args: argparse.Namespace) -> int:
    """Freeze the corpus. Refuses if any instrument check fails."""
    from svgbench.dataset import CERTIFICATE_NAME, FreezeError, freeze_dataset

    try:
        config = load_config(DEFAULT_BASE_CONFIG).config
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    frozen_root = REPO_ROOT / "data" / "frozen"
    try:
        manifest = freeze_dataset(config, frozen_root, REPO_ROOT)
    except FreezeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print((frozen_root / manifest.dataset_hash / CERTIFICATE_NAME).read_text(encoding="utf-8"))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    """Check a frozen corpus against its manifest, and optionally re-derive it."""
    from svgbench.dataset import (
        VerificationError,
        find_frozen_datasets,
        verify_determinism,
        verify_integrity,
    )

    datasets = find_frozen_datasets(REPO_ROOT / "data" / "frozen")
    if not datasets:
        print("no frozen dataset found; run `svgbench freeze` first", file=sys.stderr)
        return 1

    exit_code = 0
    for directory in datasets:
        try:
            manifest = verify_integrity(directory)
        except VerificationError as exc:
            print(f"FAIL  {directory.name}\n{exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"PASS  integrity     {manifest.dataset_hash}")

        if args.determinism:
            try:
                config = load_config(DEFAULT_BASE_CONFIG).config
                verify_determinism(config, directory)
            except (ConfigError, VerificationError) as exc:
                print(f"FAIL  determinism   {exc}", file=sys.stderr)
                exit_code = 1
                continue
            print("PASS  determinism   regenerated from seed, byte-identical")

    return exit_code


def _cmd_status(_args: argparse.Namespace) -> int:
    print(f"svgbench {__version__}")
    print("\nPipeline steps (frozen order):")
    steps = [
        ("1.  Repository scaffolding", True),
        ("2.  Configuration system", True),
        ("3.  Dataset generator", True),
        ("4.  Geometry engine", True),
        ("5.  Ground-truth engine", True),
        ("6.  Predicate registry", True),
        ("7.  Instruction generator", True),
        ("8.  Dataset freezing", True),
        ("9.  Evaluation engine", True),
        ("10. Model runner", False),
        ("11. Baseline experiment", False),
        ("12. Enhancement implementation", False),
        ("13. Enhanced experiment", False),
        ("14. Reporting", False),
    ]
    for label, done in steps:
        print(f"  [{'x' if done else ' '}] {label}")
    print("\nNo experiments have been run. No results exist yet.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0
    exit_code: int = args.handler(args)
    return exit_code


if __name__ == "__main__":  # pragma: no cover - exercised via console script
    raise SystemExit(main())
