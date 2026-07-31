---
name: Independent implementation report
about: You implemented the format-matched control in another language and ran the conformance vectors
title: "[impl] <language> — conformance report"
labels: independent-evidence
---

<!--
This is the most valuable contribution the project can receive, and it is worth more
than anything the author can add alone. An implementation written from SPEC.md by
someone else tests whether the specification is actually sufficient - which is a claim
the author cannot check, having written both.

A report is welcome whether it passes or fails. A failure is more useful: it means the
specification is ambiguous somewhere, and that is a defect in the spec, not in you.
-->

## Implementation

- **Language / runtime:**
- **Link (if public):**
- **Spec version implemented:** <!-- from conformance_vectors.json, e.g. 1.0 -->
- **Conformance level attempted:** <!-- Level 1 (invariants only) or Level 2 (bit-exact vectors) -->

## Did you read the Python?

- [ ] No — implemented from `SPEC.md` alone
- [ ] Partly
- [ ] Yes

<!--
Not a judgement. It calibrates the result: an implementation written without reading the
reference is a much stronger test of the specification than one written alongside it.
-->

## Level 1 — invariants

| invariant | holds? |
|---|---|
| I1 entity preservation | |
| I2 order preservation | |
| I3 multiset preservation | |
| I4 displacement | |
| I5 determinism | |
| I6 key sensitivity | |
| I7 seed independence | |
| I8 purity | |
| I9 refusal over degradation | |

## Level 2 — vectors

<!-- Only if you attempted bit-exact reproduction. Level 1 alone is a complete and
useful report; Level 2 is only needed to reproduce this project's published prompts. -->

| vector id | matched? | notes |
|---|---|---|
| basic-3 | | |
| k4-tuples | | |
| k7-tuples | | |
| same-key-different-seed | | |
| same-seed-different-key | | |
| partial-ties | | |
| strings | | |
| unicode-key | | |
| negatives-and-floats | | |
| large-16 | | |
| single-entity (must raise) | | |
| all-values-equal (must raise) | | |

## Where the specification was unclear

<!--
The most useful section. Any place you had to guess, infer from the Python, or make a
choice the spec did not determine is a specification defect. Please list them even if
your implementation ended up matching.
-->

## Anything else
