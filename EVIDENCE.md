# Evidence

Measured values, not intentions. Every row is produced by a test in this repository and
was regenerated for this document rather than recalled.

Claims are defined in [`CLAIMS.md`](CLAIMS.md). A claim with no evidence row is a claim
this repository has not yet earned.

**Corpus under measurement:** 30 SVGs, seed `20260728`.
**Dataset hash:** `a2938bb031c0220abb45df12b7bc3eaa19a33484ac15592e59c62247010d2b35`
**Corpus config hash:** `f2a6e5b2a40142659a786c6b1f2df26d50ef1218231ba5ccc97659a50d0846dd`
**Last regenerated:** 2026-07-28. `164 passed`, ruff and strict mypy clean.

> The corpus config hash changed from `be04eae9ebca` after `min_spatial_margin` was
> recalibrated at Step 5 (FA-007). Earlier revisions of this document cite the old
> value; the corpus it names no longer exists.

---

## C1 - the corpus is genuinely under-determined

| Test | Result | Status |
|---|---|---|
| Ambiguity-set members share tag and fill | all 30 SVGs, single `(tag, attrs, fill)` signature per set | PASS |
| No positional attributes on any shape | 0 occurrences of `transform`/`x`/`cx`/... | PASS |
| Geometry tokens are fixed length | exactly one length observed: **17 chars** | PASS |
| Element ids are fixed length and opaque | exactly one length observed: **9 chars** | PASS |
| No decimal coordinates survive redaction | 0 matches outside `d` | PASS |
| Redaction is structure-preserving | resolved == model-visible with `d` masked | PASS |
| Tokens unique within a document | no collisions in 30/30 | PASS |
| Token-to-path map absent from model-visible SVG | 0 leaks | PASS |
| Ambiguity-set size in range | K in **4-7**, 168 ambiguity elements total | PASS |
| Shapes do not overlap (intent) | all pairwise centre distances exceed summed radii | PASS |
| Shapes do not overlap (**rendered pixels**) | isolated coverages sum to document coverage within 1% | PASS |
| Adjacent area ranks separated | min observed ratio **1.351** vs configured floor 1.25 | PASS |

### Document order carries no information

Permutation test, 2000 draws, within-SVG ranks. Fails below p = 0.005.

| Visible ordering | vs area | vs placement x | vs placement y |
|---|---|---|---|
| document index | **0.0315** | 0.3853 | 0.9630 |
| element id | 0.4528 | 0.2679 | 0.4683 |
| geometry token | 0.4073 | 0.3268 | 0.4908 |

Worst case is `document_index` vs `area` at **p = 0.0315**. Reported rather than rounded
to "pass": it is the smallest of nine tests, and the smallest of nine draws from a
uniform null falls below 0.031 about 25% of the time, so this is unremarkable. It is
recorded so that a future change making it *smaller* is visible as a trend rather than
discovered as a threshold breach.

| Falsification check | Result | Status |
|---|---|---|
| Detector rejects a planted leak (document order = area order) | **p = 0.00050** | PASS |

---

## C2 - the arms are comparable

| Test | Result | Status |
|---|---|---|
| All arms share one corpus | 1 distinct corpus hash: `be04eae9ebca` | PASS |
| Arms are distinct experiments | 4/4 distinct config hashes | PASS |
| Arms differ only in `context` | no other section differs | PASS |
| Decoding settings identical across arms | 1 distinct decoding tuple | PASS |
| `permuted` control exists | present and blocking | PASS |
| Audit rejects planted drift | temperature 0.0 -> 0.7 caught by **3 independent checks** | PASS |

---

## C6 - results are independently verifiable

| Test | Result | Status |
|---|---|---|
| Corpus regeneration is byte-identical | `84d56663...` twice | PASS |
| Regenerating one sample alone reproduces it | sample 17 matches corpus[17] | PASS |
| Placement is stable | **0 rejections** across 30 samples | PASS |
| Config hash invariant to key order | identical | PASS |
| Config hash changes with every result-affecting value | 9/9 detected | PASS |
| Corpus hash ignores model/prompt/context/metrics | 7/7 ignored | PASS |

