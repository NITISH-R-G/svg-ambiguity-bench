# DESIGN FREEZE — v1

**Date frozen:** 2026-07-28
**Status:** FROZEN. Implementation has begun.

---

## What is frozen

| Area | Status | Record |
|---|---|---|
| Product requirements | FROZEN | [`docs/00-prd.md`](docs/00-prd.md) |
| Research architecture | FROZEN | [`docs/01-architecture.md`](docs/01-architecture.md) |
| Experimental protocol | FROZEN | [`docs/02-experiment-design.md`](docs/02-experiment-design.md) |
| Scoring rules | FROZEN | [`docs/02-experiment-design.md`](docs/02-experiment-design.md) §Scoring |
| Metrics | FROZEN | [`docs/02-experiment-design.md`](docs/02-experiment-design.md) §Metrics |
| Repository structure | FROZEN | [`docs/01-architecture.md`](docs/01-architecture.md) §2 |
| Decision rationale | FROZEN | [`docs/adr/`](docs/adr/) |

---

## The rule

**No further architecture work unless a critical implementation issue is discovered.**

A "critical implementation issue" means one of:

1. A design element is **impossible** to implement as specified.
2. A design element is **incorrect** — it would produce a wrong measurement.
3. A dependency or platform constraint **forbids** the specified approach.

It does *not* mean:

- A more elegant structure occurred to me.
- A new metric would be interesting.
- An additional ablation would strengthen the paper.
- The design could be more general.

Ideas in the last category are recorded in [`docs/BACKLOG.md`](docs/BACKLOG.md) and are **out of scope for v1**.

---

## Amendment procedure

If a critical issue is found:

1. Open an ADR in `docs/adr/` describing the issue and the change.
2. Amend the affected frozen document with a dated amendment note **appended**, never by silent edit.
3. Record the change in `CHANGELOG.md`.
4. If the change touches **scoring or metrics after any model output has been observed**, it must additionally be disclosed in the final report, with the pre-change result retained. See the pre-registration boundary below.

---

## Pre-registration boundary

This is the single most important process commitment in the project.

**The dataset and the scoring rules are frozen and git-tagged BEFORE the first model output is observed.**

Concretely:

- Steps 1–9 of the implementation order (through the evaluation engine) complete first.
- The scoring logic is unit-tested against hand-built fixtures authored *before* any model has run.
- A git tag `pre-registration` marks that commit.
- Only then does Step 10 (model runner) execute.

After that tag, any change to scoring or metrics is an **amendment**, disclosed with both the old and new numbers. This exists so that no scoring rule can be tuned — consciously or otherwise — to a result already seen.

The bright-line version of this rule, plus the pre-registered decision procedure for reading the three comparisons that matter (`baseline ≈ 1/K`, then `enhanced > baseline`, then `enhanced > permuted`), is in [`RESULTS.md`](RESULTS.md).

---

## Implementation order (frozen)

1. Repository scaffolding
2. Configuration system
3. Dataset generator
4. Geometry engine
5. Ground-truth engine
6. Predicate registry
7. Instruction generator
8. Dataset freezing
9. Evaluation engine  ← **git tag `pre-registration` here**
10. Model runner
11. Baseline experiment
12. Enhancement implementation
13. Enhanced experiment
14. Reporting

One step at a time. Each step must import cleanly and pass its tests before the next begins.

---

## Scope commitments carried from design review

The adversarial review ([`docs/03-review.md`](docs/03-review.md)) produced a prioritized list. What v1 commits to:

**In scope (Critical — v1 is not valid without these):**

- Permuted-facts control arm (isolates information content from prompt format)
- Abstention as a first-class outcome class
- Identification accuracy as the primary metric, not strict accuracy
- Per-predicate reporting, not only per-family
- Empirical test of the `1/K` null via selection-position distribution
- Resolved replicate/temperature policy
- Reframed contribution: enhanced arm is the benchmark, baseline is the manipulation check
- Predicate uniqueness asserted against the full element set, not only the ambiguity set
- Malformed and truncation rates reported per arm

**In scope (Important — included because cheap on the same frozen corpus):**

- Legible-geometry control arm
- Facts-only condition
- Multiple small models
- Human agreement check on the predicate registry

**Out of scope for v1** — recorded in `docs/BACKLOG.md`, not implemented:

- Format ablations beyond one enhancement rendering
- K sweep, distractor ablation, margin sweep beyond reporting
- Perceptual area weighting
- VLM arm (addressed in discussion only)
- Adversarial phrasing variants

Several review findings **cannot** be fixed within the assignment's 20–30 SVG constraint —
cluster count, single-corpus generality, synthetic-domain external validity. For those the
committed response is **narrower claims**, stated up front in `LIMITATIONS.md`, not more
experiments.

---

## Signed off

Architecture v1 approved. Experimental protocol frozen. Scoring frozen. Metrics frozen.
Repository structure frozen.

Building now.
