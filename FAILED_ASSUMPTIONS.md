# Failed assumptions

Every time this project proved itself wrong. Recorded because the same conceptual
mistake returns six months later otherwise, and because a benchmark that never documents
being wrong is either very lucky or not looking.

Each entry: what was assumed, what the evidence said, what changed, and what it would
have cost had it gone unnoticed.

The pattern worth noticing: **all six were found by asking what would falsify an
assumption, none by asking whether a test passed.** Every one of them left the system
internally consistent, which is exactly why they would have survived a conventional
test suite.

---

## FA-001 - `center_x` was not the centroid

| | |
|---|---|
| **Assumed** | `ElementIntent.center_x` was the element's centroid |
| **Evidence** | Analytic area centroid 186.53 vs recorded 183.29 - a ~3 unit gap. Vertex radii are jittered, so an irregular blob's area centroid drifts from the point it was constructed around |
| **Resolution** | Renamed to `placement_x`/`placement_y`, with the distinction documented at the field |
| **Impact if missed** | Every spatial predicate - `leftmost`, `top_left`, `topmost` - would have resolved against the construction anchor instead of the centroid. Wrong by a few units on every case, internally consistent, and invisible to every downstream test |
| **Found by** | Asserting equality between two quantities that *should* have been equal, and believing the measurement over the label |
| **Step** | 4 |

## FA-002 - the analytic z-score was not valid for this data

| | |
|---|---|
| **Assumed** | `rho * sqrt(n-1)` is approximately standard normal, so `\|z\| < 3.5` is a sound leak threshold |
| **Evidence** | Under a shuffle that is uniform **by construction**, the statistic has mean **+0.880**, not 0, across 2000 draws. Positions and attribute ranks both run `0..K-1` within an SVG, so pooling across SVGs with differing K induces association from group size alone |
| **Resolution** | Replaced with an empirical permutation null - exact, tie-safe, no distributional assumption |
| **Impact if missed** | The project would have reported a generator leak that does not exist. A 25-seed sweep showed mean z = +1.605 at 8.95 SE from zero, which reads as damning until the null is measured rather than assumed |
| **Found by** | Refusing to accept a borderline result (z = +2.76, within threshold) without checking whether it was systematic |
| **Step** | 3 |

## FA-003 - ordinal ranks were adequate for tied data

| | |
|---|---|
| **Assumed** | A stable sort producing ordinal ranks is a fine Spearman implementation |
| **Evidence** | The pooled data is almost entirely ties. Stable sorting resolves every tie by append order, which is identical in both vectors, manufacturing correlation from nothing. Accounted for roughly a third of the spurious signal in FA-002 |
| **Resolution** | Midranks - tied values share their average rank |
| **Impact if missed** | Compounded FA-002. Either alone might have been dismissed as noise; together they looked like a real generator defect |
| **Found by** | Decomposing an anomaly instead of fixing the first plausible cause |
| **Step** | 3 |

## FA-004 - there were not three independent witnesses

| | |
|---|---|
| **Assumed** | Generator intent, analytic geometry and raster coverage are three independent measurements, so agreement among them is strong evidence |
| **Evidence** | Intent and analytic both apply the shoelace formula. They differ only in whether the vertices came from the generator's memory or from parsing the serialised `d` string |
| **Resolution** | Reclassified. Intent vs analytic is a **serialisation** check; the independent witness is the rasteriser. Corrected in `CLAIMS.md`, the architecture doc and the module docstrings |
| **Impact if missed** | An overstated independence claim in the write-up - the kind of thing a reviewer catches and then distrusts the rest of the paper for |
| **Found by** | Writing down precisely what each witness computes, rather than what each was called |
| **Step** | 4 |

## FA-005 - the geometry tolerances were meaningful