---

## C7 - ground truth is correct, not merely asserted

Two witnesses measure every element: `svgelements` path algebra and `resvg` pixel
coverage. Measured on **110 elements across 12 SVGs**.

| Test | Result | Status |
|---|---|---|
| **Rank agreement - the operative gate** | **12/12 SVGs** | PASS |
| Relative area disagreement | median **0.0001**, max **0.0014** (bound 0.02) | PASS |
| Centroid disagreement | median **0.005**, max **0.030** user units (bound 0.5) | PASS |
| Size-dependent bias | small vs large shapes drift **0.0001** (bound 0.02) | PASS |
| Isolated coverages sum to document coverage | within 1% - non-overlap holds in pixels | PASS |
| Known square, analytic | area 2500, bbox (10,10,60,60), centroid (35,35) - exact | PASS |
| Known triangle, analytic | area 800, centroid (40/3, 40/3) - exact | PASS |
| Known square, raster | area 2500 +/-2%, centroid +/-0.5px | PASS |
| L-shape area centroid differs from vertex mean | separated by >1 unit, both hand-computed | PASS |
| Translation invariance of area | 4 offsets, area and bbox unchanged | PASS |
| Rank independence of raster resolution | scale 1 vs 2 agree, 8/8 SVGs | PASS |
| Engine rejects disagreeing witnesses | off-canvas shape raises | PASS |

Rank agreement is the gate that matters. The ordinal family needs an *ordering*; two
witnesses could differ by 2% on every absolute value and the benchmark would still be
sound. The absolute tolerances are a backstop against gross failure.

Tolerances were set from this distribution - roughly 14x headroom over the observed
maximum - *before any model runs*. Calibrating a measuring device against its own noise
is not the same as tuning a scoring rule to a result. An earlier 0.05 bound was 35x the
observed maximum and would have accepted almost any degradation.

### Bug found by falsification, not by testing

| Finding | How it surfaced | Consequence |
|---|---|---|
| `ElementIntent.center_x` was the **placement anchor**, not the area centroid | asserting equality against the analytic centroid; they differ by ~3 units because vertex radii are jittered | renamed to `placement_x`/`placement_y`. Reaching for `center_x` as a centroid at Step 5 would have made every spatial predicate wrong by a few units while remaining internally consistent |

---

## C8 - ground truth matches human judgement

A sample may only host a predicate when **every reasonable reading of the instruction
picks the same element**. Measured over 360 predicate slots (30 SVGs x 12 predicates).

| Outcome | Count | Share |
|---|---|---|
| valid | 236 | 65.6% |
| refused - a distractor outranks the intended target | 47 | 13.1% |
| refused - margin to runner-up too small | 41 | 11.4% |
| refused - **reasonable definitions disagree** | 34 | 9.4% |
| refused - winner outside the required quadrant | 2 | 0.6% |

The 9.4% row is the one C8 exists for. Those samples are measured perfectly; they simply
have no answer a person would confidently give. Measured before the gate was built:

| Predicate | Competing readings | Disagreement |
|---|---|---|
| `leftmost` | centroid vs left edge | 1/15 SVGs |
| `leftmost` | centroid vs bbox midpoint | 2/15 SVGs |
| `top_left` | euclidean vs manhattan distance to corner | 2/15 SVGs |

| Test | Result | Status |
|---|---|---|
| Valid predicates agree under every alternative definition | re-derived independently of the engine | PASS |
| The gate actually refuses cases | 124/360 refused | PASS |
| Ordinal ranks pick the genuinely k-th largest | all valid predicates | PASS |
| Valid spatial targets beat every distractor | full element set, not just the ambiguity set | PASS |
| Answer key refuses to answer where it has no answer | `target_of` raises on invalid predicates | PASS |
| Every sample hosts both families | 30/30 | PASS |
| Corpus supplies the instruction budget | 116 spatial slots vs 90 needed | PASS |
| Ground truth is deterministic | repeated builds identical | PASS |

