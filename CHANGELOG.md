# Changelog

Sprint-by-sprint increments. Amendments to frozen design documents are recorded here as
required by [`DESIGN_FREEZE.md`](DESIGN_FREEZE.md).

## [Unreleased]

### RESULTS.md - the pre-registration commitment device - 2026-07-28

Not a pipeline step. A rule, written now, before any model has been run, addressing a
different failure mode than the rest of the pre-registration machinery.

`DESIGN_FREEZE.md`'s pre-registration boundary is about the *design* staying fixed.
`RESULTS.md` is about a specific future temptation: finding a plausible-sounding reason
to adjust a threshold or a scoring rule after seeing a disappointing number, months from
now, having forgotten the exact reasoning that set it originally.

The bright line: nothing discovered after the `pre-registration` tag may change the
dataset, scoring, predicates, leakage checks, or evaluation rules - except a bug
demonstrably affecting every arm identically. Everything else becomes Discussion, not a
patch. The operational test for a legitimate post-tag fix: **would it have been made
identically had the arms come out the other way around?**

Also states, as an explicit decision procedure rather than facts scattered across
`CLAIMS.md`'s per-claim falsification criteria, the three comparisons the whole
repository exists to make interpretable, in the order they get read:

1. `baseline ~= 1/K` - the precondition (C1). If baseline sits well above the floor,
   stop and find the leak before interpreting anything else.
2. `enhanced > baseline` - necessary, not sufficient. An uninformative enumerated list
   could pass this too, which is the confound ADR-0009 exists to rule out.
3. `enhanced > permuted` - the actual claim (C3). If this fails to hold, that is not a
   failed experiment: it is the finding the `permuted` control was built to make
   detectable, and it gets reported as the headline rather than buried.

Cross-linked from `README.md`, `CLAIMS.md` and `DESIGN_FREEZE.md`, so it is reachable
from wherever a reader would need it.

### Sprint 2, Step 5 - Ground-truth engine and predicate registry - 2026-07-28

Supports **C7** and adds **C8**: ground truth must match what a reasonable person would
say, not merely be self-consistent.

Step 4 asked what would falsify the measurement. Step 5 asked a different question -
*what would make two reasonable humans disagree?* - and it has a different answer.
Measurement error is not what makes a benchmark case contested. **Competing reasonable
interpretations are.**

**The mechanism: operationalization invariance**
Every spatial predicate carries a primary definition plus alternatives a reasonable
person might equally have chosen. A sample may host the predicate only when all of them
pick the same element. `leftmost` is checked as centroid, left edge, and bbox midpoint;
`top_left` as euclidean, manhattan, and nearest-bbox-corner distance.

Measured before the gate existed, disagreement was not hypothetical: `leftmost` flips
between centroid and left edge in 1/15 SVGs and between centroid and bbox midpoint in
2/15; `top_left` flips between euclidean and manhattan in 2/15. Roughly one sample in
eight is humanly contested while being mathematically unambiguous.

**Refusal breakdown** (360 slots = 30 SVGs x 12 predicates)
valid 65.6% | distractor outranks target 13.1% | margin too small 11.4% |
**definition disagreement 9.4%** | winner outside quadrant 0.6%

**Deliberately not built**
An elongation gate. Equal-area shapes of differing aspect ratio are not perceived as
equal - but this corpus has median bbox aspect ratio 1.11, max 1.53, and bbox-area
ranking agrees with true-area ranking 15/15. The threat does not materialise, so no gate
was written. A gate that can never fire is decoration.

**Two failed assumptions** (FA-007, FA-008)
`min_spatial_margin = 0.15` sat on the median of the observed margin distribution,
refusing 52% of spatial predicates and leaving 13 of 30 SVGs unable to supply their
spatial instructions. Reset to 0.08 on perceptual grounds - about one shape radius on a
512 canvas. Sweeping showed the threshold was not the whole story: definition
disagreement and distractor dominance are validity requirements, not tunable knobs, so
per-SVG availability is inherently uneven and Step 7 must allocate adaptively.

The test that should have caught this asserted at least one predicate per family per
sample, and passed - the minimum really was 1. Availability is a corpus-level property,
so a per-item assertion is not a weaker version of the aggregate check, it is a
different check that passes while the requirement fails.

**Added**
- `svgbench.groundtruth` - predicate registry, construct-validity gate, per-sample answer
  key that refuses to answer where it has no defensible answer.
