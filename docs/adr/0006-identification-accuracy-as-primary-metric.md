# ADR-0006 — Identification accuracy is the primary metric

**Date:** 2026-07-28 · **Status:** Accepted (revised from initial design)

## Decision

**Identification accuracy** — did the model act on the intended element — is the headline
number. Strict accuracy (identification ∧ correct execution ∧ no collateral) is demoted to
secondary and reported alongside execution accuracy and collateral rate.

Identification is reported both unconditionally and conditional on well-formed output.

## Why

The initial design made strict accuracy primary. That was wrong: strict conflates three
independent capabilities.

1. **Identification** — which element? *This is what the experiment is about.*
2. **Execution** — was the edit performed per the operation spec?
3. **Non-collateral** — was nothing else touched?

Two models with identical identification ability but different formatting discipline get
different strict scores. Reporting strict as headline would let a formatting failure be read
as a reasoning failure — which is precisely the misattribution this benchmark exists to avoid.

The conditional-on-well-formed version matters because malformed rates will differ between
arms: enhanced prompts are longer (more truncation risk) but more structured (possibly better
compliance). Either direction, part of any measured "improvement" would be format compliance.
Reporting both numbers makes the size of that component visible instead of baked in.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Strict accuracy as primary | Conflates three capabilities; invites misattribution |
| Loose accuracy as primary | Trivially gamed by editing every candidate — scores ~100% while doing the opposite of the task |
| A single weighted composite | Weights would be arbitrary and would hide the decomposition |
| Identification only, drop the rest | Loses the hedging signal, which is the phenomenon that motivated the project |

## Tradeoffs

- **Gained:** the headline number answers the research question directly; failure modes stay
  separable; hedging remains visible via collateral rate and elements-modified.
- **Given up:** the headline is more generous than strict accuracy, so the numbers look
  better than an end-to-end "did it do the task" measure. Mitigated by reporting strict
  accuracy in the same table, never in a separate section.
- **Given up:** a single-number leaderboard. Accepted — a single number would be the wrong
  summary of a multi-capability task.
