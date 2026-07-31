# Start here

This repository has a lot of documents. Each exists for a reason, but you almost
certainly do not need all of them. Pick your row.

---

### I want the method, not the benchmark

The transferable part. Domain-independent, two pages, with pseudocode.

→ **[`METHOD.md`](METHOD.md)** — format-matched controls for context-augmentation
experiments

If you are running a RAG, tool-use, memory, or structured-prompting experiment and
claiming that *the information* helped, this is the part that applies to you.

→ **[`docs/essay.md`](docs/essay.md)** — *How we almost measured the wrong thing*

The narrative version: the confound, the many times the instrument turned out to be
wrong rather than the hypothesis, and why the null was still informative.

---

### I want to know what was found

→ [`README.md`](README.md) — the result in one screen
→ [`docs/04-results.md`](docs/04-results.md) — full write-up, three hypotheses, claim outcomes
→ [`OBSERVATIONS.md`](OBSERVATIONS.md) — the observation log, interpretation kept separate from explanation

---

### I want to reproduce it

```bash
pip install -e ".[dev]"
python -m svgbench.cli report      # every published number, ~2s, no model, no renderer
```

→ [`README.md#reproducing`](README.md) — the four tiers and what each needs
Tiers 1 and 2 need neither a model nor an SVG toolchain. Raw responses are committed, so
you can write your own scorer and check ours against it.

---

### I want to decide whether to believe it

→ [`VALIDITY.md`](VALIDITY.md) — internal, construct, external, statistical-conclusion validity, each with residual threats
→ [`LIMITATIONS.md`](LIMITATIONS.md) — 17 things this does not show
→ [`EVIDENCE.md`](EVIDENCE.md) — measured values per claim, regenerated not recalled

Start with `VALIDITY.md`. It states what is established, what is planned, and what
**cannot** be established at all.

---

### I want to audit the methodology

→ [`CLAIMS.md`](CLAIMS.md) — every module maps to one claim; what would falsify each
→ [`RESULTS.md`](RESULTS.md) — what may and may not change once results exist
→ [`FAILED_ASSUMPTIONS.md`](FAILED_ASSUMPTIONS.md) — thirteen times the project proved itself wrong
→ [`DESIGN_FREEZE.md`](DESIGN_FREEZE.md) — the Phase I / Phase II boundary
→ [`docs/verification-policy.md`](docs/verification-policy.md) — why a fixture must fail differently than the implementation

`FAILED_ASSUMPTIONS.md` is the most useful of these for judging trustworthiness. It
includes a taxonomy noting which class of defect the test suite is weakest against.

---

### I want to extend it

→ [`CONTRIBUTING.md`](CONTRIBUTING.md) — what a useful contribution looks like against a frozen instrument
→ [`docs/BACKLOG.md`](docs/BACKLOG.md) — deliberately out of scope for v1, with reasons
→ [`docs/adr/`](docs/adr/) — eleven decision records: what was decided, why, what else was considered

The corpus is frozen. Changing the scoring, predicates, or dataset makes it a **v2
instrument**, not a fix — see `RESULTS.md`.

---

### I want to read the code

```
src/svgbench/
  config/       schema, layering, two hashes (corpus identity vs experiment identity)
  generation/   corpus synthesis, geometry redaction
  geometry/     two independent measurement engines that must agree
  groundtruth/  predicate registry, construct-validity gate
  instructions/ instruction synthesis, leakage lint, provenance
  dataset/      freeze, manifest, certificate, tamper-verified integrity
  context/      the four arms - the manipulated variable lives here
  runner/       one prompt template, one execution path, append-only store
  evaluation/   parse, align, diff, classify - arm-blind by signature
  metrics/      cluster bootstrap and paired permutation at the SVG level
  reporting/    Tier-1 reproduction; imports no model and no renderer
```

The layering is enforced by a test: nothing may import from a stage downstream of it,
and the scoring path may not import a renderer.

---

## The shortest possible summary

An SVG contains several elements that are indistinguishable in its markup. An instruction
names one of them by how it *looks*. Supplying the missing geometry ought to help.

We measured whether it does — and, critically, whether any improvement would come from
the **information** supplied or merely the **format** it arrives in.

The answer was a constrained null: the context changed what the model said, but not which
element it identified. The method for asking the question is in
[`METHOD.md`](METHOD.md).
