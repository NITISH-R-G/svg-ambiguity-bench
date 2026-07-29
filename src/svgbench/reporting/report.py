"""Render metrics into `results/metrics.json` and a human-readable summary.

Contains no analysis logic. Every number here comes from `svgbench.metrics`; it must be
impossible to compute a value in this module that does not already exist there.

This is Tier-1 reproduction. It reads committed evaluation rows and nothing else - no
model, no renderer, no network - so a reviewer can regenerate every published number in
about a second. The headline table in the README and `docs/04-results.md` is generated
from this output rather than typed by hand.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from svgbench.config import Config
from svgbench.metrics import (
    arm_metrics,
    load_rows,
    minimum_detectable_effect,
    paired_permutation,
)

# Reported in this order: manipulation check, format control, treatment.
ARM_ORDER = ("main-baseline", "main-permuted", "main-enhanced")

# The pre-registered comparisons, in the order RESULTS.md commits to reading them.
COMPARISONS = (
    ("O-002", "main-enhanced", "main-baseline", "necessary, not sufficient"),
    ("O-003", "main-enhanced", "main-permuted", "THE CENTRAL CLAIM (C3)"),
    ("O-extra", "main-permuted", "main-baseline", "format effect alone"),
)


def build_report(config: Config, experiments_root: Path) -> dict[str, Any]:
    """Compute every reported number from committed evaluation rows."""
    settings = config.metrics
    arms = load_rows(experiments_root)
    present = [name for name in ARM_ORDER if name in arms]
    if not present:
        raise FileNotFoundError(f"no evaluation rows under {experiments_root}")

    metrics = {
        name: arm_metrics(
            name,
            arms[name],
            settings.bootstrap_iterations,
            settings.bootstrap_seed,
            settings.ci_level,
        )
        for name in present
    }

    comparisons: dict[str, Any] = {}
    for label, left, right, note in COMPARISONS:
        if left not in arms or right not in arms:
            continue
        key = f"{label}_{left.removeprefix('main-')}_vs_{right.removeprefix('main-')}"
        result = paired_permutation(
            arms[left],
            arms[right],
            "target_edited",
            settings.permutation_iterations,
            settings.permutation_seed,
        )
        comparisons[key] = {**result, "note": note}

    return {
        "arms": {name: metrics[name].model_dump(mode="json") for name in present},
        "comparisons": comparisons,
        "minimum_detectable_effect": minimum_detectable_effect(
            arms[present[0]], settings.permutation_iterations, settings.permutation_seed
        ),
        "settings": {
            "bootstrap_iterations": settings.bootstrap_iterations,
            "bootstrap_seed": settings.bootstrap_seed,
            "permutation_iterations": settings.permutation_iterations,
            "permutation_seed": settings.permutation_seed,
            "ci_level": settings.ci_level,
            "cluster_unit": settings.cluster_unit,
        },
    }


def render_summary(report: dict[str, Any]) -> str:
    """The headline table, generated rather than typed."""
    arms = report["arms"]
    names = [n for n in ARM_ORDER if n in arms]
    lines: list[str] = []

    def rule(char: str = "-") -> None:
        lines.append(char * 78)

    rule("=")
    lines.append("PRIMARY METRIC: IDENTIFICATION ACCURACY")
    lines.append("  cluster bootstrap over SVGs; the SVG is the unit of resampling")
    rule("=")
    lines.append(f"  {'arm':<12} {'n':>4} {'clusters':>9}   identification accuracy")
    for name in names:
        a = arms[name]
        i = a["identification"]
        lines.append(
            f"  {name.removeprefix('main-'):<12} {a['n_cases']:>4} {a['n_clusters']:>9}   "
            f"{i['point']:.4f} [{i['low']:.4f}, {i['high']:.4f}]"
        )
    lines.append(
        f"\n  per-case random-selection reference: {arms[names[0]]['random_reference']:.4f}"
    )

    lines.append("")
    rule("=")
    lines.append("PRE-REGISTERED COMPARISONS (paired cluster-level permutation)")
    rule("=")
    for key, c in report["comparisons"].items():
        lines.append(f"\n  {key}   [{c['note']}]")
        lines.append(
            f"    difference {c['observed_difference']:+.4f}"
            f"   p = {c['p_value']:.3f}"
            f"   ({int(c['n_clusters'])} clusters, {int(c['n_paired_cases'])} paired cases)"
        )

    mde = report["minimum_detectable_effect"]
    lines.append(f"\n  MINIMUM DETECTABLE EFFECT: {mde:.4f}")
    lines.append("  Read this, not the p-values. With a difference of exactly zero no")
    lines.append("  permutation can be more extreme, so p is degenerate and uninformative.")

    lines.append("")
    rule("=")
    lines.append("SECONDARY METRICS")
    rule("=")
    header = f"  {'arm':<12} {'strict':>8} {'collateral':>11} {'mean elts':>10}"
    header += f" {'MALFORMED':>10} {'ABSTAINED':>10} {'NO_EDIT':>8}"
    lines.append(header)
    for name in names:
        a = arms[name]
        o = a["outcomes"]
        lines.append(
            f"  {name.removeprefix('main-'):<12} {a['strict']['point']:>8.4f}"
            f" {a['collateral_rate']['point']:>11.4f} {a['mean_elements_modified']:>10.2f}"
            f" {o.get('MALFORMED', 0):>10} {o.get('ABSTAINED', 0):>10} {o.get('NO_EDIT', 0):>8}"
        )

    lines.append("")
    rule("=")
    lines.append("BY FAMILY, THEN BY PREDICATE (identification accuracy)")
    rule("=")
    lines.append(f"  {'arm':<12} {'SPATIAL':>9} {'ORDINAL':>9}")
    for name in names:
        f = arms[name]["by_family"]
        lines.append(
            f"  {name.removeprefix('main-'):<12} {f.get('SPATIAL', 0.0):>9.4f}"
            f" {f.get('ORDINAL_SIZE', 0.0):>9.4f}"
        )

    predicates = sorted(arms[names[0]]["by_predicate"])
    lines.append("")
    lines.append(f"  {'predicate':<16}" + "".join(f"{n.removeprefix('main-'):>11}" for n in names))
    for predicate in predicates:
        row = f"  {predicate:<16}"
        row += "".join(f"{arms[n]['by_predicate'][predicate]:>11.3f}" for n in names)
        lines.append(row)

    lines.append("")
    return "\n".join(lines)


def write_report(config: Config, experiments_root: Path, results_root: Path) -> Path:
    """Write `results/metrics.json`. Deterministic: rerunning reproduces it byte for byte."""
    report = build_report(config, experiments_root)
    results_root.mkdir(parents=True, exist_ok=True)
    path = results_root / "metrics.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    (results_root / "summary.txt").write_text(
        render_summary(report), encoding="utf-8", newline="\n"
    )
    return path
