# ADR-0010 — Decoding and replicate policy

**Date opened:** 2026-07-28 · **Date resolved:** 2026-07-29 · **Status:** Accepted

## Decision

**Greedy decoding (temperature 0), one replicate per case.**

## The open question, as originally posed

Replicates and temperature are coupled:

- At **temperature 0** with a deterministic backend, N replicates are N identical calls.
  Reporting three of them would imply a robustness that does not exist and spend 3x the
  compute for no information.
- At **temperature > 0**, replicates measure real stochasticity — but decoding
  temperature becomes an experimental variable nobody swept, and the result is
  conditional on an arbitrary value.

This ADR was deliberately left **pending** with a pre-committed resolution rule, so the
choice would be made by a measurement rather than by convenience, and so the rule was
written before the measurement existed.

## The pre-committed rule

> The smoke test measures whether the backend is deterministic at temperature 0.
> Deterministic → greedy, 1 replicate, with variance listed as unmeasured in
> LIMITATIONS. Non-deterministic → replicates are meaningful, and per-case success
> *rate* becomes the analysis unit.

## The measurement

Three byte-identical prompts submitted to Ollama at `temperature=0`, `top_p=1.0`,
`seed=0`, on both candidate models:

| Model | Distinct responses from 3 identical prompts |
|---|---|
| `qwen2.5-coder:1.5b` | **1** |
| `qwen2.5-coder:3b` | **1** |

Deterministic on this backend, this hardware, these settings.

## Consequence

`evaluation.replicates = 1`. The rule fires as written; no judgement was exercised after
seeing the result.

## Tradeoffs

- **Gained:** a third of the compute back, and a result that does not overstate its own
  robustness. 540 calls instead of 1620.
- **Given up:** any estimate of run-to-run variance. A single unlucky decode is
  indistinguishable from a systematic failure on that case. This is listed in
  `LIMITATIONS.md` as unmeasured rather than implied to be zero.
- **Scope of the finding:** determinism was verified on *this* backend, *this* hardware,
  *these* decoding settings. It is not a general property of Ollama, and a reproducer on
  different hardware may observe variation. That is why the measurement is recorded here
  rather than assumed.

**Replicate count never enters `n`.** The analysis unit remains the per-case result, and
the cluster count remains the number of SVGs (ADR-0007).
