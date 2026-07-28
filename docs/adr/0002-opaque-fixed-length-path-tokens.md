# ADR-0002 — Opaque, fixed-length path tokens

**Date:** 2026-07-28 · **Status:** Accepted

## Decision

Replace the `d` attribute of every ambiguity-set element with an explicit, self-describing,
**fixed-length** token: `d="{{GEOM_7f3a91c2}}"`. The token↔geometry map lives in a sidecar,
never in a model-visible file. All positional information must live inside `d` — no
`transform`, `x`, `y`, `cx`, or `cy` on ambiguity-set members.

## Why

**Explicit token rather than mangled coordinates.** A model shown plausible-but-wrong path
data will try to repair it, converting an identification experiment into a syntax experiment.
An obviously-redacted marker, paired with an instruction to preserve it verbatim, keeps the
measured failure mode the one we intend to measure.

**Fixed length is mandatory, not cosmetic.** Path complexity correlates with shape size. A
variable-length token would leak size through byte count — a side channel that would quietly
inflate baseline accuracy and destroy the premise while every test still passed.

**No positional attributes.** A single `transform="translate(x,y)"` would put position in
plain sight. This is the easiest way to accidentally invalidate the whole benchmark, so it is
a generator invariant with an automated audit check rather than a convention.

**Free bonus:** the token is unique per element and preserved by contract, so it doubles as
the primary identity anchor for scoring alignment — surviving a model that renames `id`s.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Leave real path data | Position becomes recoverable with effort; the ambiguity is not guaranteed. Retained instead as the separate `legible` control arm |
| Randomize coordinates | Still legible as coordinates; ground truth would no longer match the render |
| `<use href="#glyph_7"/>` against hidden `defs` | Cleaner XML, but changes the element tag and breaks the same-tag requirement |
| Variable-length hash tokens | Leaks path complexity through length |

## Tradeoffs

- **Gained:** the ambiguity is guaranteed by construction, not argued for. Stable scoring
  anchor for free.
- **Given up:** model-visible SVGs do not render. Intended — if they rendered, position would
  be recoverable.
- **Given up:** external validity. Opaque tokens do not occur in real SVGs, so the baseline
  failure rate mixes an ambiguity effect with an out-of-distribution-format effect. This is
  the single largest threat to the result's meaning, and it is why the `legible` arm exists
  (ADR-0009) and why it is stated in `LIMITATIONS.md` rather than defended.
