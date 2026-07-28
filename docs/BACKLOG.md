# Out-of-scope backlog

Ideas that are **not** part of v1. Recorded here so they stop competing for attention.

`DESIGN_FREEZE.md` forbids reopening the design for anything on this list. Adding an item is
free; implementing one requires v1 to be finished and reported first.

## Deferred ablations

| Item | Would answer | Why deferred |
|---|---|---|
| Enhancement format variants (≥2 renderings of identical facts) | Is the effect the content or its presentation? | `permuted` already separates content from format; format *tuning* is a second-order question |
| K sweep | Does difficulty scale as `1/K` predicts? | Corpus is fixed at K ∈ [4,7]; a sweep needs a second corpus |
| Distractor ablation (with/without) | Do distractors contaminate predicates? | Uniqueness is already asserted over the full element set |
| Margin sweep as an experiment | How much does corpus easiness matter? | Reported as stratified accuracy instead, which is nearly free |
| Adversarial phrasing (synonyms, negation) | Robustness to wording | Multiple templates per predicate cover the first-order concern |
| Perceptual area weighting | Does compressive size judgement change ordinal ground truth? | Introduces a free parameter with no principled value for this corpus |

## Deferred arms

| Item | Why deferred |
|---|---|
| Vision-language model arm | Compute; addressed in discussion. **The most valuable single addition if v1 finishes early** |
| Larger / hosted models | Explicitly out of scope in the PRD |
| Multi-step or conversational editing | Out of scope |
| Real-world SVG corpora (icons, logos, maps) | Out of scope; would need a different ground-truth strategy |

## Deferred engineering

- Parallel model execution (run time is not the bottleneck at this corpus size)
- A results dashboard or UI
- Packaging to PyPI
- Cross-platform renderer conformance testing

## Deferred analysis

- Multiplicity correction across the secondary metric surface
- Qualitative error taxonomy from hand-reading 20–30 failures — *cheap, and usually the
  most-quoted part of a short write-up. First thing to pull forward if time allows.*
- Cost-effectiveness curve (accuracy per additional context token)
