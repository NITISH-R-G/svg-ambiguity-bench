# Experiment Design & Pre-Registration

**Status:** FROZEN 2026-07-28, before any model has been run.

This document is the pre-registration. Scoring rules and metric definitions written here are
fixed before the first model output is observed. After the `pre-registration` git tag, any
change is an **amendment**: disclosed in the report, with the pre-change number retained.

---

## 1. Claim structure

**The enhanced arm is the benchmark. The baseline arm is a manipulation check.**

If the corpus is genuinely underdetermined, every model scores at the `1/K` floor in the
baseline arm, so the baseline has no power to discriminate between models. Its role is to
establish that the information was *removed*, not merely obscured. The discriminative
measurement is in the enhanced arm.

The reverse framing — "models fail, we fix them" — would be near-tautological, since the
treatment restores information the design deliberately deleted.

## 2. Independent variable

Exactly one thing differs between arms: the `ContextProvider` that fills the prompt's
context slot.

| Arm | Context | Corpus | Question it answers |
|---|---|---|---|
| `baseline` | empty | redacted | Is the corpus really underdetermined? |
| `permuted` | correct format, **values shuffled between elements** | redacted | Is the gain information, or format? |
| `enhanced` | derived visual facts | redacted | Can the model resolve the reference given facts? |
| `ceiling` | facts **+** predicate labels | redacted | Are residual errors reasoning or information failures? |
| `legible` | empty | **real `d`** | Is baseline failure ambiguity, or unfamiliar markup? |
| `facts_only` | facts, no SVG | — | Does the markup contribute anything? |

`ceiling` is excluded from the headline by construction: it hands over the answer and would
score near-perfectly while proving nothing about reasoning.

**`permuted` is the load-bearing control.** The enhanced prompt changes two things at once:
it adds geometric facts, *and* it adds an enumerated list that gives every element a
referential handle. Enumeration alone could move the score with no geometric content. Without
`permuted`, "supplying geometry closes the gap" and "supplying a list closes the gap" are
indistinguishable, and only the first is being claimed.

## 3. Outcome classes (frozen)

Every response receives exactly one class. Malformed and abstained cases are **scored, never
dropped**; denominators are fixed at freeze time.

| Class | Definition |
|---|---|
| `CORRECT_STRICT` | intended element received the intended edit, and nothing else changed |
| `CORRECT_LOOSE` | intended element received the intended edit, other elements also changed |
| `WRONG_TARGET` | an edit was made, but not to the intended element |
| `ABSTAINED` | the model explicitly declined, citing insufficient information |
| `NO_EDIT` | document returned semantically unchanged, without an explicit abstention |
| `MALFORMED` | unparseable, or element alignment failed |

### Why abstention is separate

The epistemically correct response to "make the top-left shape blue", given markup that
provably does not encode position, is to say the markup is insufficient. Pooling that with
`NO_EDIT` would score correct behaviour as failure, and would mean the metric rewards
confident guessing — while this project's own motivation is that models hedge. Abstention is
therefore reported as its own row, and accuracy is reported both including and excluding it.

`ABSTAINED` requires an explicit textual refusal signal; a silent no-op is `NO_EDIT`. The
classifier for this is fixed before any model output is read.

## 4. Metrics (frozen)

### Primary

**Identification accuracy** = P(the model acted on the intended element), regardless of
whether the edit was executed correctly and regardless of collateral changes.

This is primary because it is the quantity the experiment is about. `CORRECT_STRICT`
conflates three separable capabilities — identification, execution, non-collateral output —
and reporting it as headline would attribute a formatting failure to a reasoning failure.

### Secondary

| Metric | Definition |
|---|---|
| Execution accuracy | P(edit matches the operation spec \| correct identification) |
| Collateral rate | P(elements beyond the target modified) |
| Strict accuracy | identification ∧ correct execution ∧ no collateral |
| Loose accuracy | identification ∧ correct execution |
| Abstention rate | P(`ABSTAINED`) |
| Well-formed rate | 1 − P(`MALFORMED`) |
| Truncation rate | P(response hit the token limit) |
| Mean elements modified | the hedging measure |
| Multi-edit rate | P(more than one element modified) |

