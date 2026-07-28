# ADR-0007 — 30 SVGs, and inference at the SVG level

**Date:** 2026-07-28 · **Status:** Accepted

## Decision

Generate **30** SVGs — the top of the assignment's 20–30 range. Resample and test at the
**SVG level**, not the case level. Use a paired **cluster-level permutation test** for
hypothesis testing, with cluster bootstrap for interval estimation.

## Why

**Why 30 and not 20.** The number of SVGs *is* the statistical sample size. Six instructions
sharing one SVG share a layout, a K, and an ambiguity set; they are not six independent
observations. Interval width is governed by cluster count, so taking the maximum the
assignment permits is the cheapest available precision. Adding instructions per SVG raises
case count without raising cluster count — it buys much less than it appears to.

**Why cluster-level resampling.** Case-level resampling would treat correlated cases as
independent, understate variance, and manufacture false precision. That would be a real
error, not a conservatism preference.

**Why permutation over bootstrap for testing.** Nonparametric bootstrap has poor coverage at
~30 clusters, and worse at proportions near 0 or 1 — which is exactly where the baseline arm
sits if it is at the `1/K` floor. A paired permutation test on per-SVG deltas is near-exact
under the sharp null and does not depend on that asymptotic. Pairing is valid because all arms
see byte-identical cases, and it is strictly more powerful than a two-sample comparison.

## Alternatives considered

| Option | Rejected because |
|---|---|
| 20 SVGs | Fewer clusters, wider intervals, no compensating benefit |
| More than 30 | Outside the assignment's stated range |
| More instructions per SVG instead | Raises `n` without raising cluster count; inflates within-cluster correlation |
| Case-level bootstrap | Statistically wrong here — ignores clustering |
| Normal-approximation CIs | Invalid near the `1/K` floor |
| t-test on per-SVG deltas | Assumes normality of cluster means with 30 clusters; permutation assumes less |

## Tradeoffs

- **Gained:** honest intervals; a test that behaves at this sample size and at floor
  proportions.
- **Given up:** precision. Thirty clusters is genuinely few, and the intervals will be wide.
  This cannot be fixed within the assignment's constraint, so the response is a **narrower
  claim**, not a better estimator: the minimum detectable effect is computed and reported
  *before* results, so a null outcome is interpretable rather than merely underpowered.
- **Given up:** the ability to make confident per-predicate claims from small strata.
  Per-predicate cells will be small; they are reported with intervals and explicitly framed as
  descriptive rather than confirmatory.
