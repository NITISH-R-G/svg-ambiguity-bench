# ADR-0001 — Toolchain and rendering stack

**Date:** 2026-07-28 · **Status:** Accepted

## Decision

Target **Python 3.12** (not the machine default 3.14). Geometry via **`svgelements`**
(analytic, pure Python), rasterization via **`resvg-py`** (Rust binary wheels), PNG decoding
via **Pillow**.

## Why

Verified empirically before committing, because a renderer that does not install on Windows
would have surfaced at implementation step 4 and invalidated a week of scaffolding:

- Python 3.14 is too new for reliable scientific/rendering wheels; 3.12 has them.
- `resvg-py` ships prebuilt Rust wheels — no system Cairo, no DLL hunt on Windows.
- Probe result: a 50×50 square rendered to **exactly 2500 opaque pixels**, and
  `svgelements` returned the exact analytic bbox `(10, 10, 60, 60)`. Both deterministic,
  both agreeing.

The independence is the real reason for this pairing. Ground truth is only meaningful because
two witnesses agree, and a Rust rasterizer and a pure-Python path algebra library share no
code. Had both come from one library, agreement would demonstrate consistency, not
correctness.

## Alternatives considered

| Option | Rejected because |
|---|---|
| `cairosvg` | Needs system Cairo on Windows; the install failed during probing |
| `svglib` + `reportlab` | Pure Python but shares a geometry lineage with the analytic path — weakens witness independence |
| Rasterize by flattening `svgelements` paths with Pillow ourselves | Fully deterministic and portable, but both witnesses would derive from one code path, which is exactly what the design needs to avoid |
| Python 3.14 (machine default) | Wheel availability unverified for the geometry stack |

## Tradeoffs

- **Gained:** genuine measurement independence; clean Windows install; deterministic output.
- **Given up:** a second native dependency (Rust wheel) that must be pinned per platform.
  Mitigated by freezing measured geometry into the dataset, so downstream reproduction never
  re-renders and never depends on the reproducer's renderer build.
- Contributors on 3.13/3.14 must create a 3.12 environment. Accepted; pinned in
  `pyproject.toml`.
