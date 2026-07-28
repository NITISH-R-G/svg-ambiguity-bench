# Changelog

Sprint-by-sprint increments. Amendments to frozen design documents are recorded here as
required by [`DESIGN_FREEZE.md`](DESIGN_FREEZE.md).

## [Unreleased]

### Sprint 2, Step 1 — Repository scaffolding — 2026-07-28

**Added**
- Repository structure, MIT license, packaging (`pyproject.toml`), CI for Linux + Windows.
- `DESIGN_FREEZE.md` — architecture, protocol, scoring, metrics and layout frozen; amendment
  procedure and the pre-registration boundary defined.
- Frozen design record: `docs/00-prd.md`, `docs/01-architecture.md`,
  `docs/02-experiment-design.md` (the pre-registration), `docs/glossary.md`.
- `docs/adr/` — ten decision records covering the toolchain, redaction scheme, output format,
  canonical area, the runner seam, the primary metric, corpus size and inference, abstention,
  and the permuted-facts control. ADR-0010 (decoding policy) is deliberately left **pending**
  with a pre-committed resolution rule.
- `LIMITATIONS.md`, written before any results exist.
- `docs/BACKLOG.md` — out-of-scope ideas, so they stop competing for attention.
- Package skeleton: twelve subpackages, each documenting its responsibility.
- `svgbench` CLI: `status` works; unimplemented pipeline steps exit non-zero with an
  explanation instead of a traceback.
- Scaffold tests, including two architectural gates: pipeline layering is one-directional, and
  the scoring path cannot import a renderer.
- `Makefile` and `tasks.ps1` as thin wrappers over the same CLI, so Windows and POSIX
  reviewers run identical code paths.

**Design changes carried in from the adversarial review**
- Primary metric changed from strict accuracy to **identification accuracy** (ADR-0006).
- **Abstention** promoted to a first-class outcome class (ADR-0008).
- **`permuted` control arm** added and made blocking; the pre-registered primary comparison is
  now `enhanced` vs `permuted`, not `enhanced` vs `baseline` (ADR-0009).
- `legible` and `facts_only` arms added (ADR-0009).
- Reporting unit changed from family to **predicate**.
- Hypothesis testing changed from bootstrap to **paired cluster-level permutation**
  (ADR-0007).
- Contribution reframed: the enhanced arm is the benchmark, the baseline is a manipulation
  check.
- Predicate uniqueness now asserted against the full element set, not only the ambiguity set.

**Verified**
- Rendering stack probed before adoption: `resvg` and `svgelements` agree exactly on a known
  shape (2500/2500 px; analytic bbox exact). Recorded in ADR-0001.

**Not yet done**
- No experiments have been run. No results exist.
