"""Study V2 - target identification validation.

Pre-registered at the `study-v2-preregistration` tag. See
`docs/05-study-v2-preregistration.md` for the question, the interpretation bands, and
the manipulation checks this script enforces.

V1 varied the CONTEXT while holding the instruction fixed. V2 varies the INSTRUCTION
while holding context fixed at none. That asymmetry is forced by the architecture rather
than chosen: `ContextProvider.provide(svg_id, geometry)` has no instruction parameter, so
a provider cannot know which element is the target and naming the target is not
expressible as a context arm (ADR-0005).

Deliberately a script rather than a `Config` field. `config_hash` hashes the entire
dumped model, so adding a field would change V1's hash, orphan the committed
`experiments/main-*_<hash>/` directories, and break Tier-1 and Tier-2 reproduction. The
frozen instrument is reused unmodified: same prompt template, same client, same store,
and afterwards the same scorer via `svgbench evaluate`.

Usage:
    python scripts/study_v2_named_id.py            # run it
    python scripts/study_v2_named_id.py --check    # manipulation checks only, no model
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from svgbench.config import load_config
from svgbench.dataset import find_frozen_datasets
from svgbench.instructions import Instruction
from svgbench.instructions.templates import OPERATION_PHRASES
from svgbench.runner.client import build_client
from svgbench.runner.prompt import TEMPLATE_ID, TEMPLATE_VERSION, build_prompt
from svgbench.runner.store import ResponseStore

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "study-v2-named-id"

# Operation variant 0 for every case, so the edit clause is one fixed wording per
# operation. V1 varied the wording to separate phrasing effects from capability; V2 is
# not measuring phrasing, and holding it fixed removes a source of variance that would
# otherwise sit between V2 and the V1 arms it is compared against.
_OPERATION_VARIANT = 0


def named_id_text(instruction: Instruction) -> str:
    """Rewrite one instruction to name its target element explicitly.

    The operation phrase and its parameters are reused verbatim from the frozen
    templates; only the `{target}` slot changes. So the edit being requested is
    identical to V1's for the same case, and the sole difference is that the element is
    identified rather than described.
    """
    phrase = OPERATION_PHRASES[instruction.operation][_OPERATION_VARIANT]
    target = f'the element with id="{instruction.target_element_id}"'
    return phrase.format(target=target, **instruction.operation_params)


def _load_frozen() -> tuple[Path, list[Instruction], dict[str, str]]:
    datasets = find_frozen_datasets(REPO_ROOT / "data" / "frozen")
    if not datasets:
        print("no frozen dataset found", file=sys.stderr)
        raise SystemExit(1)
    frozen = datasets[0]
    instructions = [
        Instruction.model_validate(record)
        for record in json.loads((frozen / "instructions.json").read_text(encoding="utf-8"))
    ]
    svgs = {p.stem: p.read_text(encoding="utf-8") for p in (frozen / "svgs").glob("*.svg")}
    return frozen, instructions, svgs


def _v1_baseline_prompts() -> dict[str, str]:
    """The V1 baseline prompt per case, for the differ-only-in-the-instruction check."""
    root = REPO_ROOT / "experiments"
    candidates = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("main-baseline")]
    if not candidates:
        return {}
    path = candidates[0] / "responses.jsonl"
    with path.open("r", encoding="utf-8") as handle:
        return {
            record["case_id"]: record["prompt"]
            for record in (json.loads(line) for line in handle if line.strip())
        }


def check(instructions: list[Instruction], svgs: dict[str, str]) -> int:
    """Run every pre-registered manipulation check. Returns a process exit code.

    These run before the primary outcome is computed, because each one can void the
    study rather than inform it. A failure here means the run is discarded, not
    interpreted.
    """
    failures: list[str] = []

    baseline_prompts = _v1_baseline_prompts()
    if not baseline_prompts:
        failures.append("V1 baseline prompts unavailable; cannot check prompt equality")

    for instruction in instructions:
        text = named_id_text(instruction)

        # 1. The instruction names the target id verbatim.
        if instruction.target_element_id not in text:
            failures.append(f"{instruction.case_id}: id not present in rewritten instruction")

        # 2. No referring expression survives. If one did, the condition would still be
        #    partly a reference-resolution task and the study would measure a mixture.
        lowered = text.lower()
        for word in ("left", "right", "top", "bottom", "largest", "smallest", "biggest"):
            if word in lowered:
                failures.append(f"{instruction.case_id}: referring word {word!r} survives rewrite")

        # 3. The operation clause is the frozen one for this operation, with the frozen
        #    params. Reconstructing it independently would let a typo change the edit.
        expected = OPERATION_PHRASES[instruction.operation][_OPERATION_VARIANT].format(
            target=f'the element with id="{instruction.target_element_id}"',
            **instruction.operation_params,
        )
        if text != expected:
            failures.append(f"{instruction.case_id}: operation clause altered")

        # 4. Prompts differ from V1 baseline only inside the instruction line.
        if baseline_prompts:
            v1 = baseline_prompts.get(instruction.case_id)
            if v1 is None:
                failures.append(f"{instruction.case_id}: absent from V1 baseline")
            else:
                v2 = build_prompt(svg=svgs[instruction.svg_id], instruction=text, context="")
                if _outside_instruction_line(v1) != _outside_instruction_line(v2):
                    failures.append(f"{instruction.case_id}: prompt differs outside instruction")

    # 5. Exactly V1's case set.
    if baseline_prompts and {i.case_id for i in instructions} != set(baseline_prompts):
        failures.append("case set differs from V1")

    print(f"manipulation checks over {len(instructions)} cases")
    if failures:
        print(f"  FAILED ({len(failures)})", file=sys.stderr)
        for line in failures[:20]:
            print(f"    {line}", file=sys.stderr)
        if len(failures) > 20:
            print(f"    ... and {len(failures) - 20} more", file=sys.stderr)
        return 1
    print("  all checks passed")
    return 0


def _outside_instruction_line(prompt: str) -> list[str]:
    """Every line of a prompt except the one carrying the instruction."""
    return [line for line in prompt.splitlines() if not line.startswith("Instruction:")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="run manipulation checks only; no model calls"
    )
    args = parser.parse_args()

    _, instructions, svgs = _load_frozen()
    instructions.sort(key=lambda i: i.case_id)

    code = check(instructions, svgs)
    if code or args.check:
        return code

    # base.yaml alone, with no experiment overlay: the model block and decoding settings
    # are identical across every V1 arm, and V2's context is none, which is base's
    # default. Loading an arm overlay would imply this run belongs to that arm.
    config = load_config(REPO_ROOT / "configs" / "base.yaml").config
    client = build_client(config.model)
    store = ResponseStore(REPO_ROOT / "experiments", EXPERIMENT_ID)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "study": "v2",
        "preregistration": "docs/05-study-v2-preregistration.md",
        "preregistration_tag": "study-v2-preregistration",
        "condition": "named_id",
        "manipulated_variable": "instruction",
        "context_provider": "null",
        "prompt": {"template_id": TEMPLATE_ID, "template_version": TEMPLATE_VERSION},
        "model": config.model.model_dump(mode="json"),
        "replicates": 1,
        "note": (
            "Instruction condition, not a context arm. V1 arms are unaffected and "
            "their numbers do not change as a result of this run."
        ),
    }
    manifest_path = REPO_ROOT / "experiments" / EXPERIMENT_ID / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )

    total = len(instructions)
    for index, instruction in enumerate(instructions, start=1):
        if store.has(instruction.case_id, 0):
            continue
        text = named_id_text(instruction)
        prompt = build_prompt(svg=svgs[instruction.svg_id], instruction=text, context="")
        if len(prompt) // 3 > config.model.context_limit:
            print(f"{instruction.case_id}: prompt exceeds context limit", file=sys.stderr)
            return 1

        response = client.generate(prompt)
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
                "error": response.error,
            }
        )
        print(f"  [{index:3d}/{total}] {instruction.case_id}", flush=True)

    print(f"\nwrote {store.path.relative_to(REPO_ROOT)}")
    print("score it with:  python -m svgbench.cli evaluate study-v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