- `FAILED_ASSUMPTIONS.md` - every time the project proved itself wrong, with impact.
- Claim lifecycle in `CLAIMS.md`: Proposed, Specified, Measured, Stress-tested, Published.
- README now opens with the question a reviewer actually asks, and a concrete example of
  the markup, rather than with methodology.


### Sprint 2, Step 4 - Geometry engine - 2026-07-28

Supports **C7**: ground truth is correct, not merely asserted. Treated as the first
module that can invalidate the whole benchmark, so the tests were written as
falsification attempts rather than as confirmations.

**Added**
- `svgbench.geometry` - analytic path algebra (`svgelements`) and raster pixel coverage
  (`resvg`), cross-validated per element, with `GeometryDisagreementError` rejecting a
  sample rather than widening a tolerance.
- `EVIDENCE.md` - measured values per claim, regenerated rather than recalled.

**Eight falsifiers, each one a test**
Known-answer failure; rank disagreement between witnesses; translation changing measured
area; rank changing with raster resolution; isolated coverages not summing to the
document; area centroid confused with vertex mean; error correlating with shape size;
witnesses disagreeing on the real corpus.

**Measured** (110 elements, 12 SVGs)
- Rank agreement **12/12 SVGs** - the operative gate, since the ordinal family needs an
  ordering rather than an area.
- Relative area disagreement median **0.0001**, max **0.0014**.
- Centroid disagreement median **0.005**, max **0.030** user units.
- Size-dependent bias drift **0.0001**.

**Tolerances tightened after calibration**
Area 0.05 -> **0.02**, centroid 1.5 -> **0.5**. The original bounds were 35x the observed
maximum and would have accepted almost any degradation. Set from the instrument's own
noise distribution, before any model runs.

**Bug found by falsification**
`ElementIntent.center_x` was the *placement anchor*, not the area centroid - they differ
by ~3 units because vertex radii are jittered. Renamed to `placement_x`/`placement_y`.
Reaching for `center_x` as a centroid at Step 5 would have made every spatial predicate
systematically wrong while remaining internally consistent.

**Correction to an earlier claim**
Prior notes described three *independent* witnesses. That overstated it: generator intent
and analytic geometry share the shoelace formula and differ only in where the vertices
came from, so that pair is a serialization check. The independent witness is the
rasterizer. Corrected in `CLAIMS.md` and the module docs.


### Sprint 2, Step 3 — Dataset generator — 2026-07-28

Supports **C1**: the corpus is genuinely under-determined. Every invariant here is one
a reviewer would otherwise have to take on trust.

**Added**
- `svgbench.generation` — seeded scene synthesis, area-controlled irregular polygons,
  non-overlapping placement, and geometry redaction.
- **Positional seeding.** A sample's seed derives from its index, not a running counter,
  so regenerating sample 17 alone reproduces it exactly and a change in early rejection
  cannot cascade and reshuffle the corpus.
- Generator emits *intent* only and deliberately does not import the geometry engine —
  if it placed shapes by consulting the measurement that will later verify them, the
  two-witness check at Step 5 would agree by construction and be vacuous.
- `CLAIMS.md` — every module maps to one claim, with what would falsify each and what
  the repository explicitly does not claim.
- README **Threats to validity**, split into internal / construct / external /
  statistical-conclusion.

**Corpus properties (30 SVGs, default seed)**
- 0 placement rejections; K balanced over 4–7; 168 ambiguity elements.
- Minimum adjacent area ratio 1.351 against a configured floor of 1.25.

**Two measurement bugs found and fixed — in the tests, not the generator**

A leak check reported document order predicting area at z = +2.76. Rather than accept
it, a 25-seed sweep showed mean z = +1.605 at 8.95 SE from zero — apparently systematic.
Two distinct defects, both in the statistic:

1. **Ordinal ranks instead of midranks.** The pooled data is almost entirely ties, so a
   stable sort resolved every tie by append order — identical in both vectors — which
   manufactures correlation from nothing.
2. **Analytic z is miscalibrated for this structure.** Under a shuffle uniform *by
   construction*, `rho*sqrt(n-1)` has mean +0.88, not 0: positions and attribute ranks
   both run 0..K-1 within an SVG, so pooling across SVGs with different K induces
   association from group size alone.

Replaced with a permutation null — exact, tie-safe, assumption-free, and the same
instrument the main analysis already commits to (ADR-0007). Standardised against the
empirical null the generator sits at +0.362 (2.18 SE): unbiased. Had the analytic
statistic been trusted, this would have been reported as a generator leak that does not
exist.

**Verified, not assumed**
- Leak detector tested against a planted document-order-equals-area-order corpus and
  required to reject it.
