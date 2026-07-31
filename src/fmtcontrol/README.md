# fmtcontrol

**A format-matched control for context-augmentation experiments.** Domain-independent;
knows nothing about SVG, retrieval, tools or memory.

This is the transferable part of [svg-ambiguity-bench](../../README.md). The benchmark is
the case study; this is the method. It is kept importable on its own so the
domain-independence claim is checkable rather than asserted — a test fails if this package
ever imports the benchmark.

## The problem

Adding context to a prompt changes **two things at once**: the *information* it carries
and the *format* it arrives in. Comparing augmented against unaugmented cannot separate
them, so a measured improvement is equally consistent with "the retrieved facts helped"
and "a table helped".

Anyone claiming *"supplying X improves performance"* from a two-arm comparison is entitled
only to the weaker claim: *"a prompt shaped like X improves performance."*

## The control

A third arm, format-identical and information-destroyed. Same rows, same fields, same
widths, same token count — with the values permuted between entities so the entity-to-fact
mapping is broken and nothing else is.

| comparison | isolates |
|---|---|
| `enhanced − baseline` | total effect |
| `permuted − baseline` | **format** component |
| `enhanced − permuted` | **information** component ← the claim |

## Usage

```python
from fmtcontrol import permute, check_control

facts = {"doc_1": ("Paris", 2.1), "doc_2": ("Berlin", 3.4), "doc_3": ("Rome", 0.7)}

permuted = permute(facts, key="query_42", seed=991)

enhanced_text = my_renderer(facts)      # the SAME renderer for both arms,
permuted_text = my_renderer(permuted)   # or format is no longer held fixed

report = check_control(facts, permuted, enhanced_text, permuted_text)
assert report.ok, report.failures
```

**Why you render, not the package.** A renderer living here would have to guess your
format, and an arm rendered by different code from its treatment is not a format-matched
control. Handing the mapping back keeps the single-renderer requirement visible at the
call site, where it can be got right.

## What the checks catch

Each corresponds to a way the control quietly stops being one — none of which raises on
its own:

| check | prevents |
|---|---|
| identical value multiset | the permutation altered information, not just its assignment |
| same entity order | row order became a difference between arms |
| non-identity permutation | the control arm silently became a second treatment arm |
| token count within tolerance | prompt length became a confound |
| line count identical | the arms are not actually format-matched |
| rendered text differs | no manipulation occurred at all |

`permute` refuses rather than degrades: fewer than two entities, or all values equal,
raises instead of returning something that looks like a control and is not.

## Reporting

**When the effect is zero, report the minimum detectable effect, not the p-value.** With
an observed difference of exactly zero no permutation can be more extreme, so p = 1.000 by
construction and carries no information. State the null in bounded form: *no effect larger
than X occurred* — not *the effect is zero*.

## Where it applies

Anywhere added context is credited with an improvement: **RAG** (passages vs passages
permuted between queries), **tool use** (schemas vs arguments permuted between tools),
**memory** (a user's facts vs facts permuted between users), **structured prompting**,
**metadata augmentation**. The recipe is constant: *same shape, wrong contents.*

## Provenance

Matched controls are not new — placebo arms, matched-noise conditions in psychophysics,
matched-random ablations. What appears to be missing, per a
[2026 review](../../docs/03-review.md) of the SVG-editing and structured-editing benchmark
literature, is anyone applying that control to **prompt context**.

So: an application, not an invention.

**Status: the control has not yet been exercised in the role it was built for.** Across
three pre-registered studies and four models it has never had a positive effect to
decompose — see [`LIMITATIONS.md`](../../LIMITATIONS.md) §14 and
[`docs/08-study-v3-results.md`](../../docs/08-study-v3-results.md). It is known to be
buildable, auditable and behaviour-preserving under extraction. It is not known to resolve
what it was designed to resolve.

Put precisely: **the implementation currently has stronger evidence behind it than the
hypothesis it was built to test.** The code is validated by 10 conformance vectors and by
540 prompts committed before it was extracted. The hypothesis — that separating
information from format changes a conclusion someone would otherwise have drawn — awaits a
model that produces an effect to separate.

## Specification

[`SPEC.md`](SPEC.md) defines the control independently of this code: nine invariants, the
algorithm, the boundary cases, and two conformance levels. An implementation in another
language can be checked against [`conformance_vectors.json`](conformance_vectors.json)
without reading any Python.

**Level 1** (invariants hold; any PRNG) is what you need to run your own experiment.
**Level 2** (bit-exact vector reproduction) is only needed to reproduce this project's
published prompts, and carries a documented wart: it pins MT19937 because the frozen
instrument was built against it. `SPEC.md` §8 explains why that cannot be changed
retroactively and what a v2 should do instead.
