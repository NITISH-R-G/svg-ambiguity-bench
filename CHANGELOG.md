# Changelog

Sprint-by-sprint increments. Amendments to frozen design documents are recorded here as
required by [`DESIGN_FREEZE.md`](DESIGN_FREEZE.md).

## [Unreleased]

### PHASE II BEGINS - Step 10: model runner and smoke test - 2026-07-29

First work after `instrument-freeze-v1`. Two decisions resolved by measurement, and one
disclosed amendment.

**ADR-0010 resolved: replicates = 1.** The pre-committed rule was that the smoke test
would measure whether the backend is deterministic at temperature 0, and the answer
would decide the policy. Three byte-identical prompts returned **one** distinct response
on both candidate models. Deterministic, so N replicates would be N identical calls
implying a robustness that does not exist. The rule fired as written; no judgement was
exercised after seeing the result.

**ADR-0011: model selected as `qwen2.5-coder:3b`.** Both candidates were pulled
specifically so this would not have to be a guess, and the gap was far larger than
expected:

| | 1.5b | 3b |
|---|---|---|
| unparseable | **4/12 (33%)** | **0/12 (0%)** |
| median latency | 6.6s | 15.2s |
| projected 540 calls | 1.0h | 2.3h |

A third of responses failing to parse is not a minority failure mode in any useful
sense - it would mean much of every arm's score was decided by whether the model could
emit well-formed XML. R4 explicitly sanctions swapping models pre-baseline provided the
reason is recorded.

Note: the smoke script printed `PASS` for the 1.5b against a 30% threshold that was an
arbitrary constant written without justification. That constant is **not** the basis of
the decision; the measured 0% versus 33% is.

**AMENDMENT: prompt template 1.0 -> 1.1.** The plumbing check found that the placeholder
example rendered as `{GEOM_1234abcd}` while the actual document tokens are
`{{GEOM_1b7549de}}` - `str.format` collapses `{{` to `{`. Every prompt described the
tokens as looking different from how they appear.

Disclosed under the DESIGN_FREEZE amendment procedure. It qualifies: the fix affects
every arm identically, no baseline had been run, and applying the RESULTS.md test -
*would this have been made identically had the arms come out the other way around?* -
gives an unambiguous yes. Re-running the smoke test after the fix produced an identical
outcome pattern at n=12, which does not make the fix optional: a prompt that misdescribes
the document is a defect whether or not the model noticed.

**The two-hash split proved its worth.** Changing model and prompt left
`corpus_config_hash` at `f2a6e5b2...` - unchanged - while `config_hash` moved
`c8b06c9d` -> `ffdd4652`. The corpus is intact and all arms still share it. That
separation was designed at Step 2 for exactly this moment.

**Added**
- `svgbench.context` - the four providers. `permuted` retries until the permutation
  displaces at least one element, since an identity permutation would silently turn the
  arm into `enhanced` and the control would vanish with no test failing.
- `svgbench.runner` - one prompt template, one execution path, append-only response store
  keyed by experiment/case/replicate so runs resume exactly and nothing is overwritten.
- Nine context-blindness audits. The strongest: excising the injected block verbatim from
  any arm's prompt must leave text byte-identical to the baseline prompt.
- `svgbench run <arm>`, which verifies the frozen corpus and refuses if the arm's
  corpus hash does not match it.


### Sprint 2, Step 9 - Evaluation engine - PHASE I COMPLETE - 2026-07-28

Supports C4 (identification separable from execution) and C5 (abstention measured, not
punished). The last step of instrument design.

26 hand-authored fixtures, each carrying its expected verdict **and its reasoning**,
written before the scorer existed. All six outcome classes, all four operations, plus
adversarial cases: renamed ids, reordered elements, colour-notation variants, right
element with wrong operation, right edit plus collateral, and three phrasings of
abstention.

**The review gate, answered rather than assumed.** "Do the fixtures pass" is not
evidence the fixtures are adequate. The scorer was deliberately broken nine ways and
each break required to be caught: **9/9 caught**. No colour normalisation, no rotation
modulo, comparing all attributes, abstention checked last, silence counted as
abstention, execution folded into identification, deletion treated as absence, numeric
tolerance ignored, and align-by-position-only. Kept as a permanent audit test, so a
future fixture deletion that opens a hole fails the build.

**Five semantic decisions, forced by writing the adversarial fixtures.** Each had been
implicitly assumed, and each is now fixed before any model output exists: whitespace-only
output is MALFORMED not ABSTAINED; reordered attributes are not a change; `rotate(450)`
equals `rotate(90)`; non-rendering attribute changes are not collateral; two identically
edited members are CORRECT_LOOSE or WRONG_TARGET depending on whether the target is
among them.

**Arm-blindness by interface.** `evaluate_response` accepts no `arm`, `provider`,
`context`, `experiment_id` or `config_hash` parameter, asserted by test. An arm-dependent
scoring rule cannot be written without changing the signature.

**A bug in the mutation harness, not the fixtures.** The first run reported two
mutations surviving. They had not applied: `from X import Y` copies the reference, so
patching the defining module leaves the importer's binding untouched. The harness
understated the fixture set rather than overstating it, which is the safer direction -
but a verification tool that reports the wrong answer is worth the same scepticism as
the thing it verifies.

