# Study V3 - model generality, and the first real test of the control

**Status: PRE-REGISTERED. No V3 model output has been observed.**

Written before any additional model is run. The predictions and decision rules below bind
the interpretation. Editing them after results exist is an amendment and must be
disclosed as one, with the pre-change text retained.

---

## Two questions, and the second is the important one

**Q1 - generality.** V1 and V2 used one model. Does the pattern - context does not improve
identification, but naming the target does - hold across model scale and model family, or
is it a property of `qwen2.5-coder:3b`?

**Q2 - does the control ever fire?** This is the one that matters, and it has been open
since the project began.

The format-matched control exists to decompose a positive effect into an information
component and a format component. V1 produced **no effect at all**: `baseline`,
`permuted` and `enhanced` scored identically, and `permuted` and `enhanced` identified the
*same eight cases*. On this evidence the model did not read the geometry table
imperfectly - it did not use it. With a treatment effect of exactly zero there was nothing
to decompose, so the repository's central methodological contribution has never been
exercised in the role it was built for. `LIMITATIONS.md` section 14 says so.

That limitation is not fixable by better documentation, more tests, or another domain. It
is fixable by **finding a model that actually uses the supplied geometry**. If any model
scores `enhanced` above `baseline`, the decomposition becomes available for the first
time, and the question the whole instrument was built to answer becomes answerable.

V3 is therefore not primarily a generalisation study. It is an attempt to falsify the
implicit assumption that no model uses this information.

## Design

Four conditions per model - the three V1 arms plus the V2 `named_id` condition - over the
identical frozen corpus, 180 cases, 30 clusters. Nothing about the instrument changes:
same corpus hash, same prompt template, same scorer, same metrics, same cluster unit,
same greedy decoding, one replicate.

| model | family | params | role |
|---|---|---|---|
| `qwen2.5-coder:1.5b` | Qwen coder | 1.5B | scale, below the reference |
| `qwen2.5-coder:3b` | Qwen coder | 3B | **reference - already measured in V1/V2** |
| `qwen2.5-coder:7b` | Qwen coder | 7B | scale, above the reference |
| `llama3.2:3b` | Llama | 3B | family, size-matched to the reference |

Two axes cross the reference point: **scale** at fixed family (1.5B / 3B / 7B) and
**family** at fixed scale (Qwen-coder 3B vs Llama 3B). Four models is not a survey and is
not claimed to be one; it is the smallest design that can distinguish "property of this
checkpoint" from "property of models of roughly this size".

The V1/V2 results for `qwen2.5-coder:3b` are reused unchanged. They are not re-run, and
nothing measured here may alter them.

---

## Primary outcome

For each model, the **information effect**:

```
information_effect = accuracy(enhanced) - accuracy(permuted)
```

This is the quantity the format-matched control exists to isolate. It is not
`enhanced - baseline`, which confounds information with format. Reported per model with a
paired cluster-level permutation test over the 30 SVGs and the design's MDE.

## Pre-registered decision rules

Fixed now.

**On Q2 - does the control fire?**

| Outcome | Condition | Conclusion |
|---|---|---|
| **FIRES** | any model has `enhanced - permuted` exceeding that model's MDE, in the positive direction | **The control is exercised for the first time.** The information component is separated from the format component in a real measurement. `LIMITATIONS.md` 14 is retired and C3 becomes testable |
| **PARTIAL** | some model has `enhanced - baseline` above MDE but `enhanced - permuted` within MDE | **The gain is format, not information.** This is the failure mode the control was built to catch, and catching it is a positive result for the method even though it is a negative result for context augmentation |
| **SILENT** | no model shows any effect above MDE on either comparison | The control remains unexercised across four models. `LIMITATIONS.md` 14 stands, and the finding strengthens from "this model ignored the geometry" to "four models across two families and three scales ignored it" |

**PARTIAL deserves emphasis.** It is the outcome in which the method demonstrably earns
its existence: a naive two-arm study would have reported "supplying geometry helps" and
been wrong. If PARTIAL obtains, that is the strongest available evidence *for the
methodology*, and it must be reported as prominently as FIRES would have been.

**On Q1 - generality.** For each model, using the V2 bands:

| Pattern | Condition |
|---|---|
| **Replicates** | `named_id >= 0.50` and all three V1 arms within their mutual MDEs |
| **Diverges** | any model where `named_id < 0.50`, or where a V1 arm separates |

## Predictions, recorded before running

I was wrong about V2 - I predicted band C and got band A. That is on the record, and it is
the reason these are worth writing down again.

1. **Q2 will be SILENT or PARTIAL, most likely SILENT.** I expect none of these models to
   use the geometry table. Confidence: moderate-low. The 7B model is the most likely to
   break this, and if any single result surprises me it will be that one.
2. **`named_id` will exceed 0.50 for 3B and 7B, and may fall below it for 1.5B.** The
   1.5B model was measured at Step 10 as producing 4/12 unparseable responses, which is
   why it was not selected; execution capability at that scale is genuinely uncertain.
3. **`llama3.2:3b` will show the same pattern as `qwen2.5-coder:3b`** - high `named_id`,
   flat V1 arms. Confidence: low. It is not code-tuned, so its `named_id` may be
   substantially lower.

If prediction 1 is wrong and the control fires, that is the best outcome this project can
have, and I will have been wrong twice in a row in the project's favour - which is worth
stating now precisely because it is the pattern that would otherwise look like hindsight.

## Falsifiers

- **Malformed rate above ~0.10 for any model.** At that point the measurement is
  substantially about format compliance rather than reference resolution, and that
  model's numbers are reported but excluded from the pooled conclusion. The threshold is
  set now, not after seeing which model is worst.
- **`named_id` below `baseline` for any model.** Supplying strictly more information
  should not perform worse; that pattern indicates a harness fault, not a finding.
- **Any V1 arm for `qwen2.5-coder:3b` differing from its committed value.** The 3B results
  are reused, not re-run; if a recomputation disagrees, the pipeline has drifted and
  everything here is void.

## Analysis plan

- Per model: accuracy per condition with 95% cluster bootstrap over 30 SVGs, 10,000
  resamples, seeds as in `configs/base.yaml`.
- Per model: paired cluster permutation for `enhanced - permuted`, `enhanced - baseline`,
  `permuted - baseline`, `named_id - enhanced`. 10,000 permutations. MDE reported
  alongside every comparison.
- **No pooling across models into a single headline number.** Four models is too few, and
  they are not a sample from any population. Each is reported separately.
- Multiplicity: four models times four comparisons is sixteen tests. The primary outcome
  is `enhanced - permuted` only; the rest are secondary and labelled as such. No
  correction is applied to the primary because there is one per model and each is
  reported with its interval rather than as a significance verdict.

## What may and may not change

**May change:** a new results document; `LIMITATIONS.md` 14 if the control fires;
`VALIDITY.md` external-validity row; `README.md` headline if the pattern replicates or
breaks; `CLAIMS.md` outcome for C3.

**May not change:** the corpus, scoring rules, predicates, leakage checks, evaluation
rules, the V1 arm definitions, or any committed V1/V2 number. `instrument-freeze-v1` and
`study-v2-preregistration` are not superseded.

The operational test applies unchanged:

> Would this change have been made identically had the result come out the other way
> around?

## Registration

```
tag  study-v3-preregistration
```

Tagged before any V3 model output exists. Model weights may be downloaded before the tag;
downloading is not observation.
