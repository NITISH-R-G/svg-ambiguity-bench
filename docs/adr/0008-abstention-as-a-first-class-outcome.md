# ADR-0008 — Abstention is a first-class outcome, not a failure

**Date:** 2026-07-28 · **Status:** Accepted (added after design review)

## Decision

`ABSTAINED` is its own outcome class, separate from `NO_EDIT`. Abstention rate is reported as
its own row, and accuracy is reported both including and excluding abstentions. The textual
criterion for detecting an abstention is fixed before any model output is read.

## Why

Consider the ideal response to *"make the top-left shape blue"* given markup that provably
does not encode position:

> "The markup does not contain positional information, so I cannot determine which shape is
> top-left."

That is the correct answer. The original design scored it as `NO_EDIT` — a failure, pooled
with a model that produced nothing.

That is not a bookkeeping detail. It embeds a value judgement in the metric: a guess has
probability `1/K` of scoring, an abstention has probability 0, so the metric **rewards
confident guessing**. Meanwhile the project's stated motivation is that models hedge under
ambiguity. Rewarding non-hedging while complaining about hedging is incoherent.

There is also a live confound. If the enhanced arm improves partly by converting abstentions
into guesses, the headline number rises while the behaviour arguably worsens. Only a separate
abstention row makes that visible.

The cross-arm pattern is itself a finding: a model that abstains in `baseline` and commits in
`enhanced` is **well calibrated**, and that is invisible under the original scheme.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Pool abstention into `NO_EDIT` (original design) | Scores correct behaviour as failure; rewards guessing |
| Score abstention as correct in the baseline arm | Requires deciding a priori that abstention is right, which pre-judges the result and is arm-dependent — a scoring rule that knows the arm is not arm-blind |
| Prompt the model never to abstain | Suppresses the behaviour instead of measuring it, and makes the benchmark unable to see calibration |
| Treat abstention as a separate arm | Over-engineering; it is a response property, not an experimental condition |

## Tradeoffs

- **Gained:** the metric stops punishing calibrated uncertainty; calibration across arms
  becomes measurable; a real confound in the headline comparison is exposed.
- **Given up:** two accuracy numbers instead of one (with and without abstentions), which is
  more to explain. Accepted — the alternative is one number that is quietly wrong.
- **Risk:** detecting abstention from free text is a classifier, and classifiers have error
  rates. Mitigated by fixing the rule pre-registration, testing it against hand-built
  fixtures, and reporting how many cases it caught.
