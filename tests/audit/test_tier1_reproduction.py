"""Audit: Tier-1 reproduction actually works.

The README promises that a reviewer can regenerate every published number from
committed evaluation rows, with no model and no renderer, in about a minute. That
promise was once false: `results/metrics.json` existed but the code that produced it
did not, so the headline numbers were unreproducible by anything in the repository.

This test exists so that cannot silently recur. It is the check that C6 - every number
independently verifiable - actually holds rather than merely being asserted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.reporting import build_report, render_summary

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"
EXPERIMENTS = REPO_ROOT / "experiments"
RESULTS = REPO_ROOT / "results" / "metrics.json"

pytestmark = pytest.mark.skipif(not RESULTS.exists(), reason="no results committed yet")


@pytest.mark.audit
def test_committed_metrics_are_regenerable() -> None:
    """The committed numbers must be exactly what the committed code produces.

    A mismatch means the published figures came from somewhere other than this
    repository - which is the failure this test was written after finding.
    """
    config = load_config(BASE).config
    regenerated = build_report(config, EXPERIMENTS)
    committed = json.loads(RESULTS.read_text(encoding="utf-8"))
    assert regenerated == committed, (
        "results/metrics.json does not match what `svgbench report` produces. "
        "Either the code changed without regenerating, or the file was produced "
        "by something not in this repository."
    )


@pytest.mark.audit
def test_report_is_deterministic() -> None:
    """Seeded resampling, so two runs must agree exactly."""
    config = load_config(BASE).config
    assert build_report(config, EXPERIMENTS) == build_report(config, EXPERIMENTS)


@pytest.mark.audit
def test_reporting_imports_no_model_or_renderer() -> None:
    """Tier 1 must run on a machine with neither installed."""
    import ast

    forbidden = {"resvg_py", "PIL", "svgelements", "httpx", "matplotlib"}
    for path in (REPO_ROOT / "src" / "svgbench" / "reporting").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            assert not (set(names) & forbidden), f"{path.name} imports {names}"


@pytest.mark.audit
def test_summary_reports_mde_and_warns_about_p_values() -> None:
    """With a difference of exactly zero the p-value is degenerate, so the summary must
    say so rather than let a reader treat p=1.000 as evidence of no effect."""
    config = load_config(BASE).config
    summary = render_summary(build_report(config, EXPERIMENTS))
    assert "MINIMUM DETECTABLE EFFECT" in summary
    assert "degenerate" in summary
