# Observations

**Phase II log. Currently empty - no model has been run.**

This file exists before there is anything to put in it, deliberately. Creating it after
seeing results would be creating it under their influence.

---

## What this is, and what it is not

[`FAILED_ASSUMPTIONS.md`](FAILED_ASSUMPTIONS.md) is the Phase I log. Its entries are
about the **instrument**, and every one ends in a change: a renamed field, a replaced
statistic, a recalibrated threshold. That was correct while the instrument was being
built.

This is the Phase II log. Its entries are about **reality**, and none of them end in a
change. The instrument is frozen at `instrument-freeze-v1`.

**There is no `Resolution` field in this file, and no `Fix` field.** That absence is the
point. An entry has nowhere to record a change to the instrument, because after the tag
there is nowhere to make one - see [`RESULTS.md`](RESULTS.md).

If an observation genuinely reveals an instrument bug, it does not belong here. It
belongs in `CHANGELOG.md` as a disclosed amendment, under the rule that it must affect
every arm identically and would have been made the same way had the arms come out
reversed.

---

## Interpretation is not explanation

Two different things, kept in separate fields because sliding from one to the other is
easy and does real damage.

**Interpretation** - what the numbers imply for the claims. Constrained by the data.
> "Baseline identification accuracy is 0.183, against a per-case reference of 0.1852.
> Consistent with C1: the corpus is under-determined."

**Explanation** - why the numbers might have come out that way. Speculative, mechanistic,
and *not licensed by this experiment*.
> "The model may be defaulting to the first candidate when it cannot resolve a reference."

An explanation is a hypothesis for future work. It is not a finding. Recording it in the
same breath as an interpretation is how "the model probably struggled because X" becomes
a claim nobody measured. Every entry keeps them apart, and the explanation field is
allowed to be empty - often it should be.

---

## Entry format

```
## O-000  <short title>

**Observed**        the measurement, with its uncertainty
**Pre-registered**  what CLAIMS.md said would falsify or support the relevant claim
**Interpretation**  what this implies for that claim, and nothing more
**Explanation**     candidate mechanisms, explicitly marked speculative. May be empty.
**Action**          almost always "none". Anything else must cite RESULTS.md.
```

`Pre-registered` is a required field so that every observation is read against what was
committed in advance, rather than against what seems reasonable in hindsight.

---

## The three observations this project exists to record

Pre-registered in `RESULTS.md`, listed here so the log has its shape before it has its
content.

| # | Observation | Tests |
|---|---|---|
| **O-001** | `baseline` vs the per-case `1/K` reference of **0.1852** | C1 - is the corpus genuinely under-determined? |
| **O-002** | `enhanced` vs `baseline` | Necessary but not sufficient for C3 |
| **O-003** | `enhanced` vs `permuted` | **C3 - the central claim** |

Plus diagnostics that are observations in their own right, not footnotes: the
selection-position distribution, the abstention rate per arm, the malformed and
truncation rates per arm, and the `ceiling` residual.

---

## Log

## O-001  Baseline sits well below the random-selection reference

**Observed**

`main-baseline`, `qwen2.5-coder:3b`, n = 180, one replicate.

| | |
|---|---|
| **Identification accuracy** | **0.0444** (8/180) |
| Pre-registered `1/K` reference | 0.1852 |
| Malformed | 0.0000 |
| Abstained | 0.0000 |
| `NO_EDIT` | 0.444 (80/180) |
| `WRONG_TARGET` | 0.511 (92/180) |
| Identification, spatial | 0.0222 (2/90) |
| Identification, ordinal | 0.0667 (6/90) |

Diagnostics (FR-7.6, pre-registered):

- The model changed nothing in **80/180** cases.
- Of 107 elements it did touch, **60.7%** were ambiguity-set members and **39.3%** were
  distractors - elements that were never candidates.
- Conditional on touching a candidate at all: **8/65 = 0.123**, against the 0.185
  reference. About 1.3 SE below, i.e. within noise of chance.
