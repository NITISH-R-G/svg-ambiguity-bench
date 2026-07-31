# Validity

This project is best read as a **measurement instrument** rather than a benchmark. A
benchmark says "here are some tasks". An instrument says "here is what I measure, how it
is calibrated, where it fails, and what you may conclude from a reading."

This document assembles the validity argument in one place. The evidence lives in
[`EVIDENCE.md`](EVIDENCE.md), the claims in [`CLAIMS.md`](CLAIMS.md), the design
rationale in [`docs/adr/`](docs/adr/), and the things that turned out to be wrong in
[`FAILED_ASSUMPTIONS.md`](FAILED_ASSUMPTIONS.md). A reviewer should not have to assemble
the argument mentally from four documents, so it is assembled here.

**The measurand.** Whether supplying derived visual facts improves a small language
model's ability to identify the element an instruction refers to, *over and above* the
improvement caused by the format those facts arrive in.

**Status: pre-registration.** No model has been run. Every section below states what is
established, what is planned, and what cannot be established at all.

---

## 1. Internal validity

*Could anything other than the manipulated variable explain a difference between arms?*

| Threat | Control | State |
|---|---|---|
| Arms drift apart (decoding, prompt, retries) | One runner, one prompt template, one injected `ContextProvider`. Arm config files are three lines each | Established - audit fails on planted drift, caught 3 ways |
| Arms see different corpora | `corpus_config_hash` must be identical across arms; `config_hash` must differ | Established - 4 distinct config hashes over 1 corpus hash |
| Position leaks into markup | No `transform`/`x`/`cx` on any shape; audited on the shipped corpus | Established - 0 occurrences |
| Size leaks through token length | Fixed-length geometry tokens | Established - exactly one token length observed |
| Document order predicts the answer | Order shuffled independently of geometry; permutation test | Established - worst p = 0.0315 over nine checks; detector rejects a planted leak at p = 0.0005 |
| Identifiers sortable into geometric order | ids and tokens are hashes of a pre-shuffle index | Established - 6/6 checks non-significant |
| The enhancement conditions on the instruction | `ContextProvider` signature excludes the instruction; context cached per SVG | Specified, enforced by type; verification at Step 12 |
| The enhancement leaks the answer | Vocabulary check against instruction templates; `ceiling` arm isolates the labelled condition | Specified; Step 12 |
| Improvement is prompt length, not content | `permuted` arm - same format, values shuffled between elements | Specified; Step 13. **The central control** |
| Improvement is format compliance | Malformed and truncation rates reported per arm; identification reported conditional on well-formed output | Specified; Step 9 |
| Scoring favours one arm | Scorer is arm-blind by construction - it reads a response store keyed by case, and is never told the arm | Specified; Step 9 |
| Scoring rules tuned to observed results | Rules frozen and git-tagged before the first model output | Planned - tag at Step 9 |

**Residual.** The `permuted` arm equalises format but not *plausibility*: permuted facts
are internally inconsistent with the picture, and a model might detect that and behave
differently for reasons unrelated to information content. This is not controlled, and it
is the strongest remaining internal-validity objection. It is stated rather than solved.

---

## 2. Construct validity

*Does the instrument measure reference resolution under ambiguity, or something else?*

| Threat | Control | State |
|---|---|---|
| "Ambiguity" is asserted, not constructed | Ambiguity set shares tag and fill; geometry redacted to opaque fixed-length tokens | Established |
| Ground truth is self-consistent but not human | **Operationalization invariance** - a sample hosts a predicate only when every reasonable reading picks the same element | Established - 9.4% of slots refused for definition disagreement |
| One measurement, no cross-check | Two implementations must agree: Rust raster coverage, Python path algebra | Established - rank agreement 12/12 SVGs |
| Mislabelled quantities | `placement_x` is not a centroid, and is named so it cannot be mistaken for one | Established - see FA-001 |
| "Largest" means analytic area, not perceived size | Canonical area is rasterised coverage; elongation measured and found not to threaten ranking (median aspect 1.11, bbox-rank agreement 15/15) | Established |
| A distractor satisfies the instruction better than the target | Uniqueness asserted over the full element set | Established - 13.1% of slots refused on this ground |
| Corner predicates crown a mid-canvas shape | Quadrant conjunct | Established |
| "Edit accuracy" conflates distinct abilities | Reported as identification / execution / collateral, not one bit | Specified; Step 9 |
| Declining to guess is scored as failure | `ABSTAINED` is its own outcome; accuracy reported with and without | Specified; Step 9 |
| **The task may measure execution capability, not reference resolution** | **Study V2: name the target by id, change nothing else** | **Retired - `named_id` scores 0.9278 against 0.0444, so the ability to perform the edit is present and is not what V1 measured. Pre-registered; see `docs/06-study-v2-results.md`** |

**Residual, and it is real.** Operationalization invariance is a *proxy* for human
agreement, not a measurement of it. No human study was run. The claim is "reasonable
formal definitions agree", which is weaker than "people agree". A small author-conducted
review of rendered previews is planned; it will be reported as exactly that and not as a
human-agreement study.