### Sprint 2, Step 8 - Dataset freezing and the instrument certificate - 2026-07-28

Supports C6: every reported number is independently verifiable.

**Frozen corpus**: `data/frozen/a2938bb0.../`, 95 files, 512 KB, committed. Contains the
model-visible SVGs, the resolved geometry, the answer key, the instruction set with
provenance, the archived distributions, a manifest, and a certificate.

**Instrument certificate.** A hash proves two corpora are identical; it cannot state
what kind of corpus it is or whether anything has been observed. `svgbench freeze`
prints a human-readable certificate carrying the hashes, the counts, six checks run
against the bytes on disk, and the line that matters most:

```
[PASS]  Model outputs observed
        NO - experiments/ contains no stored responses
```

That check reads the filesystem rather than asserting a fact, because the point of the
pre-registration boundary is that the claim can be verified by someone who does not
trust the author.

**Archived distributions.** Twenty-odd distributions sealed inside the frozen directory
and content-hashed with it: K, margins, aspect ratios, adjacent area ratios, refusal
reasons, predicate and operation counts, valid predicates per sample, and the
document-order position of every target. Not needed to run the experiment - they
*define the instrument*, and give any future v2 corpus a baseline to be compared against.

**Freezing refuses on a failed check.** A corpus that does not satisfy its own
guarantees must not become the thing every later number depends on.

**Verification by tampering** (`docs/verification-policy.md`). The oracle is not a
second copy of the hashing code. Editing one character in one SVG, deleting a
ground-truth file, adding a file, renaming the directory, and editing the manifest to
match tampered files are each required to be detected - and are.

**Hash scope corrected before the freeze was final.** `dataset_hash` initially covered
`distributions.json`, so adding a distribution later would have changed the dataset
identity while every case stayed byte-identical - spuriously invalidating results and
breaking the rule that all arms share one dataset hash. It now covers the case-defining
artefacts only; derived files remain under per-file hashes. Verified both ways: editing
`distributions.json` leaves the identity stable *and* still fails integrity.

**A distribution bug caught by a lint.** Ruff flagged a redundant comprehension in the
target-document-position calculation, which on inspection was sorting ambiguity members
by element id while its own comment said "document order". That distribution exists
specifically to test whether a fixed-position policy could beat the 1/K floor, so a
wrong ordering would have made the C1 diagnostic useless while looking entirely
plausible.

**Verification policy** promoted from FA-010 to `docs/verification-policy.md`: a
verification fixture must be able to fail for a different reason than the implementation
would. Different code is not necessarily different reasoning. Binds hardest at Step 9,
where the review question is *"can the scorer be wrong while every fixture still
passes?"*

**Lifecycle boundary** recorded in `DESIGN_FREEZE.md`: Phase I is instrument design
(Steps 1-9), Phase II is measurement (Steps 10+), separated by `instrument-freeze-v1`.

### Sprint 2, Step 7 - Instruction generator - 2026-07-28

Last step before dataset freezing. Supports C1 (instruction text leaks nothing
matchable against the markup) and C8 (only predicates with a defensible answer become
cases).

**180 instructions over 30 SVGs, 6 per sample**
- Family balance: **exactly 90 SPATIAL / 90 ORDINAL**
- Operations: 44 / 44 / 44 / 48
- 120 distinct phrasings; every predicate used with more than one
- Mean per-case `1/K` reference: **0.1852** - the number baseline must land near

**Unevenness preserved rather than erased.** Distinct spatial predicates available per
sample ranges 2 to 6 after the construct-validity gate. Every sample still contributes
3 spatial and 3 ordinal instructions: one with only two surviving predicates fills its
quota by pairing them with different operations, rather than by weakening the gate that
refused the others. Balance is corpus-level, validity stays per-sample.

**Provenance on every instruction.** Each records `accepted_because`, its margin, and
every predicate refused for that sample with the reason. Not required by the
experiment - required by whoever later looks at one odd-seeming instruction and needs
to know why it survived when another did not, without re-deriving the ground-truth pass.

**Two failed assumptions** (FA-009, FA-010)

Least-globally-used predicate selection produced **61% spatial** (44 vs 28). There are
twice as many spatial predicates as ordinal ones, so each accrues usage more slowly and
keeps winning the comparison: the rule balanced *predicates* correctly and *families*
not at all. Replaced with explicit per-family quotas, least-used selection operating
only within a family.

The leakage lint matched `"line "` inside `"outline"`, rejecting every `add_stroke`
instruction. Fixed with word-boundary regex. The unit test written to independently
verify the lint contained the identical bug and failed on the identical instruction -
independent verification is only independent when the *reasoning* is independent, not
merely the code.

**Lifecycle boundary recorded.** `DESIGN_FREEZE.md` now marks Phase I (instrument
design, Steps 1-9) and Phase II (measurement, Steps 10+), separated by the
`instrument-freeze-v1` tag. The same sentence - "this threshold seems miscalibrated" -
is a finding in Phase I and a rationalisation in Phase II; only the side of the tag
changes.

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
