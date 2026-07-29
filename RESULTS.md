# Results discipline

**Status: not yet sealed.** The `pre-registration` git tag does not exist yet (it is
placed after Step 9, per [`DESIGN_FREEZE.md`](DESIGN_FREEZE.md)). This document states
the rule that binds from that tag onward, written now, before any model has been run,
so it cannot be shaded by a result nobody has seen yet.

The reason this file exists separately from `DESIGN_FREEZE.md`'s pre-registration
section: that section is about the *design*. This one is about *me*, six months from
now, looking at a disappointing number and finding a reason the scoring rule was
slightly wrong. This is the file that stops that version of me.

Stated more precisely, and this is the whole idea in one sentence:

> **Pre-registration transfers epistemic authority from your future self back to your
> past self.** Your past self knew less — and is in a better position to write the rules
> precisely *because* of that. A rule written when it is cheap binds a version of you for
> whom it will be expensive.

That is a stronger claim than "pre-registration prevents p-hacking". It is not a defence
against dishonesty; it is a defence against the ordinary, sincere reasoning that becomes
available only after you have seen the answer.

---

## The rule

> **Nothing discovered after the `pre-registration` tag may change the dataset, the
> scoring, the predicates, the leakage checks, or the evaluation rules.**
>
> The only exception: a bug demonstrably affecting every arm identically may be fixed,
> as a disclosed amendment, with the pre-fix numbers retained in `CHANGELOG.md` per
> `DESIGN_FREEZE.md`'s amendment procedure.
>
> **Everything else becomes Discussion, not a patch.**

A surprising result is evidence. A surprising result is not a bug report against the
instrument, unless the instrument can be shown to be wrong *for a reason that has
nothing to do with which arm produced the surprise*.

### What "becomes Discussion" means concretely

If, after seeing results, something looks off — a predicate that seems to favor one arm,
a margin that seems too tight, an operation that seems to score unfairly — the response
is:

1. Write it into the final report as a named limitation or an open question.
2. Optionally: note it in `docs/BACKLOG.md` as a v2 experiment.
3. **Do not** edit `svgbench.groundtruth`, `svgbench.evaluation`, `svgbench.metrics`, the
   predicate registry, or any frozen config to make the number look different.

The difference between an amendment and a rationalization is whether the fix is blind to
which arm benefits. "The scorer had an off-by-one that dropped the last character of
every response, in every arm" is an amendment. "The margin threshold seems too strict
now that I see `enhanced` underperforming" is not, however reasonable it sounds in the
moment — see `FAILED_ASSUMPTIONS.md` FA-007 for what "the threshold seems off" actually
looked like *before* results existed, which is the only time it's a legitimate finding.

---

## The three observations that matter

Everything built so far exists so that these three comparisons, in this order, are
interpretable. Restated here as a decision procedure rather than scattered across
`CLAIMS.md`'s per-claim falsification criteria, because at analysis time I want a
sequence to follow, not a table to search.

### 1. `baseline ≈ 1/K` — the precondition

Tests **C1**: is the corpus actually under-determined?

- **If baseline sits substantially above the per-case 1/K reference**, or the
  selection-position distribution is non-uniform (§ FR-7.6): **stop**. Do not proceed to
  interpret `enhanced` or `permuted`. Find the leak. This almost certainly means
  something built in Steps 3-5 has a hole - the same category of thing FA-001 through
  FA-005 found, except found after the tag, which is a materially worse place to find it.
- **If baseline sits at the floor**: proceed. This is a manipulation check passing, not
  a result - see `README.md`'s framing. It has no publication value on its own.

### 2. `enhanced > baseline` — necessary, not sufficient

Tests whether the treatment does anything at all.

- Necessary: if this fails, there is nothing to explain and no reason to look at
  `permuted`.
- **Not sufficient**: passing this alone does not support the central claim. An
  enhanced prompt that merely lists elements (no geometry, just an enumeration) could
  pass this comparison too. This is exactly the confound ADR-0009 exists to rule out.

### 3. `enhanced > permuted` — the actual claim

**This is C3.** This is the number the whole repository was built to make trustworthy.

- If it holds: the gain is information, not format. Report the effect size, the
  per-predicate split, and the residual gap against `ceiling` (which separates remaining
  reasoning failure from remaining information failure).
- **If `enhanced ~= permuted`**: this is not a failed experiment. It is the finding.
  Report it as the headline: the improvement from the enhancement is attributable to
  prompt format/structure, not to the geometric information it carries. This is the
  outcome the `permuted` control was built to make detectable, and detecting it is the
  method working, not failing.
- If `permuted > enhanced`: report it and investigate why, but do not silently drop the
  comparison. An enhancement that does *worse* than a content-free version of itself is
  itself a finding worth stating plainly.

None of these three steps involves touching code. They involve reading numbers that
`svgbench.metrics` already knows how to produce, in an order decided now.

---

## What this file is not

It is not a claim that mistakes cannot happen after the tag. `DESIGN_FREEZE.md`'s
amendment procedure exists because they will. It is a claim that *the direction of a
result* is never an acceptable reason for the fix, and that the test for whether a
post-tag change is legitimate is whether it would have been made identically had the
arms come out the other way around.