---

## 3. External validity

*What does a reading from this instrument NOT generalise to?*

This is the weakest axis by construction, and deliberately so - the design trades
ecological validity for the ability to attribute failure to a specific cause.

| Limit | Why |
|---|---|
| **Not real SVG editing** | Opaque `{{GEOM_...}}` tokens do not occur in the wild. Baseline failure mixes an ambiguity effect with an unfamiliar-format effect. The `legible` arm (real path data) narrows this; it does not close it |
| **Not language models in general** | One small local model, one quantisation, one backend |
| **Not arbitrary layouts** | Rejection sampling admits only well-separated, non-overlapping scenes. 34.4% of predicate slots are refused; the corpus is easier than the wild, by a published amount |
| **Not all SVG edits** | Four operations, chosen because each is checkable by structural diff. A convenience of measurement, not a representative sample |
| **Not beyond the tested predicates** | The enhancement is blind to the *instruction* (enforced by type) but not to the *benchmark*: choosing to emit centroid and area is informed by knowing which families are tested |
| **Not an argument for using an LLM** | A deterministic solver scores 100%. The instrument measures in-context reference resolution, not whether that is the right engineering choice |
| **Not a comparison against vision** | No VLM arm. If a small VLM handles this trivially, the text-only framing is much less interesting. Addressed in discussion only, which is weaker than measuring it |
| **Not stable across model behaviour, as measured** | **Established by Study V3.** The frozen abstention rule encodes an assumption about *how a model declines*, calibrated on the one model available at freeze time. `qwen2.5-coder:7b` declines in prose those patterns do not match, so 237 reasoned refusals were scored `MALFORMED`. Nothing in the scorer is broken; the behaviour it measures moved. See FA-013 |

### Instrument drift

The last row deserves separating out, because it is not the usual external-validity
caveat and it was not anticipated at pre-registration.

The standard assumption is that a fixed metric plus fixed ground truth keeps future
models comparable. Study V3 is a counterexample within this instrument: both were fixed,
and comparability degraded anyway, because an outcome class kept a name that no longer
described its contents.

> A scoring rule is an empirical hypothesis about the space of permissible model
> behaviour. Freezing it makes that hypothesis auditable rather than timeless.

Scope, stated deliberately narrowly: one axis (how a model declines), four models, one
project. It is a lesson drawn from this work, not an established principle, and it would
need replication in other evaluation settings before deserving stronger wording. What can
be said now is that this instrument has a documented instance of it, and that any
benchmark permitting abstention has the same exposure.

---

## 4. Statistical conclusion validity

*What could make the inference unreliable even if everything above holds?*

| Threat | Control | State |
|---|---|---|
| Cases treated as independent when they are not | Resampling and testing at the **SVG** level; declared in config where a reviewer sees it | Specified (ADR-0007) |
| Asymptotic approximations misbehaving | Paired cluster-level **permutation** tests, not normal-theory intervals | Specified |
| Pooling artifacts across unequal group sizes | Measured: under a provably uniform null, `rho*sqrt(n-1)` has mean +0.88 rather than 0. Permutation nulls used instead | Established - see FA-002 |
| Tie handling inflating correlation | Midranks, not ordinal ranks | Established - see FA-003 |
| Underpowered null read as a real null | Minimum detectable effect computed and reported **before** results | Planned; Step 14 |
| Multiplicity across many secondary metrics | One pre-registered primary comparison (`enhanced` vs `permuted`, paired, per family). Everything else labelled secondary or exploratory | Specified |
| Replicates inflating n | Per-case rate is the analysis unit; replicate count never enters n | Specified |
| Floor effects compressing the estimate | 1/K reference reported per case; identification reported alongside strict | Specified |

**Residual, and unfixable here.** The effective sample size is **~30 clusters**, not 180
cases. Intervals will be wide. This cannot be fixed within the assignment's 20-30 SVG
budget, so the response is a **narrower claim**, not a better estimator. Per-predicate
cells are smaller still and are reported as descriptive, not confirmatory.

---

## 5. What a reading from this instrument licenses

If the pre-registered comparison shows `enhanced > permuted`:

> On this synthetic corpus, for this model, supplying derived geometric facts improved
> element identification by more than an equivalently-formatted list of non-informative
> facts did.

That is the whole claim. Not that models cannot resolve references; not that this
generalises to real SVGs; not that the method is the best available.

If it shows `enhanced ~= permuted`, the finding is that the gain is attributable to
format rather than information - equally publishable, and the reason the control exists.

---

## 6. Known unknowns at pre-registration

Stated now so they cannot be presented later as anticipated.

- Whether the chosen model produces valid SVG often enough for malformed output to be a
  minority failure mode (A1, tested at Step 10).
- Whether the backend is deterministic at temperature 0, which decides the replicate
  policy (ADR-0010, deliberately unresolved).
- Whether abstention occurs at all for this model. Reasoning-tuned models abstain *less*
  well, so the class may be near-empty and C5 vacuous.
- Whether baseline sits at the 1/K floor. If it sits well above, C1 is falsified and the
  result is reported as invalid rather than as a finding.
