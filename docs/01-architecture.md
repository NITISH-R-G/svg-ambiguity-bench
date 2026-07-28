# Architecture — v1

**Status:** FROZEN 2026-07-28. Rationale in [`adr/`](adr/).

---

## The fairness invariant

> The arms are not separate pipelines. There is **one** pipeline parameterized by a single
> injectable component. Baseline is that component's null implementation.

Every other choice here is subordinate to it. Two separately-authored paths would drift, and
nothing downstream recovers the comparison.

---

## 1. Layers

Four layers, strictly one-directional.

```
A  CORPUS CONSTRUCTION   (stochastic, seeded, run once)
   Generator -> Renderer -> GroundTruthEngine -> InstructionGenerator -> DatasetBuilder
                                 ^                        |
                                 +---- validation --------+
                                            |
                                            v  FROZEN DATASET (content-addressed)

B  EXECUTION             (stochastic only in the model)
   CaseLoader -> ContextProvider -> PromptAssembler -> ModelClient -> ResponseStore
                       ^
                       +-- Null | Permuted | Enhancement | Ceiling  (the ONLY arm difference)

C  MEASUREMENT           (fully deterministic, offline, no model, no renderer)
   EvaluationEngine -> MetricsModule -> ReportingModule

D  VERIFICATION          (cross-cutting)
   Audit: leakage | blindness | determinism | balance
```

**Layer C touches no model and no renderer.** This is the single most important
reproducibility property: a reviewer with neither can regenerate every published number.
It is enforced by a test, not by convention (`tests/unit/test_scaffold.py`).

---

## 2. Components

### Generator
Places K ambiguity-set members and D distractors. Emits a *resolved* SVG with real path data
plus its generation intent. **All positional information lives inside `d`** — no
`transform`, no `x`/`cx` on ambiguity members. Intent is never ground truth; it is a
third witness.

### Renderer — two services, deliberately different implementations

| | GeometryEngine (analytic) | Rasterizer (visual) |
|---|---|---|
| Backend | `svgelements`, pure Python | `resvg`, Rust |
| Produces | exact bbox, centroid, analytic area | pixel coverage mask at fixed DPI |
| Used for | cross-validation, overlap tests | **canonical area** |

Independence is the point. Two views of one code path would be consistency, not validation.

### GroundTruthEngine
Normalizes geometry; computes centroid, bbox, canonical area, dense area rank, quadrant;
evaluates the Predicate Registry producing winner, runner-up, and **separation margin**;
performs tri-source validation (intent ≈ analytic ≈ raster); enforces separability and
regenerates on failure, logging every rejection.

### InstructionGenerator
Draws predicate × operation × phrasing; resolves the target **by code** against ground
truth; asserts uniqueness against the full element set; runs the leakage lint; balances the
design across family, operation, rank, quadrant, and K.

### DatasetBuilder — the freeze point
Redacts geometry; verifies redaction is structure-preserving (redacted ≡ resolved under a
geometry-masked canonical comparison); assembles cases; computes content hashes into one
`dataset_hash`; writes the manifest. Nothing regenerates after this. Arms load by hash and
refuse on mismatch.

### ContextProvider — the arm seam

```
ContextProvider :: (model_visible_svg, svg_id) -> ContextBlock
```

**The instruction is not a parameter.** Instruction-blindness is enforced by the type, not
by discipline: a contributor cannot leak the instruction because it is unreachable from
inside a provider. Context is cached per SVG, which is simultaneously an efficiency win and
a structural proof of blindness.

### Runner
Prompt assembly, model client, append-only response store. One template with one context
slot; baseline fills it with nothing.

### EvaluationEngine
Parse → align → diff → classify. Arm-blind by construction: it reads the response store
keyed by case and run, and is never told which arm produced a row.

**Alignment tiers**, recorded per case so weak-tier reliance is visible:
1. geometry token (unique, preserved by contract) — primary
2. `id` attribute
3. document position + tag + sibling context
4. otherwise → `MALFORMED`

The opaque geometry token doubles as the identity anchor. That falls out of the redaction
design for free and survives a model that rewrites ids.

### MetricsModule
Cell rates; hedging distribution; per-case 1/K reference; **SVG-level cluster resampling**
(instructions sharing an SVG share a layout and are not independent); paired cluster-level
permutation tests; per-predicate breakdowns.

