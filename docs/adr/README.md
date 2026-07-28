# Architecture Decision Records

One short record per non-obvious decision: what was decided, why, what else was considered,
and what was traded away. The point is that a reviewer can understand the rationale without
reading the full design documents.

Format: **Decision · Why · Alternatives considered · Tradeoffs · Date.**

| # | Decision | Status |
|---|---|---|
| [0001](0001-toolchain-and-rendering-stack.md) | Python 3.12; `svgelements` + `resvg-py` as two independent geometry witnesses | Accepted |
| [0002](0002-opaque-fixed-length-path-tokens.md) | Opaque, fixed-length path tokens; no positional attributes | Accepted |
| [0003](0003-full-svg-output-not-patch.md) | Model returns a full SVG document, not a patch | Accepted |
| [0004](0004-rasterized-coverage-as-canonical-area.md) | Rasterized pixel coverage is the canonical area | Accepted |
| [0005](0005-one-shared-runner-with-injectable-context.md) | One runner; arms differ only by an injected `ContextProvider` | Accepted |
| [0006](0006-identification-accuracy-as-primary-metric.md) | Identification accuracy is primary, not strict accuracy | Accepted |
| [0007](0007-corpus-size-and-cluster-level-inference.md) | 30 SVGs; resampling and testing at the SVG level | Accepted |
| [0008](0008-abstention-as-a-first-class-outcome.md) | Abstention is a first-class outcome, not a failure | Accepted |
| [0009](0009-permuted-facts-control-arm.md) | Permuted-facts control arm — required, not optional | Accepted |
| [0010](0010-decoding-and-replicate-policy.md) | Decoding and replicate policy | **PENDING** — before step 11 |

## When to add one

Add an ADR when a choice would make a reviewer ask "why did you do it that way?" and the
answer is not obvious from the code. Do not add one for style preferences or for decisions
with a single reasonable option.

Records are append-only. A superseded decision keeps its file and is marked `Superseded by
ADR-NNNN`, because the reasoning that was wrong is part of the record.
