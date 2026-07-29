# Contributing

This repository is a **frozen experimental instrument**, not an evolving library. That
changes what a useful contribution looks like.

## The one rule that governs everything

The corpus, scoring rules, predicates, leakage checks and evaluation rules were frozen at
the `instrument-freeze-v1` tag, **before any model output was observed**. See
[`RESULTS.md`](RESULTS.md).

Contributions that would change any of those are not accepted against v1. Not because
they are wrong, but because a result is only interpretable against the instrument that
produced it. The operational test:

> **Would this change have been made identically had the results come out the other way
> around?**

If no, it is not a fix. It is a new experiment, and it should be one.

## What is genuinely useful

| Contribution | Why it works |
|---|---|
| **Rescore the committed responses with your own scorer** | The strongest verification available. `experiments/*/responses.jsonl` is committed for exactly this |
| **Run a different model** | Change `model.name`; the corpus hash is unaffected by design. Report `svgbench report` output |
| **Report a reproduction failure** | `svgbench verify --determinism`, `svgbench report`, `pytest -m audit` |
| **Point out a threat to validity we missed** | [`VALIDITY.md`](VALIDITY.md) is organised by validity type; open an issue against the relevant section |
| **Extend to a new corpus (v2)** | Fork, change the seed or generation config, freeze a new dataset. `distributions.json` gives you a baseline to compare instruments |

## What we will not merge into v1

- Changes to scoring, predicates, or the frozen corpus
- New arms added to the existing run
- Prompt template changes (the template is versioned and hashed)

These belong in a **v2 instrument** with its own freeze, so that both results stay
interpretable.

## Before opening a PR

```bash
python -m pip install -e ".[dev]"
python -m pytest              # 280 tests
python -m pytest -m audit     # publication-gating checks
python -m ruff check . && python -m mypy
```

Audit tests gate publication. If one fails, the experiment still produces a number - it
is just the wrong number.

## Reporting a problem with a number

Please include the output of `svgbench report` and `svgbench verify`. Tier-1 and Tier-2
reproduction need no model and no renderer, so a mismatch is usually diagnosable from
those two alone.

## Known-wrong assumptions

Eleven are documented in [`FAILED_ASSUMPTIONS.md`](FAILED_ASSUMPTIONS.md), with a
taxonomy noting that **systems-integration defects are the class this project's test
suite is weakest against**. If you find another, that file is where it goes.
