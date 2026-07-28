# Design review — findings and disposition

**Date:** 2026-07-28, before implementation. Adversarial review of the v1 design, conducted
as "try to reject this at a top conference".

This is the record of what the review found and what was done about it. Findings that changed
the design became ADRs; findings that could not be fixed within the assignment's constraints
became entries in `LIMITATIONS.md`.

---

## Findings that changed the design

| # | Finding | Disposition |
|---|---|---|
| 1 | **The treatment changes two things at once.** The enhanced prompt adds geometric facts *and* an enumerated element list. Enumeration alone could move the score with no geometric content, so "supplying geometry helps" and "supplying a list helps" were indistinguishable. | `permuted` arm added and made **blocking**. Primary comparison is now `enhanced` vs `permuted`. → ADR-0009 |
| 2 | **Abstention was scored as failure.** Declining to guess on a provably underdetermined instruction is correct behaviour; pooling it with `NO_EDIT` meant the metric rewarded confident guessing while the project's motivation was that models hedge. | `ABSTAINED` promoted to its own outcome class. → ADR-0008 |
| 3 | **Strict accuracy conflates three capabilities** — identification, execution, non-collateral — and the research question is about the first only. | Identification accuracy made primary; strict demoted. → ADR-0006 |
| 4 | **Families are heterogeneous.** `largest` is an argmax; `third_largest` needs a full ordering plus an offset. A family average is a weighted mean over different tasks with arbitrary weights. | Reporting unit changed to **predicate**. |
| 5 | **`1/K` was assumed, not tested.** A model that always edits the first candidate achieves a marginal rate of exactly `1/K` under shuffled order — numerically identical to guessing, behaviourally different. Premise validation depended on this distinction. | Selection-position distribution added as a diagnostic; `1/K` treated as a hypothesis. |
| 6 | **Bootstrap coverage is poor at ~30 clusters**, worst near the floor proportions the baseline arm will occupy. | Paired cluster-level **permutation** test for inference; bootstrap retained for intervals only, with the caveat stated. → ADR-0007 |
| 7 | **Redaction is an unmeasured confound.** Opaque tokens are out-of-distribution markup; baseline failure mixes ambiguity with format unfamiliarity. | `legible` arm (real path data) added. → ADR-0009 |
| 8 | **Distractors could outrank the intended target**, making an instruction genuinely ambiguous while the model is marked wrong. Uniqueness was only asserted within the ambiguity set. | Uniqueness now asserted over the full element set. |
| 9 | **Malformed rates will differ between arms** (longer prompts, more structure), so part of any improvement is format compliance. | Malformed and truncation reported per arm; identification reported both unconditionally and conditional on well-formed output. |
| 10 | **Replicates and temperature were unresolved.** At temperature 0, replicates are identical calls. | ADR-0010 opened as **pending**, with a resolution rule pre-committed to a smoke-test measurement. |
| 11 | **The framing was near-tautological** — remove information, restore it, observe recovery. | Contribution reframed: the enhanced arm is the benchmark, the baseline is a manipulation check. The baseline arm has no dynamic range and cannot discriminate between models. |
| 12 | **Blindness by type signature blinds the code, not the designer.** Emitting centroid and area is informed by knowing which predicates are tested. | Stated as a limitation rather than claimed away. → ADR-0005, `LIMITATIONS.md` §4 |

## Findings accepted as limitations

Not fixable within a 20–30 SVG budget and one small model. The response is a narrower claim,
stated up front rather than discovered in review:

- ~30 clusters is a thin basis for inference → minimum detectable effect reported *before*
  results, so a null is interpretable.
- Single synthetic corpus → no generalization claim.
- No VLM baseline → discussion only; recorded as the most valuable single addition.
- A deterministic solver scores 100% → the benchmark measures in-context resolution, not
  whether an LLM is the right tool.
- Rejection sampling makes the corpus easier than arbitrary layouts → rejection log published,
  accuracy stratified by margin.
- Rasterized coverage is not *perceived* size → human-agreement sample measures the residual.

## Findings deferred

Recorded in `docs/BACKLOG.md`: format ablations, K sweep, distractor ablation, perceptual area
weighting, adversarial phrasing, multiplicity correction.

---

## The one-line summary

The infrastructure was sound; the experiment had a confounded treatment. Fixing that cost one
control arm. Everything else was either a reporting change or an honest limitation.
