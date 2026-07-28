# Claims

Every module in this repository exists to support exactly one scientific claim. This
file is the gate: **before building anything, name the claim it strengthens. If the
answer is "none", do not build it.**

The central claim is C3. Everything else exists to make C3 interpretable.

---

## The claims

| # | Claim | Evidence | Status |
|---|---|---|---|
| **C1** | The corpus is genuinely under-determined - the markup cannot distinguish the candidate elements | Generator invariants: identical tag + fill, no positional attributes, fixed-length opaque tokens, order-uncorrelated document sequence. Enforced by audit tests on the shipped corpus, and the leak detector is itself verified against a planted leak. | DONE Step 3 |
| **C2** | The arms are comparable - they differ in exactly one variable | Shared `corpus_config_hash` across arms; distinct `config_hash` per arm; arm-fairness audit verified to fail on planted drift | DONE Step 2 |
| **C3** | **Any improvement from added context is information, not format** | The `permuted` arm: identical context format, values shuffled between elements. Pre-registered primary comparison is `enhanced` vs `permuted`. | Step 12-13 |
| **C4** | Identification is separable from execution | Evaluation decomposes into identification / execution / collateral rather than one "correct" bit | Step 9 |
| **C5** | Abstention is measured, not punished | `ABSTAINED` is its own outcome class; accuracy reported with and without it | Step 9 |
| **C6** | Every reported number is independently verifiable | Frozen dataset + committed raw responses + manifests; Tiers 1-2 reproduce with no model and no renderer | Step 8, 14 |
| **C7** | Ground truth is correct, not merely asserted | Two measurement implementations must agree - Rust raster vs Python analytic. Rank agreement 12/12 SVGs; area disagreement max 0.0014 against a 0.02 bound. | DONE Step 4 |

Measured values for each are in [`EVIDENCE.md`](EVIDENCE.md).

---

## How to use this file

When proposing a feature, answer in one line: *which claim does this strengthen, and how?*

Worked examples from decisions already made:

| Proposal | Claim | Verdict |
|---|---|---|
| `permuted` arm | C3 | **Build.** Without it C3 is unsupported and the headline is uninterpretable. |
| Two hashes (corpus vs config) | C2 | **Build.** One hash cannot express "same cases, different run". |
| `legible` arm (`redact_geometry: false`) | C1 | **Build.** One boolean; isolates ambiguity from out-of-distribution markup. |
| `ceiling` arm | C4 | **Build.** Separates residual reasoning failure from information failure. |
| Second measurement engine | C7 | **Build.** One engine is an assertion; two disagreeing engines are a finding. |
| Config plugin architecture | none | **Reject.** Extensibility is not a claim. |
| `facts_only` arm | weakly C3 | **Reject for v1.** Backlogged; `permuted` already carries C3. |
| VLM / rendered-image arm | none of C1-C7 | **Reject for v1.** Interesting; different paper. Backlogged. |
| More instruction families | none | **Reject.** Raises case count without raising cluster count (ADR-0007). |

---

## What would falsify each claim

Stated in advance, so a failure is a finding rather than an embarrassment.

- **C1** - baseline accuracy substantially above the per-case `1/K` reference, *or* a
  non-uniform selection-position distribution. Either implies leakage, and the result
  would be reported as invalid rather than as a finding.
- **C2** - the arm-fairness audit fails.
- **C3** - `permuted` approximately equals `enhanced`. This is a live possibility and the
  reason the control exists. It would be reported as the headline: the gain is format,
  not information.
- **C4** - identification and execution accuracy move together across all arms and
  predicates, suggesting the decomposition captures nothing real.
- **C5** - near-zero abstention in every arm, making the class vacuous for this model.
- **C6** - Tier-1 or Tier-2 reproduction does not regenerate the committed numbers.
- **C7** - the two measurement engines disagree beyond tolerance, or disagree on the
  *ranking* of any ambiguity set.

---

## Claims this repository does NOT make

Recorded here because the fastest way to lose a reviewer is to overclaim.

- That language models in general cannot do this. One small model, one synthetic corpus.
- That this reflects real-world SVG editing. Opaque geometry tokens do not occur in the
  wild; `legible` narrows this gap without closing it.
- That the enhancement is a good engineering solution. A deterministic solver scores
  100%. The benchmark measures in-context reference resolution, not whether an LLM is
  the right tool.
- That the enhancement generalizes beyond the predicates it was designed against. It is
  blind to the *instruction* (enforced by type), not to the *benchmark*.
- That generator intent, analytic geometry and raster coverage are three *independent*
  witnesses. Intent and analytic share the shoelace formula and differ only in where the
  vertices came from, so that pair is a serialization check. The independent witness is
  the rasterizer.
