"""Command-line entry point.

This is the canonical way to run anything in this project. `Makefile` and `tasks.ps1`
are thin wrappers over it so that Windows and POSIX reviewers run identical code paths.

Subcommands are registered as the pipeline steps that implement them land. A command
for an unimplemented step exits with a clear message and a non-zero status rather than
a traceback, so a reviewer running ahead of the build gets told what is missing.
"""

from __future__ import annotations

import argparse
import json
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

    run = subparsers.add_parser("run", help="Execute one experiment arm against the model")
    run.add_argument("experiment", help="Arm name under configs/experiments, e.g. main-baseline")
    run.set_defaults(handler=_cmd_run)

    evaluate = subparsers.add_parser(
        "evaluate", help="Score stored responses (needs no model and no renderer)"
    )
    evaluate.add_argument("experiment", nargs="?", help="Arm name; omit to score every stored arm")
    evaluate.set_defaults(handler=_cmd_evaluate)

    report = subparsers.add_parser(
        "report", help="Regenerate results/metrics.json from committed evaluation rows"
    )
    report.set_defaults(handler=_cmd_report)

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


def _cmd_run(args: argparse.Namespace) -> int:
    """Execute one arm over the frozen corpus.

    Loads by dataset hash and refuses on mismatch, so an arm can never be run against a
    corpus other than the frozen one.
    """
    import json
    import time

    from svgbench.dataset import find_frozen_datasets, verify_integrity
    from svgbench.groundtruth import SampleGroundTruth
    from svgbench.instructions import Instruction
    from svgbench.runner import run_arm

    path = EXPERIMENTS_DIR / f"{args.experiment}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in EXPERIMENTS_DIR.glob("*.yaml"))
        print(f"unknown experiment {args.experiment!r}; available: {available}", file=sys.stderr)
        return 2

    try:
        config = load_config(DEFAULT_BASE_CONFIG, path).config
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    datasets = find_frozen_datasets(REPO_ROOT / "data" / "frozen")
    if not datasets:
        print("no frozen dataset; run `svgbench freeze` first", file=sys.stderr)
        return 1
    frozen = datasets[0]
    manifest = verify_integrity(frozen)

    if manifest.corpus_config_hash != corpus_config_hash(config):
        print(
            "corpus config hash does not match the frozen dataset; refusing to run.\n"
            "  This arm would be scored against a corpus it did not see.",
            file=sys.stderr,
        )
        return 1

    instructions = [
        Instruction.model_validate(record)
        for record in json.loads((frozen / "instructions.json").read_text(encoding="utf-8"))
    ]
    svgs = {p.stem: p.read_text(encoding="utf-8") for p in (frozen / "svgs").glob("*.svg")}
    geometry = {
        p.stem: SampleGroundTruth.model_validate_json(p.read_text(encoding="utf-8")).geometry
        for p in (frozen / "groundtruth").glob("*.json")
    }

    print(f"arm        {config.experiment_id}  (provider: {config.context.provider})")
    print(f"model      {config.model.name}  temp={config.model.temperature}")
    print(f"dataset    {manifest.dataset_hash[:16]}...")
    print(f"cases      {len(instructions)} x {config.evaluation.replicates} replicate(s)\n")

    started = time.monotonic()

    def progress(done: int, total: int) -> None:
        if done % 10 == 0 or done == total:
            elapsed = time.monotonic() - started
            rate = elapsed / done if done else 0.0
            print(
                f"  {done:>4}/{total}  {elapsed / 60:5.1f}m elapsed, "
                f"~{rate * (total - done) / 60:5.1f}m remaining",
                flush=True,
            )

    output = run_arm(
        config=config,
        instructions=instructions,
        svgs=svgs,
        geometry=geometry,
        dataset_hash=manifest.dataset_hash,
        output_root=REPO_ROOT / "experiments",
        on_progress=progress,
    )
    print(f"\nresponses written to {output.relative_to(REPO_ROOT)}")
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    """Score stored responses into evaluation rows.

    Tier-2 reproduction: this reads only the frozen corpus and the committed responses.
    No model, no renderer, no network. A reviewer can re-derive every scored row - or
    write their own scorer and check it against these.
    """
    import json
    from collections import Counter

    from svgbench.dataset import find_frozen_datasets
    from svgbench.evaluation import evaluate_response
    from svgbench.instructions import Instruction

    datasets = find_frozen_datasets(REPO_ROOT / "data" / "frozen")
    if not datasets:
        print("no frozen dataset found", file=sys.stderr)
        return 1
    frozen = datasets[0]

    instructions = {
        i.case_id: i
        for i in (
            Instruction.model_validate(record)
            for record in json.loads((frozen / "instructions.json").read_text(encoding="utf-8"))
        )
    }
    svgs = {p.stem: p.read_text(encoding="utf-8") for p in (frozen / "svgs").glob("*.svg")}

    experiments_root = REPO_ROOT / "experiments"
    arms = sorted(
        p for p in experiments_root.iterdir() if p.is_dir() and (p / "responses.jsonl").exists()
    )
    if args.experiment:
        arms = [p for p in arms if p.name.startswith(args.experiment)]
    if not arms:
        print("no stored responses to score", file=sys.stderr)
        return 1

    exit_code = 0
    for arm in arms:
        rows = []
        with (arm / "responses.jsonl").open("r", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle if line.strip()]

        for record in records:
            instruction = instructions[record["case_id"]]
            result = evaluate_response(
                case_id=record["case_id"],
                original_svg=svgs[record["svg_id"]],
                response=record["response"],
                operation=instruction.operation,
                params=instruction.operation_params,
                target_element_id=instruction.target_element_id,
            )
            rows.append(
                {
                    **result.model_dump(mode="json"),
                    "replicate": record["replicate"],
                    "svg_id": record["svg_id"],
                    "predicate": instruction.predicate,
                    "family": instruction.family,
                    "operation": instruction.operation,
                    "k": instruction.k,
                    "truncated": record["truncated"],
                    "error": record["error"],
                }
            )

        out = arm / "evaluations.jsonl"
        with out.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

        outcomes = Counter(r["outcome"] for r in rows)
        identified = sum(r["target_edited"] for r in rows)
        reference = sum(1.0 / r["k"] for r in rows) / len(rows)

        print(f"\n{arm.name}   n={len(rows)}")
        print(f"  outcomes            {dict(outcomes.most_common())}")
        print(f"  identification      {identified / len(rows):.4f}  ({identified}/{len(rows)})")
        print(f"  1/K reference       {reference:.4f}")
        print(f"  malformed           {outcomes['MALFORMED'] / len(rows):.4f}")
        print(f"  abstained           {outcomes['ABSTAINED'] / len(rows):.4f}")
        print(f"  -> {out.relative_to(REPO_ROOT)}")

    return exit_code


