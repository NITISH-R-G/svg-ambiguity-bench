# ADR-0010 — Decoding and replicate policy

**Date:** 2026-07-28 · **Status:** PENDING — must be Accepted before implementation step 11

## The open question

Replicates and temperature are coupled, and the original design did not resolve the coupling:

- At **temperature 0**, N replicates are N identical calls. Reporting three of them implies a
  robustness that does not exist, and spends 3× the compute for no information.
- At **temperature > 0**, replicates measure real model stochasticity — but decoding
  temperature becomes an experimental variable that nobody swept, and the result becomes
  conditional on an arbitrary value.

## Constraint

This must be decided **before the baseline run**, because deciding it afterwards — with
results visible — would breach the pre-registration boundary in `DESIGN_FREEZE.md`.

## Candidate options

| Option | For | Against |
|---|---|---|
| Greedy, 1 replicate | Cheapest; fully determined given a backend; no arbitrary temperature | No estimate of run-to-run variance; a single unlucky decode is indistinguishable from a systematic failure |
| Greedy, N replicates | — | Wasteful: identical outputs. Rejected outright unless the smoke test shows the backend is non-deterministic at temperature 0, which would itself be worth recording |
| Temperature > 0, N replicates | Measures stochasticity honestly; per-case rate is a richer unit | Adds a swept-nowhere parameter; multiplies run time |

## Decision procedure (frozen)

The smoke test at implementation step 10 will measure whether the chosen backend is in fact
deterministic at temperature 0 on this task — local backends often are not, because of
threading and batching. That measurement decides this ADR:

- **Deterministic at temp 0** → greedy with 1 replicate; variance discussed as unmeasured and
  listed in `LIMITATIONS.md`.
- **Non-deterministic at temp 0** → greedy with N replicates is meaningful after all, since
  the variation is real; per-case success *rate* becomes the analysis unit.

Either way: **replicate count never enters `n`.** The analysis unit is the per-case rate, and
the cluster count stays the number of SVGs (ADR-0007).

## Why this is recorded now, unresolved

Leaving it implicit is how an experimental parameter gets chosen by accident and then
rationalised. Recording it as an open decision with a pre-committed resolution rule means the
choice is made by a measurement rather than by convenience — and that the rule was written
before the measurement existed.
