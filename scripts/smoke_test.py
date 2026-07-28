"""Smoke test: decide model and replicate policy by measurement, before the baseline.

THIS IS NOT A MEASUREMENT. It runs a handful of cases to answer two engineering
questions whose answers must be fixed before Phase II proper begins. Its outputs are
inputs to an ADR, not results, and nothing it prints belongs in OBSERVATIONS.md.

  A1  Does the model emit valid SVG often enough that malformed output is a MINORITY
      failure mode? If not, the experiment measures format compliance rather than
      identification (risk R3), and the model or the output contract must change - which
      R4 explicitly sanctions, provided it happens before the baseline and is recorded.

  ADR-0010  Is the backend deterministic at temperature 0? Replicates are only
      meaningful if it is not. At temperature 0 with a deterministic backend, N
      replicates are N identical calls, and reporting three of them would imply a
      robustness that does not exist. Local backends are often NOT deterministic,
      because of threading and batching - so this is measured rather than assumed.

Deliberately reports identification accuracy too, on a small sample, purely as a sanity
check that the plumbing produces gradable output at all. That number is noise at this
sample size and must not be read as a baseline.

Usage:
    python scripts/smoke_test.py qwen2.5-coder:1.5b [n_cases]
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

from svgbench.config import load_config
from svgbench.context import build_provider
from svgbench.evaluation import evaluate_response, extract_svg, parse_elements
from svgbench.geometry import ElementGeometry
from svgbench.groundtruth import SampleGroundTruth
from svgbench.runner import build_client, build_prompt

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = REPO_ROOT / "configs" / "base.yaml"

DETERMINISM_PROBES = 3


def _frozen_dir() -> Path:
    root = REPO_ROOT / "data" / "frozen"
    directories = [p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").exists()]
    if not directories:
        raise SystemExit("no frozen dataset; run `svgbench freeze` first")
    return directories[0]


def main() -> int:
    model_name = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:1.5b"
    n_cases = int(sys.argv[2]) if len(sys.argv) > 2 else 12

    config = load_config(
        BASE, overrides={"model.name": model_name, "model.backend": "ollama"}
    ).config
    frozen = _frozen_dir()

    instructions = json.loads((frozen / "instructions.json").read_text(encoding="utf-8"))
    svgs = {p.stem: p.read_text(encoding="utf-8") for p in (frozen / "svgs").glob("*.svg")}
    truths = {
        p.stem: SampleGroundTruth.model_validate_json(p.read_text(encoding="utf-8"))
        for p in (frozen / "groundtruth").glob("*.json")
    }

    # Spread across the corpus rather than taking the first n, so the sample is not all
    # from one SVG or one predicate.
    step = max(1, len(instructions) // n_cases)
    sample = instructions[::step][:n_cases]

    client = build_client(config.model)
    provider = build_provider("enhanced", config.context.permutation_seed)

    print(f"model            {model_name}")
    print(f"cases            {len(sample)} of {len(instructions)}")
    print(f"temperature      {config.model.temperature}")
    print(f"dataset          {frozen.name[:16]}...\n")

    outcomes: Counter[str] = Counter()
    latencies: list[int] = []
    completions: list[int] = []
    truncated = 0
    unparseable = 0

    for i, instruction in enumerate(sample, 1):
        svg_id = instruction["svg_id"]
        geometry: dict[str, ElementGeometry] = truths[svg_id].geometry
        prompt = build_prompt(
            svg=svgs[svg_id],
            instruction=instruction["text"],
            context=provider.provide(svg_id, geometry),
        )

        started = time.monotonic()
        response = client.generate(prompt)
        latencies.append(int((time.monotonic() - started) * 1000))
        if response.completion_tokens:
            completions.append(response.completion_tokens)
        truncated += response.truncated

        extracted = extract_svg(response.text)
        if extracted is None or parse_elements(extracted) is None:
            unparseable += 1

        result = evaluate_response(
            case_id=instruction["case_id"],
            original_svg=svgs[svg_id],
            response=response.text,
            operation=instruction["operation"],
            params=instruction["operation_params"],
            target_element_id=instruction["target_element_id"],
        )
        outcomes[result.outcome] += 1
        print(f"  [{i:2d}/{len(sample)}] {result.outcome:<15} {latencies[-1]:>6}ms  {instruction['predicate']}")

    print("\n--- A1: is malformed output a minority failure mode? ---")
    malformed = outcomes["MALFORMED"]
    print(f"  outcomes         {dict(outcomes)}")
    print(f"  unparseable      {unparseable}/{len(sample)} ({100 * unparseable / len(sample):.0f}%)")
    print(f"  truncated        {truncated}/{len(sample)}")
    verdict = "PASS" if malformed <= len(sample) * 0.3 else "FAIL"
    print(f"  verdict          {verdict}  (malformed {malformed}/{len(sample)})")
    if verdict == "FAIL":
        print("  -> A1 violated. The experiment would measure format compliance.")
        print("     Swap the model or adjust the output contract, and record why (R4).")

    print("\n--- ADR-0010: is the backend deterministic at temperature 0? ---")
    probe = sample[0]
    probe_prompt = build_prompt(
        svg=svgs[probe["svg_id"]],
        instruction=probe["text"],
        context=provider.provide(probe["svg_id"], truths[probe["svg_id"]].geometry),
    )
    replies = [client.generate(probe_prompt).text for _ in range(DETERMINISM_PROBES)]
    identical = len(set(replies)) == 1
    print(f"  {DETERMINISM_PROBES} identical prompts -> {len(set(replies))} distinct response(s)")
    if identical:
        print("  DETERMINISTIC -> use 1 replicate. N replicates would be N identical")
        print("  calls, implying a robustness that does not exist.")
    else:
        print("  NON-DETERMINISTIC -> replicates measure real variation and are")
        print("  meaningful. Per-case success RATE becomes the analysis unit.")

    print("\n--- runtime projection (3 arms x 180 cases) ---")
    median = statistics.median(latencies)
    print(f"  median latency   {median:.0f}ms")
    if completions:
        print(f"  median output    {statistics.median(completions):.0f} tokens")
    print(f"  projected        {540 * median / 1000 / 3600:.1f}h for 540 calls")

    print("\nNOTE: identification numbers above are noise at this sample size.")
    print("They are a plumbing check, not a baseline. See OBSERVATIONS.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
