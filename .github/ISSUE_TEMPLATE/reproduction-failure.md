---
name: Reproduction failure
about: A committed number does not regenerate on your machine
labels: reproduction
---

**Which tier failed?**
- [ ] Tier 1 — `svgbench report` (no model, no renderer)
- [ ] Tier 2 — `svgbench evaluate` (no model, no renderer)
- [ ] Tier 3 — `svgbench verify --determinism` (needs renderer)
- [ ] Tier 4 — a model run (bit-exact reproduction is **not** claimed here)

**Expected vs observed**

<!-- Paste the relevant rows. results/metrics.json is the committed reference. -->

**Environment**

<!-- python --version, OS, and `pip freeze | grep -E 'resvg|svgelements|pydantic|numpy'` -->

**Note:** Tier 4 is not expected to reproduce bit-for-bit — local backends vary with
build and threading. What should reproduce is the conclusion, within the reported
interval. See README, "Reproducing the numbers".