### Deliberately not gated

**Shape elongation.** Equal-area shapes of differing aspect ratio are not perceived as
equal, which would threaten the ordinal family. Measured on this corpus: median bbox
aspect ratio **1.11**, max **1.53**, and bbox-area ranking agrees with true-area ranking
in **15/15 SVGs**. The threat does not materialise, so no gate was built. A gate that can
never fire is decoration.

---

## Instruction set (Step 7)

180 instructions over 30 SVGs, 6 per sample.

| Property | Result | Status |
|---|---|---|
| Every instruction uses a predicate the sample can host | 180/180 | PASS |
| Target matches ground truth exactly | resolver is code, never a model | PASS |
| Target is always an ambiguity-set member | 180/180 | PASS |
| Family balance across the corpus | **90 SPATIAL / 90 ORDINAL - exactly 50/50** | PASS |
| Operation balance | 44 / 44 / 44 / 48, spread 4 | PASS |
| Predicate balance within family | ordinal 22-23 each, spatial 10-12 each | PASS |
| Distinct phrasings used | **120** across 12 predicates | PASS |
| Every predicate used with >1 phrasing | 12/12 | PASS |
| No duplicate (predicate, operation) within a sample | 180/180 | PASS |
| Instruction text contains no id, token or document fill | 180/180 | PASS |
| Requested edit colour absent from the document | all recolor cases | PASS |
| Lint rejects a planted leak | raises on an injected element id | PASS |
| Deterministic | repeated builds byte-identical | PASS |

**Mean per-case 1/K reference: 0.1852.** This is the number the baseline arm must land
near for C1 to hold. K distribution over cases: 4 (36 cases), 5 (36), 6 (72), 7 (36).

### Unevenness preserved, not erased

Distinct spatial predicates available per sample, after the construct-validity gate:

| distinct predicates | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| samples | 2 | 6 | 12 | 8 | 2 |

Every sample still contributes 3 spatial and 3 ordinal instructions. A sample with only
two surviving spatial predicates fills its quota by pairing them with different
operations, rather than by weakening the gate that refused the others. Balance is
corpus-level; validity stays per-sample.

### Provenance

Every instruction records why it exists and what was refused alongside it:

```
ins_5690b36019cb  predicate=largest  margin=1.592
  accepted_because: all_definitions_agree, margin_clears_threshold,
                    unique_over_full_element_set, witnesses_agree_on_ranking
  rejected_candidates:
    bottommost    definition_disagreement
    leftmost      definition_disagreement
    rightmost     margin_too_small
    top_left      definition_disagreement
    topmost       distractor_outranks_target
```

---

## Frozen dataset (Step 8)

`data/frozen/a2938bb0.../` - 95 files, 512 KB, committed. Self-describing: the exact
bytes the model will receive, the answer key, the archived distributions, and a
certificate.

| Check, run against the bytes on disk | Result |
|---|---|
| Generator invariants | 30 samples: identical tag/fill, no positional attributes, 17-char tokens |
| Geometry witnesses | raster and analytic agree on ranking 30/30 |
| Ground truth | 236/360 predicate slots admitted, 124 refused as contested |
| Instruction allocation | 180 instructions, 90 spatial / 90 ordinal |
| Leakage audit | 180 instructions carry no id, token or document fill |
| **Model outputs observed** | **NO** - `experiments/` contains no stored responses |

### Integrity verified by tampering, not by re-implementation

Per [`docs/verification-policy.md`](docs/verification-policy.md), the oracle is not a
second copy of the hashing code.

| Tamper | Detected |
|---|---|
| One character edited in one SVG | yes - reports which file changed |
| A ground-truth file deleted | yes |
| An extra file added | yes |
| Directory renamed | yes - no longer matches its own hash |
| Manifest edited to match tampered files | yes |
| Regeneration from a different seed | yes |
| Untouched corpus | verifies, and regenerates byte-identically |

### Hash scope

`dataset_hash` covers the **case-defining artefacts only** - SVGs, ground truth,
instructions. The manifest, certificate and `distributions.json` are excluded from it
but still covered by per-file hashes.

