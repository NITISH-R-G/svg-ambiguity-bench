"""Metrics and inference over evaluation rows.

Resampling and testing are at the **SVG level**, not the case level. Six instructions
share one SVG, one layout and one ambiguity set; treating them as six independent
observations would understate variance and manufacture precision that does not exist
(ADR-0007). The effective sample size is ~30 clusters, not 180 cases.

Hypothesis tests are **paired cluster-level permutation** tests rather than
normal-theory intervals. Bootstrap coverage is poor at ~30 clusters and worse near the
floor proportions the baseline arm occupies, and pairing is valid because every arm sees
byte-identical cases.

Touches no model and no renderer, so every number here is re-derivable by a reviewer
with neither.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

_FROZEN = ConfigDict(extra="forbid", frozen=True)


class Interval(BaseModel):
    """A point estimate with a cluster-bootstrap interval."""

    model_config = _FROZEN

    point: float
    low: float
    high: float

    def __str__(self) -> str:
        return f"{self.point:.4f} [{self.low:.4f}, {self.high:.4f}]"


class ArmMetrics(BaseModel):
    """Everything reported for one arm."""

    model_config = _FROZEN

    arm: str
    n_cases: int
    n_clusters: int

    identification: Interval
    identification_given_wellformed: Interval
    strict: Interval
    execution_given_identified: float
    collateral_rate: Interval
    mean_elements_modified: float
    random_reference: float

    outcomes: dict[str, int]
    by_family: dict[str, float]
    by_predicate: dict[str, float]


def load_rows(experiments_root: Path) -> dict[str, list[dict[str, Any]]]:
    """Evaluation rows per arm. Reads committed files only."""
    arms: dict[str, list[dict[str, Any]]] = {}
    for directory in sorted(experiments_root.iterdir()):
        path = directory / "evaluations.jsonl"
        if not path.exists():
            continue
        name = directory.name.split("_")[0]
        arms[name] = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
        ]
    return arms


def _cluster(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["svg_id"]].append(row)
    return dict(grouped)


def _rate(rows: list[dict[str, Any]], field: str) -> float:
    return sum(bool(r[field]) for r in rows) / len(rows) if rows else 0.0


def cluster_bootstrap(
    rows: list[dict[str, Any]],
    field: str,
    iterations: int,
    seed: int,
    ci_level: float,
) -> Interval:
    """Resample SVGs with replacement, not cases.

    Cases within an SVG move together, which is what preserves the correlation the
    clustering exists to respect.

    Each cluster is reduced once to (successes, size) before resampling. Rebuilding the
    row list on every iteration made this quadratic enough to be unusable at 10,000
    iterations; the statistic is identical either way.
    """
    if not rows:
        return Interval(point=0.0, low=0.0, high=0.0)

    summarised = [
        (sum(bool(r[field]) for r in group), len(group)) for group in _cluster(rows).values()
    ]
    point = _rate(rows, field)

    rng = random.Random(seed)
    n_clusters = len(summarised)
    draws: list[float] = []
    for _ in range(iterations):
        hits = 0
        total = 0
        for _ in range(n_clusters):
            h, t = summarised[rng.randrange(n_clusters)]
            hits += h
            total += t
        draws.append(hits / total if total else 0.0)

    draws.sort()
    tail = (1.0 - ci_level) / 2.0
    return Interval(
        point=point,
        low=draws[int(tail * (len(draws) - 1))],
        high=draws[int((1.0 - tail) * (len(draws) - 1))],
    )


def paired_permutation(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
    field: str,
    iterations: int,
    seed: int,
) -> dict[str, float]:
    """Paired cluster-level permutation test on the per-SVG difference.

    Under the sharp null that the arm label is irrelevant, swapping the two arms' results
    *within an SVG* leaves the distribution unchanged. Flipping whole clusters - never
    individual cases - is what respects the clustering.
    """
    by_case_a = {r["case_id"]: r for r in rows_a}
    by_case_b = {r["case_id"]: r for r in rows_b}
    shared = sorted(set(by_case_a) & set(by_case_b))

    per_svg: dict[str, list[float]] = defaultdict(list)
    for case_id in shared:
        a, b = by_case_a[case_id], by_case_b[case_id]
        per_svg[a["svg_id"]].append(float(bool(a[field])) - float(bool(b[field])))

    deltas = {svg: sum(values) / len(values) for svg, values in per_svg.items()}
    observed = sum(deltas.values()) / len(deltas)

    rng = random.Random(seed)
    values = list(deltas.values())
    extreme = 0
    for _ in range(iterations):
        flipped = [v if rng.random() < 0.5 else -v for v in values]
        if abs(sum(flipped) / len(flipped)) >= abs(observed):
            extreme += 1

    return {
        "observed_difference": observed,
        "p_value": (extreme + 1) / (iterations + 1),
        "n_clusters": float(len(deltas)),
        "n_paired_cases": float(len(shared)),
    }


def arm_metrics(
    arm: str,
    rows: list[dict[str, Any]],
    bootstrap_iterations: int,
    bootstrap_seed: int,
    ci_level: float,
) -> ArmMetrics:
    wellformed = [r for r in rows if r["outcome"] != "MALFORMED"]
    identified = [r for r in rows if r["target_edited"]]

    outcomes: dict[str, int] = defaultdict(int)
    for row in rows:
        outcomes[row["outcome"]] += 1

    by_family: dict[str, float] = {}
    for family in sorted({r["family"] for r in rows}):
        subset = [r for r in rows if r["family"] == family]
        by_family[family] = _rate(subset, "target_edited")

    by_predicate: dict[str, float] = {}
    for predicate in sorted({r["predicate"] for r in rows}):
        subset = [r for r in rows if r["predicate"] == predicate]
        by_predicate[predicate] = _rate(subset, "target_edited")

    return ArmMetrics(
        arm=arm,
        n_cases=len(rows),
        n_clusters=len(_cluster(rows)),
        identification=cluster_bootstrap(
            rows, "target_edited", bootstrap_iterations, bootstrap_seed, ci_level
        ),
        identification_given_wellformed=cluster_bootstrap(
            wellformed, "target_edited", bootstrap_iterations, bootstrap_seed, ci_level
        ),
        strict=cluster_bootstrap(
            [{**r, "_strict": r["outcome"] == "CORRECT_STRICT"} for r in rows],
            "_strict",
            bootstrap_iterations,
            bootstrap_seed,
            ci_level,
        ),
        execution_given_identified=(
            sum(r["target_edit_correct"] for r in identified) / len(identified)
            if identified
            else 0.0
        ),
        collateral_rate=cluster_bootstrap(
            [{**r, "_coll": bool(r["collateral_element_ids"])} for r in rows],
            "_coll",
            bootstrap_iterations,
            bootstrap_seed,
            ci_level,
        ),
        mean_elements_modified=sum(len(r["predicted_target_ids"]) for r in rows) / len(rows),
        random_reference=sum(1.0 / r["k"] for r in rows) / len(rows),
        outcomes=dict(outcomes),
        by_family=by_family,
        by_predicate=by_predicate,
    )


def minimum_detectable_effect(
    rows: list[dict[str, Any]],
    iterations: int,
    seed: int,
) -> float:
    """The smallest per-SVG difference this design could have detected at p < 0.05.

    Reported so a null result is interpretable rather than merely underpowered. Derived
    from the permutation null's own spread, which is the distribution the test actually
    compares against.
    """
    clusters = _cluster(rows)
    rng = random.Random(seed)
    n = len(clusters)
    if n == 0:
        return 0.0

    # Per-SVG variability of the outcome, used as the scale of a plausible difference.
    per_svg = [_rate(v, "target_edited") for v in clusters.values()]
    spread = (sum((x - sum(per_svg) / n) ** 2 for x in per_svg) / max(n - 1, 1)) ** 0.5

    draws = []
    for _ in range(iterations):
        flipped = [rng.choice([-1.0, 1.0]) * spread for _ in range(n)]
        draws.append(abs(sum(flipped) / n))
    draws.sort()
    return float(draws[int(0.95 * (len(draws) - 1))])
