"""Study V3 - model generality, and the first real test of the format-matched control.

Pre-registered at the `study-v3-preregistration` tag. See
`docs/07-study-v3-preregistration.md` for the questions, the FIRES/PARTIAL/SILENT
decision rules, and the falsifiers.

Sweeps four conditions per model over the frozen corpus:

    baseline   no context
    permuted   geometry table, values shuffled between elements  <- the control
    enhanced   geometry table, correct
    named_id   no context; the instruction names the target element by id (Study V2)

The primary outcome is `enhanced - permuted`, per model. Not `enhanced - baseline`,
which confounds the information with the format it arrives in.

A script rather than config plumbing, for the same reason as V2: `config_hash` hashes the
whole dumped model, so adding fields would change V1's hash and orphan the committed
`experiments/main-*_<hash>/` directories. Everything frozen is reused verbatim - the
corpus, the prompt template, the context providers, the store, and afterwards the scorer.

Results for `qwen2.5-coder:3b` are NOT recomputed. V1 and V2 already measured that model
and those numbers are reused unchanged.

Usage:
    python scripts/study_v3_models.py --check
    python scripts/study_v3_models.py --model llama3.2:3b
    python scripts/study_v3_models.py                      # every pending model
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from svgbench.config import load_config
from svgbench.context import build_provider
from svgbench.dataset import find_frozen_datasets
from svgbench.geometry import ElementGeometry
from svgbench.instructions import Instruction
from svgbench.runner.client import build_client
from svgbench.runner.prompt import TEMPLATE_ID, TEMPLATE_VERSION, build_prompt
from svgbench.runner.store import ResponseStore

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study_v2_named_id import named_id_text

REPO_ROOT = Path(__file__).resolve().parents[1]

# The reference model. Already measured by V1 and V2; reused, never re-run.
REFERENCE_MODEL = "qwen2.5-coder:3b"

MODELS: tuple[str, ...] = (
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:7b",
    "llama3.2:3b",
)

# `named_id` is not a context arm - it varies the instruction and leaves context empty.
# See ADR-0005: providers are instruction-blind by type signature, so naming the target
# is not expressible as a provider.
CONDITIONS: tuple[str, ...] = ("baseline", "permuted", "enhanced", "named_id")

_PROVIDER_FOR = {"baseline": "null", "permuted": "permuted", "enhanced": "enhanced"}


def _slug(model: str) -> str:
    return model.replace(":", "-").replace("/", "-")


def experiment_id(model: str, condition: str) -> str:
    return f"v3-{_slug(model)}-{condition}"


def _load_frozen() -> tuple[
    list[Instruction], dict[str, str], dict[str, dict[str, ElementGeometry]]
]:
    datasets = find_frozen_datasets(REPO_ROOT / "data" / "frozen")
    if not datasets:
        print("no frozen dataset found", file=sys.stderr)
        raise SystemExit(1)
    frozen = datasets[0]
    instructions = sorted(
        (
            Instruction.model_validate(record)
            for record in json.loads((frozen / "instructions.json").read_text(encoding="utf-8"))
        ),
        key=lambda i: i.case_id,
    )
    model_visible = {p.stem: p.read_text(encoding="utf-8") for p in (frozen / "svgs").glob("*.svg")}
    return instructions, model_visible, _frozen_geometry(frozen)


def _frozen_geometry(frozen: Path) -> dict[str, dict[str, ElementGeometry]]:
    """Read geometry from the frozen ground truth rather than re-measuring it.

    The model-visible SVGs have their path data redacted, so nothing can be measured
    from them. Reading the frozen artefact makes the V3 context byte-identical to what
    V1's arms received, by construction.

    Both witnesses are loaded, not just one. `ElementGeometry.area` and `.centroid` are
    the RASTER measurements by definition (ADR-0004: the ordinal predicates are
    perceptual, and pixel coverage is what a viewer integrates). Reconstructing from the
    analytic values alone would silently feed the providers a different table than V1
    used.
    """
    geometry: dict[str, dict[str, ElementGeometry]] = {}
    for path in sorted((frozen / "groundtruth").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        geometry[record["svg_id"]] = {
            element_id: ElementGeometry.model_validate(entry)
            for element_id, entry in record["geometry"].items()
        }
    return geometry


def available_models() -> set[str]:
    import httpx

    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return {m["name"] for m in response.json().get("models", [])}
    except Exception:
        return set()


def check() -> int:
    """Pre-flight. Confirms the corpus, the conditions, and which models are present."""
    instructions, model_visible, geometry = _load_frozen()
    present = available_models()

    print(f"corpus            {len(instructions)} cases, {len(model_visible)} svgs")
    print(f"conditions        {', '.join(CONDITIONS)}")
    print(f"reference (reuse) {REFERENCE_MODEL}")
    print()

    empty = [s for s, g in geometry.items() if not g]
    if empty:
        print(f"  FAIL: geometry empty for {len(empty)} svgs, e.g. {empty[:3]}", file=sys.stderr)
        return 1
    print(f"geometry          measured for {len(geometry)} svgs")

    # The control must actually differ from the treatment, per svg.
    enh = build_provider("enhanced", 991)
    perm = build_provider("permuted", 991)
    identical = [s for s, g in geometry.items() if enh.provide(s, g) == perm.provide(s, g)]
    if identical:
        print(f"  FAIL: permuted == enhanced for {identical[:3]}", file=sys.stderr)
        return 1
    print(f"control           permuted differs from enhanced on all {len(geometry)} svgs")

    missing = [m for m in MODELS if m not in present]
    print()
    for model in MODELS:
        mark = "ok     " if model in present else "MISSING"
        print(f"  {mark} {model}")
    if missing:
        print(f"\n  {len(missing)} model(s) not pulled yet", file=sys.stderr)
        return 2
    return 0


def run_condition(model: str, condition: str) -> None:
    instructions, model_visible, geometry = _load_frozen()
    config = load_config(REPO_ROOT / "configs" / "base.yaml").config
    model_config = config.model.model_copy(update={"name": model})
    client = build_client(model_config)

    store = ResponseStore(REPO_ROOT / "experiments", experiment_id(model, condition))

    context_by_svg: dict[str, str] = {}
    if condition != "named_id":
        provider = build_provider(_PROVIDER_FOR[condition], config.context.permutation_seed)
        context_by_svg = {s: provider.provide(s, g) for s, g in geometry.items()}

    manifest = {
        "experiment_id": experiment_id(model, condition),
        "study": "v3",
        "preregistration": "docs/07-study-v3-preregistration.md",
        "preregistration_tag": "study-v3-preregistration",
        "condition": condition,
        "context_provider": _PROVIDER_FOR.get(condition, "null"),
        "manipulated_variable": "instruction" if condition == "named_id" else "context",
        "prompt": {"template_id": TEMPLATE_ID, "template_version": TEMPLATE_VERSION},
        "model": model_config.model_dump(mode="json"),
        "replicates": 1,
    }
    path = REPO_ROOT / "experiments" / experiment_id(model, condition) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8", newline="\n")

    total = len(instructions)
    errors = 0
    for index, instruction in enumerate(instructions, start=1):
        if store.has(instruction.case_id, 0):
            continue
        text = named_id_text(instruction) if condition == "named_id" else instruction.text
        prompt = build_prompt(
            svg=model_visible[instruction.svg_id],
            instruction=text,
            context=context_by_svg.get(instruction.svg_id, ""),
        )
        response = client.generate(prompt)
        if response.error:
            # Never persist a transport failure as a completed case: `store.has` would
            # then skip it on resume and a connection fault would be scored as a model
            # result. This exact defect corrupted the first V2 pass.
            errors += 1
            print(f"    ! {instruction.case_id}: {response.error[:60]}", file=sys.stderr)
            if errors >= 10:
                print("    aborting: 10 consecutive transport errors", file=sys.stderr)
                raise SystemExit(1)
            continue
        errors = 0
        store.append(
            {
                "case_id": instruction.case_id,
                "instruction_id": instruction.instruction_id,
                "svg_id": instruction.svg_id,
                "replicate": 0,
                "prompt": prompt,
                "response": response.text,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "latency_ms": response.latency_ms,
                "truncated": response.truncated,
                "error": None,
            }
        )
        if index % 30 == 0:
            print(f"    [{index:3d}/{total}]", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="pre-flight only, no model calls")
    parser.add_argument("--model", help="run one model only")
    args = parser.parse_args()

    if args.check:
        return check()

    present = available_models()
    targets = [args.model] if args.model else [m for m in MODELS if m in present]
    if not targets:
        print("no target models available", file=sys.stderr)
        return 1

    for model in targets:
        if model == REFERENCE_MODEL:
            print(f"skip {model}: reference, reused from V1/V2")
            continue
        for condition in CONDITIONS:
            print(f"\n=== {model}  {condition} ===", flush=True)
            run_condition(model, condition)
    print("\nscore with:  python -m svgbench.cli evaluate v3-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