Identification accuracy is reported **both unconditionally and conditional on well-formed
output**. Both are needed: the unconditional number is what a user experiences, the
conditional number isolates identification from format compliance.

### Diagnostic

| Metric | What it tests |
|---|---|
| Selection-position distribution | **whether `1/K` is guessing or a fixed policy** |
| Selection-rank distribution | off-by-one errors in ordinal predicates |
| Selection-quadrant distribution | corner priors in spatial predicates |
| Enhancement fact-accuracy | whether the supplied facts were correct |
| Tokens / latency per case | cost of the enhancement |

The selection-position distribution matters more than it looks. A model that always edits the
first ambiguity-set element achieves a *marginal* rate of exactly `1/K` under randomized
document order — numerically identical to guessing, behaviourally nothing like it. Matching
the null is therefore not evidence of guessing unless the error distribution is also uniform.
`1/K` is treated as a hypothesis to test, not an assumption.

## 5. Reporting unit

**Per predicate**, not only per family. Families are heterogeneous:

- `largest` / `smallest` are single-pass argmax/argmin.
- `second_largest` / `third_largest` require a full ordering plus a correct offset — a
  categorically harder operation with a known failure mode.
- `leftmost` is a 1-D argmin; `top_left` is a 2-D compound predicate.

A family-level average is a weighted mean over tasks of very different difficulty, with
weights set by an arbitrary design choice. Family-level numbers are reported as a summary;
per-predicate numbers are the finding.

## 6. Inference (frozen)

- **Resampling unit: the SVG**, not the case. Instructions sharing an SVG share a layout and
  are not independent; case-level resampling would understate variance.
- **Interval estimation:** cluster bootstrap over SVGs, seeded, iteration count in config.
  Reported with the caveat that coverage is imperfect at ~30 clusters and at proportions near
  the `1/K` floor.
- **Hypothesis testing:** paired **cluster-level permutation test** on per-SVG deltas
  between arms. With ~30 clusters this is better behaved than a bootstrap, and pairing is
  valid because arms see byte-identical cases.
- **Multiplicity:** one primary comparison is pre-registered (paired Δ identification
  accuracy, enhanced vs permuted, per family). Everything else is labelled secondary or
  exploratory.
- **Minimum detectable effect** is computed and reported **before** results, so a null result
  is interpretable rather than ambiguous.

## 7. Replicates and decoding

Replicates are only meaningful under stochastic decoding: at temperature 0 they are identical
calls, and reporting three of them would imply a robustness that does not exist. The frozen
policy is therefore stated in the config and in `adr/0008`, and it is decided **before** the
baseline runs. Whichever is chosen, per-case success *rate* is the analysis unit; replicate
count never enters `n`.

## 8. Uniqueness against the full element set

Predicate uniqueness is asserted over **every** element in the document, not only the
ambiguity set. A distractor that outranks the intended target on the instruction's predicate
would make the instruction genuinely ambiguous to a human, and a model picking the distractor
would be marked wrong while being arguably right.

## 9. What this design cannot show

Recorded here, before results, so it cannot be quietly dropped later:

1. Nothing about models in general — the corpus is synthetic and the model count is small.
2. Nothing about real-world SVG editing — opaque `d` tokens do not occur in the wild. The
   `legible` arm partially addresses this; it does not remove the limitation.
3. Nothing about generality of the enhancement beyond the predicates it was designed
   against. The enhancement is blind to individual instructions but not to the task
   distribution: choosing to emit centroid and area is itself informed by knowing the
   families under test.
4. Nothing about whether an LLM is the right tool — a deterministic solver scores 100% on
   this task. The benchmark measures in-context reference resolution, not whether that is the
   best engineering choice.
5. Corpus difficulty is filtered by separability margins. The corpus is easier than arbitrary
   layouts, by an amount reported via the rejection log and margin-stratified accuracy.
