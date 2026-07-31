"""A format-matched control outside SVG, in about thirty lines.

Run it:

    python examples/rag_style_control.py

No model, no network, no benchmark. `fmtcontrol` depends on nothing outside the standard
library, so this file runs against a copy of `src/fmtcontrol/` on its own.

The scenario is retrieval-augmented QA with structured evidence: each retrieved document
contributes a fixed-schema row - source, published year, relevance score - and the
question is whether an improvement comes from *those facts* or merely from *having a
table*. That is the same confound the SVG study measures, in a domain sharing none of its
code.

Note which representation is used, and why. The applicability condition in METHOD.md
requires a representation that admits a value permutation while preserving its
presentation-level invariants. A fixed-width metadata table satisfies it. Raw passage
*text* would not: passages differ in length, so permuting them between queries changes the
token count and breaks the format match on the property that matters most. That boundary
is a property of the representation, not of the domain.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fmtcontrol import check_control, permute

# entity -> (source, year, relevance). Fixed schema, bounded width.
EVIDENCE: dict[str, tuple[str, int, float]] = {
    "doc_1": ("annual-report-2023", 2023, 0.91),
    "doc_2": ("press-release-q2", 2024, 0.77),
    "doc_3": ("sec-filing-10k", 2022, 0.64),
    "doc_4": ("analyst-note", 2024, 0.58),
}

QUERY_ID = "q_0447"
PERMUTATION_SEED = 991  # independent of whatever seed produced the retrieval


def render(evidence: dict[str, tuple[str, int, float]]) -> str:
    """The renderer. Used for BOTH arms - that is what holds format fixed."""
    lines = ["Retrieved evidence:", "  id       source                 year   relevance"]
    for doc_id, (source, year, relevance) in evidence.items():
        lines.append(f"  {doc_id:<8} {source:<22} {year:<6} {relevance:.2f}")
    return "\n".join(lines)


def main() -> int:
    control = permute(EVIDENCE, key=QUERY_ID, seed=PERMUTATION_SEED)

    enhanced_text = render(EVIDENCE)
    permuted_text = render(control)

    print("=" * 72)
    print("ENHANCED  — real evidence (the treatment arm)")
    print("=" * 72)
    print(enhanced_text)
    print()
    print("=" * 72)
    print("PERMUTED  — same table, values reassigned (the control arm)")
    print("=" * 72)
    print(permuted_text)
    print()

    report = check_control(EVIDENCE, control, enhanced_text, permuted_text)
    print("=" * 72)
    print(f"VALIDATION  — {report}")
    print("=" * 72)
    for name in report.checks_run:
        print(f"  pass   {name}")
    print(f"\n  token count difference: {report.token_delta}")

    print(
        "\nThe two arms are indistinguishable in shape and identical in the multiset of\n"
        "values they contain. Only the document->fact assignment differs. So:\n"
        "\n"
        "    enhanced - baseline   total effect of adding the table\n"
        "    permuted - baseline   what the FORMAT alone bought\n"
        "    enhanced - permuted   what the INFORMATION bought   <- the actual claim\n"
        "\n"
        "Without the third arm, the first comparison is all you have, and it does not\n"
        "license the claim people usually make from it."
    )

    if not report.ok:  # pragma: no cover - the example is meant to pass
        print("\nUNEXPECTED: control invalid", report.failures, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
