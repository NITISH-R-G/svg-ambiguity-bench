# PRD — svg-ambiguity-bench

**Version:** 1.0 · **Status:** FROZEN 2026-07-28 · See [`../DESIGN_FREEZE.md`](../DESIGN_FREEZE.md)

Rationale for individual decisions lives in [`adr/`](adr/). This document states *what* is
required, not *why* it was chosen.

---

## 1. Problem

SVG markup encodes how to draw, not what is drawn where. When several elements share a tag
and a fill and their path geometry is opaque, the markup contains no feature distinguishing
them. Natural-language edit instructions refer to visual appearance. A model editing such
markup is performing an underdetermined task.

## 2. Goals

- **G1** A reproducible corpus with a controlled, known-by-construction ambiguity property.
- **G2** Edit instructions in two independent families, each resolving to exactly one element
  under a machine-checkable ground truth.
- **G3** Measure a small local model's baseline performance.
- **G4** An original method supplying the missing visual semantics, under a strict
  no-leakage constraint.
- **G5** Measure identical cases with that method, reporting arm × family separately.
- **G6** A public repository whose numbers a third party can regenerate.

**Non-goal:** demonstrating that the enhancement wins. A cleanly measured null result
satisfies every goal above.

## 3. Functional Requirements

### FR-1 Generator
- **1.1** 20–30 SVGs, deterministic from one integer seed; rerun is byte-identical.
- **1.2** Each contains an ambiguity set of K ∈ [4,7] elements with identical tag and fill.
- **1.3** Ambiguity-set geometry is `<path>` with `d` replaced by an opaque token.
- **1.4** Distractor elements (different tag or fill) are present.
- **1.5** Document order is shuffled independently of every ground-truth property, verified
  by automated correlation check.
- **1.6** Element ids are opaque and order-uncorrelated.
- **1.7** A ground-truth sidecar per SVG, never shipped to the model in any arm.
- **1.8** **No positional attributes** (`transform`, `x`, `y`, `cx`, `cy`, …) on
  ambiguity-set members. All position lives inside `d`.
- **1.9** Geometry tokens are **fixed length**, so byte count cannot leak path complexity.

### FR-2 Separability
- **2.1** Spatial: the intended target beats the runner-up by a configured margin.
- **2.2** Ordinal: adjacent area ranks differ by a configured relative margin.
- **2.3** Ambiguity-set elements do not overlap beyond a threshold.
- **2.4** A case failing any guarantee is regenerated, never silently shipped; every
  rejection is logged with its reason and the log is published.

### FR-3 Instructions
- **3.1** Two families: **Spatial** and **Ordinal Size**.
- **3.2** Each instruction resolves to exactly one element; the resolver is code.
- **3.3** Operations are a closed, structurally checkable set: recolor fill, add stroke,
  delete, rotate.
- **3.4** Phrasing encodes no answer: no ids, counts, or ordering hints. Enforced by lint.
- **3.5** Balanced across family, operation, target rank, target quadrant, and K.
- **3.6** ≥2 surface phrasings per predicate.
- **3.7** Uniqueness is asserted against the **full element set**, not only the ambiguity
  set — a distractor must not outrank the intended target on the instruction's predicate.

### FR-4 Execution
- **4.1** One runner, one prompt template, shared by every arm.
- **4.2** Arms differ only in the injected context block.
- **4.3** The model returns a full edited SVG document.
- **4.4** Fixed, recorded decoding parameters.
- **4.5** Every raw request and response persisted.

### FR-5 Context providers (arms)

| Arm | Context | Role |
|---|---|---|
| `baseline` | empty | manipulation check |
| `permuted` | correct format, values shuffled between elements | isolates format from information |
| `enhanced` | derived visual facts | the benchmark |
| `ceiling` | facts + predicate labels | upper bound, excluded from headline |
| `legible` | empty, but corpus has real `d` | separates redaction artifact from ambiguity |
| `facts_only` | facts, SVG withheld | tests whether markup contributes |

- **5.1** Provider signature excludes the instruction. Blindness is enforced by type.
- **5.2** Context is computed once per SVG and reused across its instructions.
- **5.3** No ground-truth id, rank label, or instruction-predicate phrase may appear in
  `enhanced` context. (`ceiling` deliberately violates this and is excluded from headline.)
- **5.4** The enhancement's own fact-accuracy is measured against ground truth and reported
  separately from model accuracy.

### FR-6 Evaluation
- **6.1** Malformed output is a scored outcome, never a discarded case. Denominators are
  fixed at freeze time.
- **6.2** Structural diff on a canonical view: normalized whitespace, sorted attributes,
  normalized color and numeric notation.
