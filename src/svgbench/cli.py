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

from svgbench import __version__

# Pipeline steps in frozen implementation order (see DESIGN_FREEZE.md). A step is
# listed here from the moment it has a CLI surface; `None` means not yet built.
_PLANNED_COMMANDS: dict[str, str] = {
    "generate": "Generate the SVG corpus, ground truth and instructions (steps 3-7)",
    "freeze": "Freeze the corpus and write the dataset manifest (step 8)",
    "verify": "Re-verify a frozen dataset against its manifest (step 8)",
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


def _cmd_status(_args: argparse.Namespace) -> int:
    print(f"svgbench {__version__}")
    print("\nPipeline steps (frozen order):")
    steps = [
        ("1.  Repository scaffolding", True),
        ("2.  Configuration system", False),
        ("3.  Dataset generator", False),
        ("4.  Geometry engine", False),
        ("5.  Ground-truth engine", False),
        ("6.  Predicate registry", False),
        ("7.  Instruction generator", False),
        ("8.  Dataset freezing", False),
        ("9.  Evaluation engine", False),
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
