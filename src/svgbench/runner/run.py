"""The single shared execution path for every arm.

Supports C2: the arms differ in exactly one variable.

There is one runner and one prompt template. An arm is chosen by which `ContextProvider`
fills the template's context slot, and nothing else in this file branches on it. Two
separately-authored pipelines would drift - a retry policy tweaked here, a stop sequence
added there - and no amount of care downstream would recover the comparison.

Context is resolved once per SVG and reused across that SVG's instructions. Efficiency is
the lesser reason; the greater one is that a block serving six different instructions
demonstrably depends on none of them.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from svgbench.config import Config, config_hash, corpus_config_hash
from svgbench.context import build_provider
from svgbench.geometry import ElementGeometry
from svgbench.instructions import Instruction
from svgbench.runner.client import build_client
from svgbench.runner.prompt import TEMPLATE_ID, TEMPLATE_VERSION, build_prompt
from svgbench.runner.store import ResponseStore


def run_arm(
    config: Config,
    instructions: list[Instruction],
    svgs: dict[str, str],
    geometry: dict[str, dict[str, ElementGeometry]],
    dataset_hash: str,
    output_root: Path,
    on_progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Execute one arm over every case. Returns the response file.

    Args:
        svgs: model-visible SVG per svg_id - exactly what the model receives.
        geometry: measured geometry per svg_id, for the context provider. Never reaches
            the model except through a provider.

    Raises:
        ValueError: if a prompt would exceed the model's context limit. Truncation would
            inflate malformed rates in the arm with the longest prompts, which is the
            enhanced one - turning a format artefact into an apparent result.
    """
    experiment_id = f"{config.experiment_id}_{config_hash(config)[:12]}"
    store = ResponseStore(output_root, experiment_id)
    provider = build_provider(config.context.provider, config.context.permutation_seed)
    client = build_client(config.model)

    _write_manifest(config, dataset_hash, experiment_id, output_root, provider.name)

    # Resolved per SVG, not per case. This is the blindness guarantee in practice.
    context_by_svg = {
        svg_id: provider.provide(svg_id, element_geometry)
        for svg_id, element_geometry in geometry.items()
    }

    total = len(instructions) * config.evaluation.replicates
    done = 0

    for instruction in instructions:
        prompt = build_prompt(
            svg=svgs[instruction.svg_id],
            instruction=instruction.text,
            context=context_by_svg[instruction.svg_id],
        )
        # Rough token estimate; the exact count comes back with the response. Checked
        # before spending a call rather than discovered afterwards.
        if len(prompt) // 3 > config.model.context_limit:
            raise ValueError(
                f"{instruction.case_id}: prompt of ~{len(prompt) // 3} tokens exceeds "
                f"the context limit of {config.model.context_limit}"
            )

        for replicate in range(config.evaluation.replicates):
            done += 1
            if store.has(instruction.case_id, replicate):
                continue

            response = client.generate(prompt)
            store.append(
                {
                    "case_id": instruction.case_id,
                    "instruction_id": instruction.instruction_id,
                    "svg_id": instruction.svg_id,
                    "replicate": replicate,
                    "prompt": prompt,
                    "response": response.text,
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "latency_ms": response.latency_ms,
                    "truncated": response.truncated,
                    "error": response.error,
                }
            )
            if on_progress:
                on_progress(done, total)

    return store.path


def _write_manifest(
    config: Config,
    dataset_hash: str,
    experiment_id: str,
    output_root: Path,
    provider_name: str,
) -> None:
    """Bind responses to the corpus, config, model and decoding that produced them.

    Without this a stored response is an orphan: reproducible in principle, unattributable
    in practice.
    """
    manifest: dict[str, Any] = {
        "experiment_id": experiment_id,
        "arm": config.experiment_id,
        "context_provider": provider_name,
        "dataset_hash": dataset_hash,
        "config_hash": config_hash(config),
        "corpus_config_hash": corpus_config_hash(config),
        "prompt": {"template_id": TEMPLATE_ID, "template_version": TEMPLATE_VERSION},
        "model": config.model.model_dump(mode="json"),
        "replicates": config.evaluation.replicates,
    }
    path = output_root / experiment_id / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
