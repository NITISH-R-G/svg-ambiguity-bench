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

*No observations recorded. No model has been run.*