| | |
|---|---|
| **Assumed** | Area tolerance 0.05 and centroid tolerance 1.5 were sensibly conservative |
| **Evidence** | Observed maximum disagreement across 110 elements: **0.0014** area, **0.030** centroid. The bounds sat 35x and 50x above the observed maximum |
| **Resolution** | Tightened to 0.02 and 0.5, roughly 14x headroom. Calibrated from the instrument's own noise, before any model runs |
| **Impact if missed** | A gate that cannot fire is decoration. A genuine 2% measurement degradation would have passed silently |
| **Found by** | Comparing the tolerance against the measured distribution instead of against intuition |
| **Step** | 4 |

## FA-006 - PowerShell round-trips were safe for UTF-8 documents

| | |
|---|---|
| **Assumed** | `Get-Content -Raw` / `Set-Content -Encoding utf8` round-trips markdown losslessly |
| **Evidence** | Em-dashes and check marks became mojibake in `CLAIMS.md` and `EVIDENCE.md` |
| **Resolution** | Files rewritten through the editor; non-ASCII punctuation removed from those documents; repo-wide scan confirms clean |
| **Impact if missed** | Cosmetic, but in the two documents a reviewer reads first. Low severity, recorded because it is a recurring operational trap rather than a one-off |
| **Found by** | Reading back what was written instead of trusting the write |
| **Step** | 4 |

## FA-007 - the spatial margin threshold was set without data

| | |
|---|---|
| **Assumed** | `min_spatial_margin = 0.15` was a sensible "obviously the winner" threshold |
| **Evidence** | It landed almost exactly on the **median** of the observed margin distribution (0.146), refusing **52%** of spatial predicates and leaving **13 of 30 SVGs** unable to supply the three spatial instructions the design needs |
| **Resolution** | Reset to **0.08** on perceptual grounds - roughly one shape's own radius on a 512 canvas, the scale at which "further left" stops being a judgement call. Margin refusals fell to 11.4%; valid predicates rose from 56.9% to 65.6% |
| **Impact if missed** | The instruction generator at Step 7 would have failed to fill its budget, and the natural fix under deadline pressure is to quietly weaken the guarantee rather than question the threshold |
| **Found by** | Measuring the rejection rate the gate actually produced, instead of assuming a plausible-looking constant was harmless |
| **Step** | 5 |

### The test that should have caught it, and did not

`test_every_sample_can_host_both_families` asserted at least one valid predicate per
family. Every sample passed - the minimum really was 1. But the design needs *three*
spatial predicates per SVG, and availability is a **corpus-level** property that a
per-sample minimum cannot see.

Added `test_corpus_supplies_enough_predicates_for_the_instruction_budget`, which compares
total supply against total demand. The lesson generalises: when a requirement is about an
aggregate, asserting it per-item is not a weaker version of the same check, it is a
different check that can pass while the requirement fails.

## FA-008 - lowering the margin would not have been enough anyway

| | |
|---|---|
| **Assumed** | Per-SVG spatial shortfall was purely a threshold problem, fixable by tuning |
| **Evidence** | Sweeping the threshold down to 0.03 still left 4 SVGs short and a per-SVG minimum of 1. `definition_disagreement` (9.4%) and `distractor_outranks_target` (13.1%) are validity *requirements*, not tunable thresholds - no setting makes them go away |
| **Resolution** | Accepted uneven per-SVG availability as a property of the corpus. Instruction allocation at Step 7 must adapt to what each sample can host and balance at the corpus level, rather than assuming a fixed within-SVG split. Asserted by a test so Step 7 inherits the constraint explicitly |
| **Impact if missed** | Step 7 would have been written assuming a uniform 3+3 split and failed on roughly a third of the corpus |
| **Found by** | Sweeping the parameter rather than tuning it to the first value that looked acceptable |
| **Step** | 5 |

---

## What this list is for

When a future change touches spatial predicates, FA-001 says which field is *not* the
centroid. When a future analysis pools across groups of unequal size, FA-002 says the
asymptotic statistic is miscalibrated there. When a future tolerance is chosen, FA-005
says to check it against a measured distribution.

It also feeds the write-up directly: this is the lessons-learned section, written while
the lessons were still being learned rather than reconstructed afterwards.
