# ADR-0004 — Rasterized coverage is the canonical area

**Date:** 2026-07-28 · **Status:** Accepted

## Decision

Canonical area — the quantity that defines "largest", "second largest", "smallest" — is
**rasterized pixel coverage at a fixed DPI**. The analytic path area is computed as an
independent cross-check; disagreement beyond tolerance fails the sample.

## Why

The ordinal instruction family is *perceptual*. "Second largest" means *looks* second
largest. Signed analytic area diverges from perceived extent for concave and self-intersecting
shapes, and can even go negative depending on winding. Pixel coverage is what a viewer's eye
integrates.

Using both, from two unrelated implementations (ADR-0001), turns ground truth from an
assertion into an agreement between independent witnesses.

Rasterizing at a fixed size is deterministic, and the measured values are frozen into the
dataset — so downstream reproduction never re-renders and never depends on the reproducer's
renderer build.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Analytic area as canonical | Diverges from perception on concave shapes; sign depends on winding |
| Bounding-box area | Badly wrong for diagonal or elongated shapes |
| Convex hull area | Better than bbox, still ignores concavity |
| Perceptual weighting (area^β, elongation-corrected) | Closer to human judgement, but introduces a free parameter with no principled value for this corpus. Deferred to `docs/BACKLOG.md` as a robustness check |

## Tradeoffs

- **Gained:** ground truth matches the perceptual claim the instructions make; two
  independent witnesses; deterministic and freezable.
- **Given up:** rasterization is DPI-dependent, so DPI becomes a config value inside the
  dataset hash. Accepted and explicit.
- **Known residual risk:** pixel coverage is still not *perceived* size. Human size judgement
  is compressive and sensitive to elongation, so a "1.3× area margin" is perceptually smaller
  than it reads. Two shapes with equal coverage but different elongation may not be judged
  equal. This is why separability margins exist and why a human-agreement sample is run
  against the predicate registry — the residual disagreement rate is measured and reported,
  not assumed to be zero.
