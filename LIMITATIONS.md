# Limitations

**Status: pre-results.** This document was written *before* any experiment ran, from the
design review, so that the known weaknesses could not be quietly discovered after the fact.
It will be **expanded** against actual results, never softened.

---

## What this project cannot show, by construction

These do not depend on how the numbers come out.

### 1. Nothing about language models in general
A small number of small local models, one quantization each, on one synthetic corpus. Any
sentence beginning "LLMs cannot…" is unsupported by this data.

### 2. Nothing about real-world SVG editing
Ambiguity-set path data is replaced by opaque `{{GEOM_…}}` tokens. **No SVG in the wild looks
like this.** A model may degrade on such markup for reasons unrelated to reference
resolution — unfamiliar format, repair attempts, refusal. The `legible` arm (real path data)
partially separates these, but it does not make the redacted corpus realistic.

### 3. The core comparison is close to tautological
Information is deliberately removed, then restored, and performance recovers. That is a
manipulation check, not a discovery. The informative content is *magnitude*, the *per-predicate
split*, the *residual errors*, and the *cost* — not the direction.

### 4. The enhancement is conditioned on the task distribution
Instruction-blindness is enforced by a type signature, so no individual instruction can leak
into the context. But choosing to emit **centroid** and **area** is itself informed by knowing
that the tested families are spatial and ordinal-size. Those are close to the sufficient
statistics for exactly these predicates. The method is blind to the *instruction*, not to the
*benchmark*.

### 5. A deterministic solver would score 100%
Parse, render, measure, edit. The benchmark measures in-context visual-reference resolution —
it does not argue that a language model is the right tool for this job.

### 6. No vision-language baseline
The obvious alternative is to render the SVG and show a VLM the image. Not run, for compute
reasons. If a small VLM handles this trivially, the text-only framing is much less
interesting. This is addressed in discussion only, which is weaker than measuring it.

### 7. The corpus is filtered toward easiness
Separability margins and non-overlap constraints are rejection sampling: layouts where the
answer is contested are discarded. The corpus is therefore **easier than arbitrary SVG**. The
rejection log and margin-stratified accuracy quantify this; they do not remove it.

### 8. Inference rests on ~30 clusters
Instructions sharing an SVG are not independent, so the effective sample size is the number of
SVGs, not the number of cases. Thirty is genuinely few and intervals will be wide. **This
cannot be fixed within the assignment's 20–30 SVG budget**, so the response is a narrower
claim rather than a better estimator. The minimum detectable effect is reported before
results, so that a null outcome can be distinguished from an underpowered one.

### 9. Per-predicate cells are small
Per-predicate reporting is the right unit (families are heterogeneous), but the resulting
cells are small. Those numbers are descriptive, not confirmatory.

### 10. Ground truth is machine-defined
"Top-left" is operationalized as nearest-corner-centroid ∧ in-quadrant. That is a reasonable
model of human semantics, not a validated one. Canonical area is pixel coverage, which is not
the same as *perceived* size — human size judgement is compressive and sensitive to
elongation. A human-agreement sample measures the residual disagreement; it does not
eliminate it.

### 11. One prompt template family
Prompt phrasing is a first-order effect on structured-output tasks. A small number of
templates are tested; the result remains conditional on them.

### 12. Operations are restricted to what can be scored crisply
Recolor, stroke, delete, rotate. Chosen because each is checkable by structural diff. This is
a convenience of measurement, not a representative sample of SVG edits.

---

## Threats that are actively checked (and how)

These could invalidate the result, so they are tested rather than argued:

| Threat | Check |
|---|---|
| Position leaks via attributes | Audit forbids `transform`/`x`/`cx` on ambiguity members |
| Size leaks via token length | Fixed-length tokens, asserted |
| Document order correlates with the answer | Corpus-wide rank-correlation check |
| The enhancement conditions on the instruction | Type signature + byte-identical-context check |
| The enhancement hands over the answer | Vocabulary check against instruction templates |
| Improvement is format, not information | The `permuted` arm |
| Improvement is format compliance | Malformed/truncation rate reported per arm |
| "Baseline is at chance" is actually a fixed policy | Selection-position distribution |
| A distractor outranks the intended target | Uniqueness asserted over the full element set |
| Scoring favours one arm | Arm-blind scorer; fixtures written pre-registration |

---

## Completed after results

- **Rejection rate and margin distribution.** 124/360 predicate slots refused: 13.1%
  distractor outranks target, 11.4% margin too small, 9.4% definition disagreement, 0.6%
  quadrant. Corpus is easier than arbitrary layouts by that amount.
- **Baseline error distribution.** Corpus target positions uniform-within-K
  (χ² = 9.14, 6 df, p = 0.17). Model selection shows a weak edge preference
  (0.028–0.167 per slot vs uniform 0.064, 65 picks) which cannot help against a
  uniformly positioned corpus.
- **Malformed and truncation rates.** 0/180 and 0/180 in every arm. A1 satisfied.
- **`enhanced` − `permuted` gap.** +0.0000. See §14 below.
- **`ceiling` residual.** Not run — the three-arm scope was chosen before the baseline.
- **Human-agreement rate.** Not run. Operationalization invariance remains a proxy.
- **Scoring amendments after the tag.** None. One *prompt* amendment (template 1.0 → 1.1,
  a placeholder-example typo), disclosed in `CHANGELOG.md`, affecting all arms
  identically, made before the baseline run.

---

## Limitations the results introduced

These could not have been written in advance, because they depend on what happened.

### 13. C4 and C5 turned out vacuous, so two design decisions are untested

Execution given identification was **1.000** in every arm, and abstention was **0/180**.
The identification/execution split (ADR-0006) and the abstention class (ADR-0008) were
both correct to build — each could have mattered and would have been unrecoverable
afterwards — but neither separated anything on this data.

This means the repository **cannot claim** those decisions improved the measurement here.
It can only claim they were available and did not fire. A reader who thinks the
abstention boundary is drawn wrong has no counter-evidence from this run: the model never
said it could not tell, it simply returned the document unchanged (44–48% of cases),
which the frozen rules score `NO_EDIT`.

### 14. The central claim is undetermined, not answered

C3 asks whether an improvement comes from information or format. The treatment effect was
zero, so the decomposition has no quantity to operate on. **This experiment therefore
provides no evidence either way about C3**, and the `permuted` arm — the repository's
main methodological contribution — was never exercised in the role it was built for.

That is worth stating plainly: the control was designed to distinguish two explanations
of a positive effect, and no positive effect occurred. Its value here is confined to
demonstrating that the format-matched comparison *can* be constructed and audited, not to
resolving the question it was built to resolve.

### 15. The most informative follow-up was deliberately not run

An arm naming the target element by id outright would separate *"cannot use the supplied
facts"* from *"cannot perform the edit"*. That is the obvious next experiment and would
sharpen H3 considerably.

It is **not** in the pre-registered design. Adding it after seeing a null would be
designing toward an explanation for a result already observed, which is exactly what
`RESULTS.md` exists to prevent. Recorded as future work rather than run.

### 16. One model, and the null may be model-specific

`qwen2.5-coder:3b` was selected because `qwen2.5-coder:1.5b` produced 33% unparseable
output (ADR-0011). Both are small. Nothing here bears on whether a larger model would
show an effect, and the observed behaviour — declining to edit in nearly half of all
cases — may be characteristic of models at this scale rather than of the task.

### 17. Reported effects are bounded, not excluded

The minimum detectable effect is **0.0289**. An improvement of 1–2 percentage points
would not have been detected. The claim is that no effect *larger than about three
points* occurred, not that the effect is exactly zero.
