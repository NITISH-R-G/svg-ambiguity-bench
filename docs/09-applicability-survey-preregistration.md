# Survey pre-registration - does anyone need this?

**Status: PRE-REGISTERED. No papers have been assessed against these criteria.**

Every study so far has asked whether the method *works*. This asks whether it is *needed*,
which is the question a hostile reviewer put more sharply than any internal check did:

> It doesn't answer a question anyone else was asking.

Nothing in the repository answers that, and no amount of documentation can. It is an
empirical question about the literature, so it gets the same treatment as everything else
here: criteria first, then look.

---

## The question

Among published evaluations that claim *"adding structured context X improved metric Y"*,
what fraction run a control that separates the **information** in X from the **format** X
arrives in?

If most already do, the method is redundant and this project's remaining value is as a
specification of something the field handles fine. **That is a real possible outcome and
it would be worth knowing.**

## Sample

**Pilot: 15 papers.** Not fifty. If the effect is as one-sided as either side of this
argument expects, fifteen resolves it; if it is genuinely marginal, fifteen tells us to
either stop or commit to the larger survey with a sharper instrument. Running fifty first
would be spending a week to learn what a day can establish.

Drawn from: RAG, tool use / function calling, memory and personalisation, metadata
conditioning, and structured prompting. Sampled by search rather than by citation count,
because highly-cited papers are not representative of practice.

**Selection is recorded before assessment.** A paper enters the sample if its abstract or
results claim an improvement attributable to added structured context. Papers are not
dropped after reading for being inconvenient; a paper that turns out not to make such a
claim is recorded as **out of scope** with the reason.

## Per-paper coding

Fixed now. Each paper gets four judgements, in this order:

1. **Claim present?** Does it assert that adding context X improved a metric?
2. **Applicability condition met?** Is X a representation admitting value permutation while
   preserving token count, field structure, ordering and width?
   (`METHOD.md`. Fixed-schema tables, metadata records, tool argument lists: yes.
   Variable-length free text: usually **no**.)
3. **Separating control present?** One of:
   - **yes** — an arm holding format fixed and destroying information (shuffled, permuted,
     randomised-but-matched)
   - **partial** — a control that varies content but *also* varies format (e.g. removing
     the field, empty context, irrelevant passages of different length)
   - **none** — augmented vs unaugmented only
4. **Would the conclusion change?** Only asked when 3 is `partial` or `none`:
   could the reported gain be wholly or partly a format effect, on the paper's own
   evidence? **unknown** is a permitted and expected answer.

## Pre-registered interpretation

Let *A* = papers meeting the applicability condition, *S* = those among them with a
separating control.

| Outcome | Condition | Conclusion |
|---|---|---|
| **REDUNDANT** | `S/A >= 0.60` | The field already controls for this. The critic is right that the gap is not real. `fmtcontrol` is a tidy specification of common practice and should be presented as nothing more |
| **PARTIAL** | `0.25 <= S/A < 0.60` | Mixed practice. The method has a target but the problem is not systemic; the honest framing is "inconsistently controlled" |
| **GAP** | `S/A < 0.25` | Most applicable published claims do not separate information from format. The gap is real and nameable, and the next paper writes itself |
| **INAPPLICABLE** | `A/15 < 0.30` | Fewer than a third of context-augmentation papers use permutable representations. The method is narrower than claimed and the applicability condition is the finding |

**Prediction, recorded now:** GAP, with `A/15` around 0.4-0.6 — i.e. the control is rarely
run, *and* the method applies to a minority of papers because much context is free text.
Confidence: low. I have been wrong on two of three previous predictions.

The outcome that most damages the project is REDUNDANT. The outcome that most damages the
*framing* is INAPPLICABLE, because it would mean the headline application - RAG - is
mostly out of scope.

## Falsifiers

- **Fewer than 8 papers can be assessed** from available sources: the pilot is
  underpowered and reports counts only, no ratio.
- **Assessment rests on abstracts alone** for more than half the sample: coding
  "separating control present" from an abstract is unreliable, and that limit is
  reported rather than worked around.

## What this may and may not change

**May change:** how the contribution is framed; whether a survey paper is the right next
output; the priority order in `TRUST.md`.

**May not change:** any V1-V3 number, the frozen instrument, or the specification.

## Honest note on who is coding

One assessor, who has an interest in the answer. That is a real bias and there is no
blinding available. Mitigations: criteria fixed in advance, `unknown` permitted and
expected, every paper listed with its judgement so a reader can disagree per-row, and the
prediction recorded before searching.

It is weaker evidence than an independent survey would be, and is reported as a **pilot**
rather than as a result.
