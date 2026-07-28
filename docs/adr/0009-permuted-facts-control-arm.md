# ADR-0009 — The permuted-facts control arm

**Date:** 2026-07-28 · **Status:** Accepted (added after design review) · **Priority:** blocking

## Decision

Add a `permuted` arm: **identical enhancement format, with the geometric values shuffled
between elements.** Same field names, same layout, same token count, same enumeration — only
the mapping from element to fact is destroyed.

Also add `legible` (real path data, no context) and `facts_only` (context without the SVG).

`permuted` is **required for v1 to be valid**. It is not an optional ablation.

## Why

The enhanced prompt changes **two things at once**, and the paper claims only one of them:

1. It adds geometric facts. *(the intended variable)*
2. It adds an **enumerated list of elements**, giving each a referential handle and turning an
   unstructured document into a selection problem over a visible menu.

Change (2) alone could produce a large improvement with zero geometric content. Enumeration
effects on structured-output tasks are well documented. Without a control that holds format
fixed and destroys only the information, a positive result supports *"adding a structured
element list improves single-target editing"* at least as well as it supports *"supplying
geometry closes the information gap"* — and only the second is being asserted.

This is the difference between a claim and a demonstration. If `permuted` matches `enhanced`,
the honest finding is that the gain is format, and that is a publishable result — it is simply
a different one.

`legible` addresses a separate confound: opaque `{{GEOM_...}}` tokens are out-of-distribution
markup, so baseline failure mixes an ambiguity effect with an unfamiliar-format effect. Real
path data isolates them and restores a claim to external validity.

`facts_only` asks whether the markup contributes at all — if identical, the task is list
selection, not SVG editing.

## Alternatives considered

| Option | Rejected because |
|---|---|
| No control; attribute the gain to geometry | The central claim would be unsupported. This was the original design's flaw |
| Random values instead of permuted | Permutation preserves the marginal distribution of the numbers exactly; random values change format statistics and confound the comparison |
| Enumerate elements with no facts at all | A weaker control — differs in token count and shape, so format is not held fixed |
| Argue the confound away in the discussion | Not a substitute for a measurement that costs one extra run |

## Tradeoffs

- **Gained:** the primary claim becomes falsifiable. The pre-registered primary comparison is
  **enhanced vs permuted**, not enhanced vs baseline.
- **Given up:** run time — three extra arms over the same frozen corpus. Cheap: they are
  prompt-assembly variants, requiring no new corpus and no new scoring code.
- **Accepted risk:** `permuted` may show that most of the gain is format. That is a real
  possibility and the reason the control exists. It would be reported as the headline.