### ReportingModule
Tables and figures only. No analysis logic — a number not present in the metrics output must
not be computable here.

---

## 3. Predicate Registry

Every visual predicate is a first-class object with an operational definition, a margin
definition, and a human-agreement requirement. Adding a predicate touches no other module.

| Family | Predicate | Definition | Margin |
|---|---|---|---|
| Spatial | `top_left` etc. | argmin centroid distance to that corner **∧** centroid in that quadrant | relative gap to runner-up |
| Spatial | `leftmost`/`rightmost` | argmin/argmax centroid x | normalized x-gap |
| Spatial | `topmost`/`bottommost` | argmin/argmax centroid y | normalized y-gap |
| Ordinal | `largest`/`smallest` | rank 1 / rank K by canonical area | adjacent-rank relative gap |
| Ordinal | `second_largest`/`third_largest` | rank 2 / rank 3 | adjacent-rank relative gap |

The quadrant conjunct on corner predicates exists because pure nearest-corner argmin can
crown a shape near the middle, which no human would call "the top-left one".

---

## 4. Geometry redaction

```
d="{{GEOM_7f3a91c2}}"     <- fixed length, order-uncorrelated, unique per element
```

- Explicit self-describing token, not mangled coordinates: plausible-but-wrong path data
  invites repair attempts and converts an identification experiment into a syntax one.
- **Fixed length is mandatory** — variable length would leak path complexity, which
  correlates with size.
- The token↔geometry map lives in the sidecar, never in a model-visible file.

Accepted consequence: model-visible SVGs do not render. That is intended. If they rendered,
position would be recoverable.

---

## 5. Repository layout

```
docs/            specs, experiment design, ADRs, results
  adr/           one record per non-obvious decision
configs/         base + per-experiment configs; models/
src/svgbench/    config generation geometry groundtruth instructions dataset
                 context runner evaluation metrics reporting audit
tests/           unit/ property/ integration/ audit/ fixtures/
scripts/         thin CLI wrappers, no logic
data/generated/  disposable working area (gitignored)
data/frozen/     IMMUTABLE, committed - the scientific record
experiments/     manifests + raw responses + evaluations, committed
results/         metrics and figures, committed
assets/          static, non-generated
```

`data/frozen/`, `experiments/`, and `results/` are committed on purpose: a reviewer must be
able to see the exact bytes the model saw and re-score them independently.

---

## 6. Experiment lifecycle

Each stage has a gate. No stage proceeds if its gate fails.

| # | Stage | Gate |
|---|---|---|
| 1 | Generate dataset | tri-source validation, ambiguity invariants, separability |
| 2 | Generate instructions | balance, zero lint violations, unique resolution |
| 3 | **Freeze** | independent regeneration reproduces `dataset_hash` (CI job) |
| 4 | Run baseline | coverage complete; prompt-length headroom confirmed |
| 5 | Evaluate | every response classified; fixture suite green |
| 6 | Run other arms | blindness, leakage, prompt-diff, fact-accuracy checks |
| 7 | Evaluate | same engine, same code, no flags |
| 8 | Report | re-running reproduces `metrics.json` byte-identically |
| 9 | Publish | README table generated, not hand-typed; LIMITATIONS revised |

**Seed derivation is hierarchical and positional**: `seed → svg_seed[i] → shape_seed[i][j]`,
derived from stable indices rather than a running counter. Regenerating SVG #17 alone is
byte-identical, and a change in early rejection does not cascade and reshuffle the corpus.

**Pre-registration boundary:** stages 1–3 and the scoring rules are committed and tagged
before stage 4 runs. See [`../DESIGN_FREEZE.md`](../DESIGN_FREEZE.md).

---

## 7. Reproduction tiers

| Tier | Verifies | Needs | Cost |
|---|---|---|---|
| 1 | every published number | Python | ~1 min |
| 2 | the whole scoring chain | Python | ~2 min |
| 3 | corpus determinism | + renderer | ~10 min |
| 4 | model results | + local model | hours |

Tier 4 does not reproduce bit-for-bit; small local models vary with backend build and
threading even at temperature 0. What reproduces is the conclusion, within the reported
interval. The report says so rather than implying exactness the design cannot deliver.