- Hedging is rare: 91 cases changed exactly one element, 9 changed more.

**Pre-registered**

`CLAIMS.md` states C1 is falsified by baseline accuracy *substantially above* the
per-case `1/K` reference, or by a non-uniform selection-position distribution. Neither
is observed. Corpus-side target positions were tested against the uniform-within-K
expectation: chi-square 9.14 on 6 df, p = 0.17 - consistent with uniform.

**Interpretation**

C1 holds. There is no evidence of leakage: the baseline does not beat chance, and the
frozen corpus places targets uniformly across document positions, so no positional
policy could beat chance either. The corpus is under-determined as designed, and the
baseline arm has done its job as a manipulation check.

The result is *below* rather than *at* chance because the `1/K` reference assumes a model
that both acts and confines itself to the candidate set. This model frequently does
neither. Restricted to cases where it picked a candidate, identification is
indistinguishable from chance.

**Explanation** *(speculative; not licensed by this experiment)*

Two candidate mechanisms, neither measured. The model may be unable to act under this
degree of under-determination and default to echoing the input, which would explain the
44% no-edit rate. And it may not restrict attention to the same-fill candidate set,
which would explain 39% of its edits landing on distractors. Distinguishing these would
need an experiment this one was not designed to run.

**Action**

None. Proceed to `permuted` and `enhanced`.

## O-002  Supplying the missing geometry produced no measurable improvement

**Observed**

All three arms, n = 180 each, 30 clusters, one replicate. Cluster bootstrap over SVGs,
95% interval.

| arm | identification | strict | collateral | NO_EDIT | malformed | abstained |
|---|---|---|---|---|---|---|
| `baseline` | **0.0444** [0.0167, 0.0778] | 0.0222 | 0.533 | 0.444 | 0 | 0 |
| `permuted` | **0.0444** [0.0167, 0.0778] | 0.0389 | 0.478 | 0.483 | 0 | 0 |
| `enhanced` | **0.0444** [0.0167, 0.0778] | 0.0389 | 0.483 | 0.478 | 0 | 0 |

Paired cluster-level permutation, 10,000 iterations:

| comparison | difference | p |
|---|---|---|
| `enhanced` − `baseline` | **+0.0000** | 1.000 |
| `enhanced` − `permuted` | **+0.0000** | 1.000 |
| `permuted` − `baseline` | **+0.0000** | 1.000 |

Minimum detectable effect at p < 0.05: **0.0289**.

The context is demonstrably reaching the model. Prompts differ in 180/180 cases between
every arm pair; responses differ in 56/180 (baseline vs enhanced) and 27/180 (enhanced
vs permuted). `enhanced` and `permuted` prompts are token-identical at a median of 817
tokens, against 535 for `baseline`.

**Pre-registered**

`RESULTS.md` names `enhanced > baseline` as **necessary but not sufficient** for C3. It
is not satisfied: the difference is zero.

**Interpretation**

Supplying the geometric facts the markup does not encode produced **no measurable
improvement in identification** for this model on this corpus. The design would have
detected a difference of 0.029; the observed difference is 0.000.

The zero is *mechanical*, not remarkable: both arms identified exactly 8 cases and every
cluster holds exactly 6, so the mean per-SVG delta is forced to (8−8)/180. Nothing should
be read into its exactness. Equally, `p = 1.000` is degenerate - with an observed
difference of zero, every permutation is at least as extreme. **The minimum detectable
effect, not the p-value, is what bounds this result.**

The premise of the instrument was that the markup lacks the information the instruction
refers to. That premise holds - C1 was confirmed at O-001. What does not follow, and what
this observation shows, is that supplying the information helps. For this model the
binding constraint is evidently something other than the missing facts.

**Explanation** *(speculative; not licensed by this experiment)*

The model declines to edit at all in 44-48% of cases in every arm, and that rate barely
moves when the geometry is supplied. A model that cannot reliably perform the edit
mechanics would show exactly this pattern regardless of what it knows about which element
to target. Distinguishing "cannot use the facts" from "cannot perform the edit" would
require an ablation this design does not contain - for instance, an arm naming the target
element by id outright. That is not the `ceiling` arm, which supplies predicate labels
rather than the answer, and it was not run.