- Audit suite runs the invariants at the *shipped* 30-SVG size, not just the fast
  6-SVG fixture.

### Sprint 2, Step 2 — Configuration system — 2026-07-28

The config system exists to make one property machine-checkable: **the arms differ in
exactly one variable.** Without that, the central comparison is uninterpretable
whatever its value.

**Added**
- `svgbench.config` — strict schema (unknown keys rejected, models frozen), three-layer
  resolution (base → experiment → explicit override), and canonical hashing.
- **Two hashes, deliberately separate.** `config_hash` is the identity of an
  *experiment* and must differ between arms so their responses cannot collide.
  `corpus_config_hash` is the identity of a *corpus* and must be equal across arms, or
  each arm would generate its own dataset and the paired comparison in ADR-0007 would
  be invalid. Verified: four distinct config hashes over one shared corpus hash.
- Controlled vocabularies (predicate and operation names) owned by `config`, so the
  predicate registry imports them rather than the reverse. Keeps `config` a
  dependency-free leaf while still catching a typo'd predicate at load time.
- Cross-field validation that a corpus can support its own instructions —
  `third_largest` with `ambiguity_min < 3` is rejected at load rather than surfacing
  later as an inexplicable rejection loop.
- `configs/base.yaml` (complete on its own) plus one file per arm. The arm files are
  deliberately three lines each, so the fairness invariant is visible at a glance.
- `svgbench config <experiment>` prints the resolved config with both hashes.
- Arm-fairness audit suite (`tests/audit/`): arms differ only in `context`, decoding
  settings are identical, providers are distinct, corpus is shared, the `permuted`
  control exists.

**Verified, not assumed**
- Planted an arm with a drifted `temperature` and confirmed the audit fails (three
  independent checks caught it), then confirmed it passes on removal. An audit that
  cannot fail is decoration.

**Justification** — the practice of hashing every result-affecting parameter follows
Biderman et al. 2024 ([arXiv 2405.14782](https://arxiv.org/html/2405.14782)), which
documents that undocumented evaluation settings, not flawed reasoning, are the leading
cause of irreproducible LLM results — with observed swings above 20% and reordered
model rankings.

### Sprint 2, Step 1 — Repository scaffolding — 2026-07-28

**Added**
- Repository structure, MIT license, packaging (`pyproject.toml`), CI for Linux + Windows.
- `DESIGN_FREEZE.md` — architecture, protocol, scoring, metrics and layout frozen; amendment
  procedure and the pre-registration boundary defined.
- Frozen design record: `docs/00-prd.md`, `docs/01-architecture.md`,
  `docs/02-experiment-design.md` (the pre-registration), `docs/glossary.md`.
- `docs/adr/` — ten decision records covering the toolchain, redaction scheme, output format,
  canonical area, the runner seam, the primary metric, corpus size and inference, abstention,
  and the permuted-facts control. ADR-0010 (decoding policy) is deliberately left **pending**
  with a pre-committed resolution rule.
- `LIMITATIONS.md`, written before any results exist.
- `docs/BACKLOG.md` — out-of-scope ideas, so they stop competing for attention.
- Package skeleton: twelve subpackages, each documenting its responsibility.
- `svgbench` CLI: `status` works; unimplemented pipeline steps exit non-zero with an
  explanation instead of a traceback.
- Scaffold tests, including two architectural gates: pipeline layering is one-directional, and
  the scoring path cannot import a renderer.
- `Makefile` and `tasks.ps1` as thin wrappers over the same CLI, so Windows and POSIX
  reviewers run identical code paths.

**Design changes carried in from the adversarial review**
- Primary metric changed from strict accuracy to **identification accuracy** (ADR-0006).
- **Abstention** promoted to a first-class outcome class (ADR-0008).
- **`permuted` control arm** added and made blocking; the pre-registered primary comparison is
  now `enhanced` vs `permuted`, not `enhanced` vs `baseline` (ADR-0009).
- `legible` and `facts_only` arms added (ADR-0009).
- Reporting unit changed from family to **predicate**.
- Hypothesis testing changed from bootstrap to **paired cluster-level permutation**
  (ADR-0007).
- Contribution reframed: the enhanced arm is the benchmark, the baseline is a manipulation
  check.
- Predicate uniqueness now asserted against the full element set, not only the ambiguity set.

**Verified**
- Rendering stack probed before adoption: `resvg` and `svgelements` agree exactly on a known
  shape (2500/2500 px; analytic bbox exact). Recorded in ADR-0001.

**Not yet done**
- No experiments have been run. No results exist.