def _cmd_report(_args: argparse.Namespace) -> int:
    """Tier-1 reproduction: every published number, from committed rows, no model."""
    from svgbench.reporting import render_summary, write_report

    try:
        config = load_config(DEFAULT_BASE_CONFIG).config
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        path = write_report(config, REPO_ROOT / "experiments", REPO_ROOT / "results")
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(render_summary(json.loads(path.read_text(encoding="utf-8"))))
    print(f"wrote {path.relative_to(REPO_ROOT)} and results/summary.txt")
    return 0


def _cmd_status(_args: argparse.Namespace) -> int:
    """Print the protocol identity and VERIFY it against what is on disk.

    This command previously printed a hardcoded step list ending in "No experiments have
    been run", which stayed in place after 2,880 responses had been committed. A status
    command that asserts rather than measures is worse than none: it is the first thing a
    visitor runs, and it was confidently wrong.

    Everything below is read from `protocol.json`, the frozen manifest, and the
    experiments directory, and cross-checked. A mismatch is reported and exits non-zero.
    """
    import json

    from svgbench.dataset import find_frozen_datasets

    protocol_path = REPO_ROOT / "protocol.json"
    if not protocol_path.exists():
        print("protocol.json not found", file=sys.stderr)
        return 1
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    problems: list[str] = []

    print(f"svgbench {__version__}   protocol {protocol['protocol_version']}")

    instrument = protocol["instrument"]
    print("\nInstrument")
    print(f"  freeze tag          {instrument['freeze_tag']}")
    print(f"  dataset hash        {instrument['dataset_hash']}")
    print(f"  config hash         {instrument['config_hash']}")
    print(f"  corpus config hash  {instrument['corpus_config_hash']}")
    print(f"  seed                {instrument['seed']}")

    # The dataset directory is named for its own hash, so agreement here is a real check
    # rather than two copies of the same string.
    datasets = find_frozen_datasets(REPO_ROOT / "data" / "frozen")
    if not datasets:
        problems.append("no frozen dataset on disk")
    else:
        frozen = datasets[0]
        manifest = json.loads((frozen / "manifest.json").read_text(encoding="utf-8"))
        for field in ("dataset_hash", "config_hash", "corpus_config_hash", "seed"):
            if manifest.get(field) != instrument[field]:
                problems.append(
                    f"{field}: protocol.json says {instrument[field]!r}, "
                    f"frozen manifest says {manifest.get(field)!r}"
                )
        if manifest.get("model_outputs_observed") is not False:
            problems.append("frozen manifest no longer records model_outputs_observed=false")

    print("\nScoring")
    scoring = protocol["scoring"]
    print(f"  abstention rule     {scoring['abstention_rule_version']}")
    for defect in scoring.get("known_defects", ()):
        print(f"  KNOWN DEFECT        {defect['id']}: {defect['summary'][:64]}...")
        print(f"                      status: {defect['status']}")

    fmt = protocol["fmtcontrol"]
    print("\nfmtcontrol")
    print(f"  version             {fmt['version']}")
    print(f"  spec version        {fmt['spec_version']}")
    vectors_path = REPO_ROOT / "src" / "fmtcontrol" / "conformance_vectors.json"
    if vectors_path.exists():
        vectors = json.loads(vectors_path.read_text(encoding="utf-8"))
        n_vectors = len(vectors["vectors"])
        n_raise = len(vectors["must_raise"])
        print(f"  conformance vectors {n_vectors} + {n_raise} must-raise")
        if vectors["spec_version"] != fmt["spec_version"]:
            problems.append(
                f"spec version: protocol.json says {fmt['spec_version']!r}, "
                f"vectors say {vectors['spec_version']!r}"
            )
    else:
        problems.append("conformance vectors missing")

    print("\nStudies")
    for study in protocol["studies"]:
        print(f"  {study['id']:4s} {study['question'][:66]}")
        print(f"       -> {study['outcome']}")

    experiments = REPO_ROOT / "experiments"
    stored = sorted(p for p in experiments.iterdir() if (p / "responses.jsonl").exists())
    total = 0
    for directory in stored:
        with (directory / "responses.jsonl").open("r", encoding="utf-8") as handle:
            total += sum(1 for line in handle if line.strip())
    print(f"\nStored responses      {total} across {len(stored)} conditions")

    open_items = protocol["open"]
    print("\nOpen")
    print(f"  central claim exercised     {open_items['central_claim_exercised']}")
    print(f"  independent implementations {open_items['independent_implementations']}")
    print(f"  independent replications    {open_items['independent_replications']}")
    print(f"  next study                  {open_items['next_study']}")

    if problems:
        print(f"\nPROTOCOL MISMATCH ({len(problems)}):", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("\nprotocol.json agrees with the frozen manifest and the committed vectors.")
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
