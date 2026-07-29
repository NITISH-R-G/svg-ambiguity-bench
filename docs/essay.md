# How we almost measured the wrong thing

*An essay about building an experiment whose instrument turned out to be wrong more often
than its hypothesis.*

---

## The question

An SVG is a drawing program. Its rendered output has position, size and adjacency. Its
source text often encodes none of them in readable form.

So this markup is genuinely under-determined:

```xml
<path id="e13415408" d="{{GEOM_1b7549de}}" fill="#8c5a3c"/>
<path id="e15485c60" d="{{GEOM_33cabe17}}" fill="#c0c0c0"/>
<path id="e0d63fea4" d="{{GEOM_c2532d12}}" fill="#8c5a3c"/>
<path id="e30176ca8" d="{{GEOM_a9f3024e}}" fill="#8c5a3c"/>
```

Three elements share a fill. The geometry is redacted. Asked to *"make the top-left shape
blue"*, a model has nothing in the source to go on. The instruction refers to the
rendered picture; the edit happens in the source text; the source text does not encode
what the instruction is about.

The obvious fix is to supply the missing facts — centroid and area, per element. And the
obvious experiment is: measure accuracy with and without them.

That experiment is where the interesting problem starts, and it has nothing to do with
SVG.

---

## The confound

Adding context to a prompt changes **two things at once**.

It adds the *information* you intend. It also adds a *format*: an enumerated list, a
table, a set of referential handles that did not previously exist, several hundred extra
tokens. Either could move the score.

If you compare augmented against unaugmented and see an improvement, those two
explanations are observationally identical. You are entitled to *"a prompt shaped like
this helps"* — but the claim people actually make is *"this information helps."*

The fix is a third arm: same format, information destroyed. Keep the field names, the row
count, the column widths, the token count. **Permute the values between elements** so the
mapping from element to fact is broken and nothing else is.

Then:

| comparison | isolates |
|---|---|
| enhanced − baseline | the total effect |
| permuted − baseline | the **format** component |
| enhanced − permuted | the **information** component ← the claim |

None of this is new. Matched controls are ordinary experimental design — placebo arms,
matched-noise conditions in psychophysics, matched-random ablations. What seems to be
missing is anyone applying that control to *prompt context*. The benchmarks I surveyed
report a single augmented-versus-unaugmented number.

So: a standard control, applied to a confound that context-augmentation evaluations
routinely leave uncontrolled. A small claim, and the one the evidence supports.

---

## Eleven times the instrument was wrong

Here is the thing I did not expect.

Over the project, eleven assumptions turned out to be false. **Every single one was in
the measuring apparatus, not in the thing being measured.** Not one was a wrong guess
about how the model would behave.

A few, because the specifics matter more than the count:

**The leak detector was miscalibrated.** A check reported that document order predicted
element size at z = +2.76 — within my threshold, technically passing. I swept 25 seeds
anyway. Mean z = +1.605, 8.95 standard errors from zero. That reads as a corpus with a
real leak, which would have invalidated the entire premise.

It wasn't the corpus. It was two independent bugs in my *statistic*. Ordinal ranks where
midranks were required, so tied values were broken by append order — identical in both
vectors, manufacturing correlation from nothing. And an analytic z-score that is simply
wrong for this structure: under a shuffle that is uniform **by construction**, it has mean
**+0.88**, not 0, because positions and attribute ranks both run 0..K−1 within a group and
pooling across groups of different size induces association from group size alone.

I found the second by building a synthetic null I knew was uniform and measuring what the
statistic did to it. Standardised against that empirical null, the generator sat at +0.36.
Fine. Had I trusted the formula, I would have reported a leak that does not exist.

**A field was named wrong.** `ElementIntent.center_x` was the *placement anchor* the shape
was constructed around — not its area centroid. Because vertex radii are jittered, the two
differ by about three units. I found it by asserting they were equal and watching the
assertion fail. Every spatial predicate — `leftmost`, `top_left` — would have resolved
against the wrong point, been wrong by a few units on every case, and stayed perfectly
self-consistent while doing it.

**A threshold was set by intuition.** `min_spatial_margin = 0.15` looked reasonable. It
sat almost exactly on the *median* of the observed margin distribution, refusing 52% of
spatial predicates and leaving 13 of 30 samples unable to supply the instructions the
design needed. The test that should have caught it asserted "at least one valid predicate
per family per sample" — and passed, because the minimum genuinely was 1. Availability is
a corpus-level property, and a per-item assertion is not a weaker version of an aggregate
check. It is a *different* check that passes while the requirement fails.

**Git would have broken the corpus.** The frozen dataset is content-addressed; the freeze
code writes LF explicitly so a corpus frozen on Windows hashes identically to one frozen
on POSIX. Staging it produced 94 warnings that git would convert LF to CRLF on checkout.
The freeze code controls the bytes it *writes*. It does not control what git *checks out
somewhere else*. **A fresh clone on Windows would have failed the corpus's own integrity
check** — and every test inside the repository was green.