**Action**

None.

## O-003  C3 not supported: its prerequisite did not occur

**Observed**

`enhanced` − `permuted` = **+0.0000**, p = 1.000, 30 clusters, 180 paired cases.

`permuted` and `enhanced` identified **exactly the same 8 cases**. `baseline` overlaps 7
of those 8; the union across all three arms is 9 cases.

**Pre-registered**

C3 - *any improvement from added context is information, not format* - is the central
claim, and `enhanced` vs `permuted` is its pre-registered test.

**Interpretation**

**C3 was not supported, because its prerequisite did not occur.** The comparison asks
which of two components explains an improvement; the treatment effect was zero, so there
is no quantity to decompose. A zero difference between `enhanced` and `permuted` is
exactly what one expects when both equal `baseline`.

This is a scientific dependency, not a methodological failure. The experiment *did* test
the treatment. The treatment effect was zero. C3 is conditional on a non-zero effect, and
that condition was measured and not met.

This is not the outcome `RESULTS.md` anticipated. It listed two: the gain is information
(`enhanced > permuted`), or the gain is format (`enhanced ≈ permuted` with both above
baseline). The third case - no gain at all - resolves the prerequisite negatively rather
than answering the decomposition question.

That `permuted` and `enhanced` identified the identical case set is worth recording. It
means shuffling the geometric values between elements changed nothing whatsoever about
which element the model acted on. Under a model that used the numbers, permutation should
have hurt.

**Explanation** *(speculative)*

Consistent with the model not consuming the numeric content of the context at all. Not
established, and not separable here from the possibility that it consumes them but is
blocked downstream by the edit mechanics.

**Action**

None. The instrument is not at fault and nothing about it changes. The reportable finding
is O-002 - no effect - with C3 recorded as untestable on this corpus and this model.

## O-004  C4 and C5 are vacuous for this model

**Observed**

- Execution given identification: **1.000** in all three arms. Whenever the model acted
  on the intended element, it performed the requested edit correctly.
- Abstention: **0/180** in all three arms. The model never explicitly declined.
- Malformed: **0/180** in all three arms.

**Pre-registered**

`CLAIMS.md` states C4 is falsified if identification and execution move together such
that the decomposition captures nothing, and C5 if abstention is near zero in every arm,
making the class vacuous for this model.

**Interpretation**

Both conditions are met. The identification/execution split (ADR-0006) captured nothing
here because execution never failed given identification - the decomposition was correct
to build, since it could have mattered, but on this data it separated nothing. The
abstention class (ADR-0008) is empty: this model never says it cannot tell, it simply
returns the document unchanged, which the frozen rules score as `NO_EDIT` rather than
`ABSTAINED`.

That scoring rule was fixed before any output existed and is not revisited. It remains
the right rule - silence is not a claim about insufficient information - but it means the
44-48% `NO_EDIT` rate carries behaviour that a differently-drawn boundary might have
called abstention. Stated so a reader can judge that boundary for themselves.

Malformed at 0/180 confirms A1 and vindicates ADR-0011: had the 1.5b model been used, a
third of every arm would have been unparseable.

**Action**

None.

---

**Note on the pre-registration itself**

The C1 falsifier was imprecisely worded. It said a non-uniform *selection*-position
distribution "implies leakage". It does not: a model-side positional prior is only
exploitable if the *corpus* places targets non-uniformly, which is a separate and
corpus-side property. The right test - and the one applied above - is the corpus-side
one, which the frozen `distributions.json` supports because it was sealed before any
model ran.

The model's own selection does show a weak edge preference once normalised by
opportunity (pick rate 0.028-0.167 per slot against a uniform 0.064), but with 65 picks
this is weak evidence, and it cannot produce above-chance accuracy against a uniformly
positioned corpus. Recorded, not acted on.