- **6.3** Outcome classes: `CORRECT_STRICT`, `CORRECT_LOOSE`, `WRONG_TARGET`, `ABSTAINED`,
  `NO_EDIT`, `MALFORMED`.
- **6.4** Record elements-modified count per case.
- **6.5** Record alignment tier per case.
- **6.6** Scoring is arm-blind: the engine is not told which arm produced a response.

### FR-7 Metrics
- **7.1** **Primary: identification accuracy** — did the model act on the intended element.
- **7.2** Secondary: execution accuracy given correct identification; collateral rate;
  strict accuracy; loose accuracy.
- **7.3** Abstention rate reported separately; accuracy reported both including and
  excluding abstentions.
- **7.4** Malformed and truncation rates per arm; identification reported both
  unconditionally and conditional on well-formed output.
- **7.5** Random-selection reference computed per case as 1/K, then averaged.
- **7.6** Selection-position distribution, to test the 1/K null rather than assume it.
- **7.7** Reported **per predicate**, not only per family.
- **7.8** Uncertainty via SVG-level cluster resampling; paired cluster-level permutation
  test across arms.
- **7.9** Minimum detectable effect reported before results.

### FR-8 Repository
Generator, benchmark, evaluation, enhancement, scripts, README, LIMITATIONS, pinned
dependencies, recorded environment. One command reproduces the corpus; one reproduces the
numbers from stored responses with no model.

## 4. Non-Functional Requirements

- **NFR-1** Reproducibility: every stochastic element seeded; responses cached so analysis
  runs offline.
- **NFR-2** Fairness: arms differ in exactly one variable, enforced by shared code paths.
- **NFR-3** Hardware: CPU-only.
- **NFR-4** Auditability: every number traceable to a raw response on disk.
- **NFR-5** Honesty: LIMITATIONS.md expanded, never softened, after results.
- **NFR-6** Modularity: model, context provider, and predicates swappable behind interfaces.
- **NFR-7** Test-first: scoring, resolvers, and leakage checks unit-tested before any model
  is invoked.

## 5. Success Metrics

**Primary:** identification accuracy per arm × predicate, with intervals.

**Project success** — independent of the direction of the result:

- **S1** Corpus provably satisfies its ambiguity and separability guarantees.
- **S2** Baseline is near the 1/K reference **and** its error distribution is consistent
  with selection rather than a fixed positional policy.
- **S3** No-leakage and blindness checks pass.
- **S4** All arms ran on byte-identical cases with identical settings.
- **S5** Every cell reported with uncertainty, whatever the values.
- **S6** Limitations documented.

**Pre-registered hypotheses**

- **H1** Baseline identification accuracy ≈ 1/K in both families.
- **H2** Enhanced > baseline in at least one family.
- **H3** Enhanced > permuted — the gain is information, not format.
- **H4** The two families improve by different margins.

Each may fail. Failure is reported, not re-specified around. **H3 is the load-bearing
hypothesis**: without it, H2 is uninterpretable.

## 6. Assumptions

- **A1** The model emits syntactically valid SVG often enough that malformed output is a
  minority failure mode. Checked by smoke test before committing to a full run.
- **A2** Rendered geometry is a faithful ground truth. Checked by two independent engines
  plus a human agreement sample.
- **A3** Human-obvious visual targets exist for every instruction.
- **A4** Spatial and ordinal families are independent. **Checked**, not assumed — the
  area-ratio constraint can induce a position/area correlation.
- **A5** Cell sizes support a meaningful interval. Confirmed by reporting the MDE.
- **A6** The model has no memorized exposure to this corpus.

## 7. Acceptance Criteria

1. `generate` produces 20–30 SVGs from a seed; rerun is byte-identical.
2. Every SVG has ≥4 same-tag/same-fill elements with opaque, fixed-length `d` tokens and no
   positional attributes.
3. Document order shows no correlation with position or area.
4. Every instruction resolves to exactly one element against the full element set.
5. Both families present and balanced.
6. Leakage lint passes.
7. All arms run; raw responses persisted.
8. Blindness check passes: context byte-identical across instructions for one SVG.
9. Arms ran on byte-identical cases with identical settings.
10. Scoring unit tests pass on fixtures covering all six outcome classes.
11. All cells reported with n, primary and secondary metrics, failure breakdown, intervals,
    and the 1/K reference.
12. Enhancement fact-accuracy reported separately.
13. README headline table and reproduce commands present; LIMITATIONS.md written.
14. Analysis re-runs from cached responses with no model access.
15. Public repo with incremental commits.

## 8. Out of Scope

Multi-step or conversational editing · rasterized-image-only inputs · frontier models as the
system under test · fine-tuning · real-world SVG corpora · prompt optimization for either
arm · a UI · human evaluation studies beyond the agreement sample · claims of generalization
beyond this synthetic corpus.
