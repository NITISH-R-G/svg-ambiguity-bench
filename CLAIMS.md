# Claims

Every module in this repository exists to support exactly one scientific claim. This
file is the gate: **before building anything, name the claim it strengthens. If the
answer is "none", do not build it.**

The central claim is C3. Everything else exists to make C3 interpretable.

---

## The claim lifecycle

A claim is not mature until it has passed through all five states. Skipping one means
the claim is weaker than it looks.

```
Proposed  ->  Specified  ->  Measured  ->  Stress-tested  ->  Published
(asserted)    (operational  (numbers    (adversarially     (in README
              definition)    on disk)    attacked)          / write-up)
```

**Stress-tested** is the state most often skipped, and it is the one that matters. A
measured claim says "the number came out this way". A stress-tested claim says "we tried
to make it come out the other way and could not". For C1 that meant planting a leak and
requiring the detector to reject it; for C2, planting decoding drift; for C7, feeding
witnesses that cannot agree.

## The claims

| # | Claim | Proposed | Specified | Measured | Stress-tested | Published |
|---|---|---|---|---|---|---|
| **C1** | Corpus is genuinely under-determined | yes | yes | Step 3 | yes - planted leak rejected at p=0.0005 | pending |
| **C2** | Arms are comparable | yes | yes | Step 2 | yes - planted drift caught 3 ways | pending |
| **C3** | **Improvement is information, not format** | yes | yes | - | - | - |
| **C4** | Identification separable from execution | yes | yes | - | - | - |
| **C5** | Abstention measured, not punished | yes | yes | - | - | - |
| **C6** | Every number independently verifiable | yes | yes | Step 3 | partial - regeneration verified, full Tier 1-2 needs Step 14 | pending |
| **C7** | Ground truth correct, not asserted | yes | yes | Step 4 | yes - disagreeing witnesses rejected | pending |
| **C8** | Ground truth matches human judgement | yes | yes | Step 5 | yes - 9.4% of slots refused for definition disagreement | pending |

Nothing is Published until there are results. That column staying empty is the honest
state of the project, not an oversight.

### What each claim asserts

- **C1** - the markup cannot distinguish the candidate elements. Generator invariants:
  identical tag and fill, no positional attributes, fixed-length opaque tokens,
  order-uncorrelated document sequence.
- **C2** - the arms differ in exactly one variable. Shared corpus hash, distinct config
  hash, identical decoding.
- **C3** - the central claim. The `permuted` arm holds context format fixed and destroys
  only the information.
- **C4** - evaluation decomposes into identification / execution / collateral rather than
  one "correct" bit.
- **C5** - `ABSTAINED` is its own outcome class; accuracy reported with and without it.
- **C6** - frozen dataset plus committed raw responses; Tiers 1-2 reproduce with no model
  and no renderer.
- **C7** - two measurement implementations agree. Rank agreement 12/12 SVGs.
- **C8** - *new at Step 5.* Ground truth is not merely self-consistent but matches what a
  reasonable person would say. A sample whose answer depends on which reasonable
  definition you pick is rejected, not shipped.

Measured values for each are in [`EVIDENCE.md`](EVIDENCE.md). Assumptions that turned out
to be wrong are in [`FAILED_ASSUMPTIONS.md`](FAILED_ASSUMPTIONS.md). The rule governing
what may and may not change once results exist is in [`RESULTS.md`](RESULTS.md) - read
it before looking at any model output, not after.

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
