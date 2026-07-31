"""POST-HOC characterisation of the `MALFORMED` outcome class. Changes no scoring.

The frozen scorer classifies any response from which no well-formed SVG document can be
extracted as `MALFORMED`, unless the frozen abstention patterns match first. That rule is
correct as written and is not modified here. `abstention_rule_version` stays at 1.0 and
every published figure continues to come from it.

What this script does is *describe* what is inside that class. Study V3 produced a
`MALFORMED` rate of 0.65 on one condition of `qwen2.5-coder:7b`, which trips a
pre-registered falsifier. Whether that means "the model emitted garbage" or "the model
declined in prose the frozen patterns do not match" changes what the exclusion means,
and the two are not distinguishable from the rate alone.

This is exploratory. It is reported alongside the frozen analysis, never in place of it.

Usage:
    python scripts/characterise_malformed.py
    python scripts/characterise_malformed.py --samples 3
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from svgbench.evaluation.extract import detects_abstention, extract_svg, parse_elements

REPO_ROOT = Path(__file__).resolve().parents[1]

# Broader than the frozen abstention patterns ON PURPOSE. The frozen set is deliberately
# narrow so that ordinary commentary ("I changed the second path's fill") cannot be
# mistaken for a refusal - a property worth keeping. This wider set exists only to ask
# how much sits in the gap between the two, and must never be used for scoring.
_REFUSAL_WIDE = re.compile(
    r"""
    \b(?:cannot|can't|cannot\ be|unable\ to|not\ possible\ to|no\ way\ to)\b
    | \bdoes\ not\ (?:contain|provide|specify|include|indicate)\b
    | \bdoesn't\ (?:contain|provide|specify|include|indicate)\b
    | \bno\ (?:explicit|positional|size|sizing|geometric)\b
    | \binsufficient\b | \bnot\ enough\b
    | \bwithout\ (?:the\ )?(?:actual|real|explicit)\b
    | \bI\ would\ need\b | \bplease\ (?:provide|clarify|specify)\b
    | \bambiguous\b | \bunclear\ which\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

CATEGORIES = (
    "transport_error",
    "truncated",
    "prose_refusal",
    "prose_other",
    "svg_unparseable",
    "svg_no_elements",
    "unclassified",
)


def categorise(response: str, truncated: bool, error: str | None) -> str:
    """Assign one disjoint category. Order is significant.

    Transport and truncation come first because they are facts about the call rather
    than about the text, and a truncated refusal is still a truncation.
    """
    if error:
        return "transport_error"
    if truncated:
        return "truncated"

    svg = extract_svg(response)
    if svg is None:
        # No document at all. Either the model talked instead of answering, or it
        # produced something unrelated.
        return "prose_refusal" if _REFUSAL_WIDE.search(response) else "prose_other"

    elements = parse_elements(svg)
    if elements is None:
        return "svg_unparseable"
    if not elements:
        return "svg_no_elements"
    return "unclassified"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=0, help="print N example texts per category")
    args = parser.parse_args()

    experiments = sorted(
        p for p in (REPO_ROOT / "experiments").iterdir() if (p / "evaluations.jsonl").exists()
    )

    grand: Counter[str] = Counter()
    samples: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    # How many frozen-MALFORMED responses WOULD the frozen abstention rule have caught if
    # it had been consulted? Zero by construction - abstention is checked first - so a
    # non-zero count here would mean the pipeline disagrees with itself.
    frozen_would_match = 0

    print(f"{'experiment':44s} {'MALF':>5s}  " + "  ".join(f"{c[:9]:>9s}" for c in CATEGORIES))
    print("-" * 44 + "  " + "-" * 5 + "  " + "  ".join("-" * 9 for _ in CATEGORIES))

    for directory in experiments:
        responses = {
            json.loads(line)["case_id"]: json.loads(line)
            for line in (directory / "responses.jsonl").open(encoding="utf-8")
            if line.strip()
        }
        rows = [
            json.loads(line)
            for line in (directory / "evaluations.jsonl").open(encoding="utf-8")
            if line.strip()
        ]
        malformed = [r for r in rows if r["outcome"] == "MALFORMED"]
        if not malformed:
            continue

        counts: Counter[str] = Counter()
        for row in malformed:
            record = responses[row["case_id"]]
            category = categorise(record["response"], record["truncated"], record.get("error"))
            counts[category] += 1
            grand[category] += 1
            if detects_abstention(record["response"]):
                frozen_would_match += 1
            if len(samples[category]) < args.samples:
                samples[category].append(f"[{directory.name}] {record['response'][:300]}")

        print(
            f"{directory.name:44s} {len(malformed):5d}  "
            + "  ".join(f"{counts.get(c, 0):9d}" for c in CATEGORIES)
        )

    total = sum(grand.values())
    print("-" * 44 + "  " + "-" * 5 + "  " + "  ".join("-" * 9 for _ in CATEGORIES))
    print(f"{'TOTAL':44s} {total:5d}  " + "  ".join(f"{grand.get(c, 0):9d}" for c in CATEGORIES))

    print()
    print(f"frozen abstention rule would have matched: {frozen_would_match}")
    print("  (expected 0 - abstention is checked before extraction, so any non-zero")
    print("   value would mean the scoring pipeline disagrees with itself)")

    if total:
        refusal = grand.get("prose_refusal", 0)
        print()
        print(f"prose refusals as a share of MALFORMED: {refusal}/{total} = {refusal / total:.3f}")

    for category, texts in samples.items():
        if not texts:
            continue
        print(f"\n=== {category} ===")
        for text in texts:
            print(f"  {text.replace(chr(10), ' ')[:280]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
