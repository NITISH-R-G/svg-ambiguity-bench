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

## To be completed after results

- [ ] Observed rejection rate and margin distribution
- [ ] Whether the baseline error distribution was uniform
- [ ] Malformed and truncation rates per arm
- [ ] `enhanced` − `permuted` gap and its interpretation
- [ ] Residual error taxonomy from the `ceiling` arm
- [ ] Human-agreement rate on the predicate registry
- [ ] Any scoring amendment made after the `pre-registration` tag
