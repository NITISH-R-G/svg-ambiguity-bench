"""Audit: the arms differ in exactly one variable.

The central claim of this repository is a difference between arms. A difference is
only interpretable if everything except the manipulated variable is identical, so
that property must be machine-checked rather than asserted in prose.

This is the config-level half of the guarantee. The other half is structural: the
ContextProvider signature excludes the instruction, so blindness cannot be violated
by code that has not been written yet (ADR-0005).

Motivated by Biderman et al. 2024 (arXiv 2405.14782), which documents that undocumented
or drifting evaluation settings - not flawed reasoning - are the dominant cause of
irreproducible LLM results, with observed swings above 20% and reordered rankings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from svgbench.config import config_hash, corpus_config_hash, load_config

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"
EXPERIMENTS = REPO_ROOT / "configs" / "experiments"

# The manipulated variable, and the only section permitted to differ between arms.
MANIPULATED_SECTION = "context"

# The label is not a parameter; it is expected to differ and is excluded from the hash.
LABEL_FIELD = "experiment_id"


def _arm_configs() -> dict[str, dict[str, Any]]:
    return {
        path.name: load_config(BASE, path).config.model_dump(mode="json")
        for path in sorted(EXPERIMENTS.glob("main-*.yaml"))
    }


@pytest.mark.audit
def test_arms_differ_only_in_the_context_section() -> None:
    arms = _arm_configs()
    assert len(arms) >= 3, "expected at least baseline, permuted and enhanced"

    reference_name, reference = next(iter(arms.items()))
    for name, cfg in arms.items():
        if name == reference_name:
            continue
        differing = {key for key in set(reference) | set(cfg) if reference.get(key) != cfg.get(key)}
        unexpected = differing - {MANIPULATED_SECTION, LABEL_FIELD}
        assert not unexpected, (
            f"{name} differs from {reference_name} outside the manipulated variable: "
            f"{sorted(unexpected)}. Arms must differ only in `{MANIPULATED_SECTION}`."
        )


@pytest.mark.audit
def test_every_arm_uses_a_distinct_context_provider() -> None:
    """A duplicated provider means two arms are secretly the same experiment."""
    providers = {name: cfg["context"]["provider"] for name, cfg in _arm_configs().items()}
    assert len(set(providers.values())) == len(providers), f"duplicate arms: {providers}"


@pytest.mark.audit
def test_arms_share_a_corpus_but_are_distinct_experiments() -> None:
    """Same cases (so pairing is valid), different config identity (so runs cannot collide)."""
    configs = [load_config(BASE, p).config for p in sorted(EXPERIMENTS.glob("main-*.yaml"))]
    assert len({corpus_config_hash(c) for c in configs}) == 1, "arms must share one corpus"
    assert len({config_hash(c) for c in configs}) == len(configs), "arms must be distinct runs"


@pytest.mark.audit
def test_decoding_settings_are_identical_across_arms() -> None:
    """Called out separately from the section check because this is the classic drift.

    A temperature or token limit that moved between runs would make any measured
    difference an artifact, and it is exactly the kind of change that gets made
    mid-experiment for an innocent-looking reason.
    """
    decoding = {
        name: {
            k: cfg["model"][k]
            for k in ("name", "backend", "temperature", "top_p", "seed", "max_output_tokens")
        }
        for name, cfg in _arm_configs().items()
    }
    distinct = {tuple(sorted(d.items())) for d in decoding.values()}
    assert len(distinct) == 1, f"decoding settings drifted between arms: {decoding}"


@pytest.mark.audit
def test_baseline_supplies_no_context() -> None:
    """The manipulation check must actually withhold the information."""
    baseline = load_config(BASE, EXPERIMENTS / "main-baseline.yaml").config
    assert baseline.context.provider == "null"


@pytest.mark.audit
def test_permuted_arm_exists() -> None:
    """Without it, `enhanced > baseline` cannot distinguish information from format.

    See ADR-0009. This is the control the central claim rests on, so its absence
    should fail the build rather than be noticed at analysis time.
    """
    permuted = load_config(BASE, EXPERIMENTS / "main-permuted.yaml").config
    assert permuted.context.provider == "permuted"