The reason is not tidiness. If a derived summary were part of the identity, adding one
distribution later would change the dataset hash while every case stayed byte-identical,
spuriously invalidating stored results and breaking the rule that all arms share one
dataset hash. Verified both ways: editing `distributions.json` leaves the dataset hash
unchanged *and* still fails integrity verification.

---

## C4 and C5 - the evaluation engine (Step 9)

26 hand-authored fixtures, each carrying its expected verdict **and its reasoning**,
written before the scorer existed. All six outcome classes and all four operations
covered.

### Can the scorer be wrong while every fixture still passes?

The review gate, answered by breaking the scorer nine ways and requiring the fixtures to
notice each. **9/9 caught.**

| Deliberate break | Caught by |
|---|---|
| No colour normalisation (`#00f` != `#0000ff`) | `recolor_target_short_hex`, `recolor_target_named_colour` |
| No rotation modulo (`rotate(450)` != `rotate(90)`) | `rotate_target_congruent` |
| Compare all attributes (non-rendering counted as collateral) | `non_rendering_attribute_added`, `renamed_ids_tokens_preserved` |
| Abstention checked after the document | `abstention_with_unchanged_document` |
| Silence counted as abstention | `whitespace_only` |
| Execution folded into identification | `right_element_wrong_operation`, `rotate_target_wrong_angle` |
| Deletion treated as a missing element | `delete_target` |
| Numeric tolerance ignored (`3` != `3.0`) | `numeric_formatting_difference` |
| Align by position only | `reordered_elements`, `renamed_ids_tokens_preserved`, +3 |

Kept as a permanent audit test, so a future fixture deletion that opens a hole fails the
build rather than passing quietly.

### Semantic decisions fixed before any model output

Writing adversarial fixtures forced five questions that had been implicitly assumed.

| Question | Decision |
|---|---|
| Is whitespace-only output an abstention? | **No - MALFORMED.** Silence makes no claim about insufficient information |
| Are reordered attributes a change? | **No.** Attribute order is meaningless in XML |
| Is `rotate(450)` equal to `rotate(90)`? | **Yes.** They render identically, and this instrument exists to privilege the rendered layer |
| Is a non-rendering attribute change collateral? | **No.** Collateral is defined over rendering-relevant attributes only |
| Two ambiguity members edited identically? | **Depends on whether one is the target.** `CORRECT_LOOSE` if so, `WRONG_TARGET` if not |

### Arm-blindness

Enforced by the interface: `evaluate_response` takes no `arm`, `provider`, `context`,
`experiment_id` or `config_hash` parameter, asserted by test. An arm-dependent scoring
rule cannot be written without changing the signature, which is visible in review rather
than buried in a branch.

---

## Instrument calibration

Findings about the *measuring tools*, recorded because a wrong instrument is
indistinguishable from a wrong result until someone checks.

| Finding | Measurement | Consequence |
|---|---|---|
| Ordinal ranks are invalid for heavily-tied pooled data | stable-sort tie-breaking correlated both vectors by append order | replaced with midranks |
| `rho * sqrt(n-1)` is miscalibrated for this structure | under a **provably uniform** shuffle its mean is **+0.880**, not 0 (2000 draws) | replaced with a permutation null |
| Generator is unbiased once measured correctly | **+0.362**, 2.18 SE from zero, standardised against the empirical null | no generator change needed |

Had the analytic statistic been trusted, this project would have reported a generator
leak that does not exist. The same pooling artifact threatens the main analysis, which
also aggregates across SVGs with differing K - the reason ADR-0007 commits to
permutation testing there too.

---

## Not yet evidenced

Listed so absence is visible rather than implied.

| Claim | Blocked on |
|---|---|
| **C4** identification separable from execution | Step 9 |
| **C5** abstention measured, not punished | Step 9 |
| **C3** improvement is information, not format | Step 12-13. **The central claim. No data yet.** |
| baseline approximately 1/K | Step 11 |
| enhanced vs permuted | Step 13 |