**The verification tool was wrong about the verification.** I broke the scorer nine ways
to check whether the fixtures would catch each. Two "survived." They hadn't applied:
`from X import Y` copies the reference, so patching the defining module leaves the
importer's binding untouched. My mutation harness was lying about my mutation coverage.

---

## The pattern

Reading those back, one habit did the work:

> **Distrust the measuring instrument before distrusting the thing being measured.**

What makes that hard is that in almost every case above, **nothing was failing**. z = 2.76
was inside the threshold. Every sample really did have ≥1 valid predicate. The corpus
really did verify locally. The mutation harness really did report 7/9.

There was no red build. Interrogating the instrument was a *choice* each time, and the
cheapest moment to make it is when everything looks fine.

The second-order version of this is the one I'd underline: **a verification tool deserves
the same scepticism as the thing it verifies.** My leak detector, my margin test and my
mutation harness were all wrong at some point. Each was written to check something else.

---

## Freezing, and why it's about your future self

Before running any model, I tagged the instrument: corpus, scoring rules, predicates,
evaluation logic, analysis plan. The tag message records the dataset hash and the line
`NO MODEL OUTPUTS HAVE BEEN OBSERVED.`

Pre-registration is usually explained as preventing p-hacking. I think that undersells it:

> **Pre-registration transfers epistemic authority from your future self back to your past
> self.** Your past self knew less — and is in a better position to write the rules
> *precisely because of that*. A rule written when it is cheap binds a version of you for
> whom it will be expensive.

It is not a defence against dishonesty. It is a defence against the ordinary, sincere
reasoning that only becomes available *after* you have seen the answer — which is harder
to guard against, because it does not feel like motivated reasoning at the time.

The operational test I ended up with:

> Would this change have been made identically had the results come out the other way
> around?

---

## The result

All three arms scored **identification accuracy 0.0444**, against a random-selection
reference of 0.1852. Every pairwise difference **0.0000**. Minimum detectable effect
**0.0289**.

The instinct is to call this a failed experiment. It isn't, and the reason is that three
hypotheses were separately measurable:

| | | |
|---|---|---|
| **H1** the model ignored the context | *rejected* | 56/180 responses differ |
| **H2** the context never reached the model | *rejected* | 180/180 prompts differ |
| **H3** context altered generation without improving reference resolution | **supported** | the only one consistent with both |

**The context reaches the model and changes what it says. It does not change which element
it identifies.** That is a concrete observation, and considerably more specific than "no
improvement."

Two things I'd flag about reporting it.

The p-values are all 1.000 and carry **no information**. With an observed difference of
exactly zero, no permutation of the data can be more extreme; the test is degenerate. The
number a reader actually wants is *how large an effect could you have missed* — which is
what the MDE answers. Report the bound, not the ritual.

And the null is *constrained*, not general. Not "context never helps." Rather: on this
corpus, for this model, context changed generation without changing identification. Every
qualifier is load-bearing.

---

## What I'd say honestly against it

The uncomfortable part: **the format-matched control — the methodological contribution —
was never exercised in the role it was built for.** It exists to decompose a positive
effect. There was no positive effect. It demonstrated that the control can be built and
audited, not that it resolves what it was designed to resolve.

Two other claims came back vacuous. Execution-given-identification was 1.000 everywhere,
so the identification/execution split separated nothing here. Abstention was 0/180, so
that outcome class never fired. Both were right to build — each could have mattered and
would have been unrecoverable afterwards — but the repository cannot claim they improved
*this* measurement.

And it's one small model on a synthetic corpus with opaque tokens that don't occur in real
SVGs. The model declined to edit at all in 44% of cases, which may say more about models
at this scale than about the task.

---

## The experiment I wanted to run and didn't

Somewhere in the 44% no-edit rate is a real question: is the model unable to *use* the
supplied facts, or unable to *perform the edit*? An arm naming the target element by id
outright would separate those cleanly. It's half an hour of work.

I didn't run it. Adding an arm after seeing a null is designing toward an explanation for
a result already in hand, and the rule I'd written months earlier said no.

I want to be accurate about that: declining wasn't discipline in the moment. The argument
for running it — *"it's obviously informative"* — was available and tempting. What stopped
it was a decision made when it was cheap, binding a version of me for whom it was
expensive.

It's recorded as future work, with the reasoning attached, so a future reader knows it was
considered and declined rather than overlooked.

---

## What transfers

If you're running an experiment where added context is credited with an improvement — RAG,
tool schemas, memory, metadata, structured prompting — the confound is the same and so is
the control. **Same shape, wrong contents.** One extra arm.

The two implementation details that are easy to get wrong and load-bearing: use the *same
renderer* for both arms, or format is no longer held fixed; and reject the identity
permutation, or that case silently becomes a second augmented case with no test failing.

The method is in [`METHOD.md`](../METHOD.md). The worked example, all 540 raw responses,
and the instrument that produced them are in the repository.

The SVG benchmark answers one narrow question and is explicit about the boundary. The
habit of asking *"could my measuring instrument be wrong?"* before *"could my hypothesis
be wrong?"* is the part I'd carry to the next project.
