# Study V2 results - target identification validation

Pre-registered at [`study-v2-preregistration`](05-study-v2-preregistration.md) before the
condition was implemented. The interpretation bands below were fixed in advance; this
document applies them and does not revise them.

---

## Primary outcome

**`A_named` = 0.9278** [0.8833, 0.9667], 180 cases, 30 clusters, cluster bootstrap over
SVGs.

| Band | Condition | Result |
|---|---|---|
| **A** | `A_named >= 0.50` | **← this one** |
| B | `0.1852 <= A_named < 0.50` | |
| C | `A_named < 0.1852` | |

The pre-registered conclusion for band A, quoted unchanged from the registration:

> Execution is substantially intact. Reading **R1** is supported: the model can perform
> these edits when told which element to edit, so V1's null is attributable to reference
> resolution rather than to inability to execute. **V1's interpretation strengthens.**

**I predicted band C.** The registration says so explicitly - *"Band C is the outcome that
damages the project most, and it is the one I consider most likely."* That prediction was
wrong, and it was wrong in the direction that favours the project, which is exactly the
direction in which a prediction made after the fact would not have been trustworthy.

---

## The comparison that matters

Same 180 cases. Same 30 SVGs. Same target element per case. Same model, decoding, prompt
template and scorer. The only thing that changes is whether the instruction *describes*
the target or *names* it.

| condition | how the target is specified | identification accuracy | `NO_EDIT` |
|---|---|---|---|
| `baseline` | described, no geometry given | 0.0444 [0.0167, 0.0778] | 0.444 |
| `permuted` | described, geometry given but scrambled | 0.0444 [0.0167, 0.0778] | 0.483 |
| `enhanced` | described, correct geometry given | 0.0444 [0.0167, 0.0778] | 0.478 |
| **`named_id`** | **named by id** | **0.9278 [0.8833, 0.9667]** | **0.067** |

Paired cluster-level permutation, `named_id` against each V1 arm:

| comparison | difference | p | clusters |
|---|---|---|---|
| `named_id` - `baseline` | **+0.8833** | 0.0001 | 30 |
| `named_id` - `permuted` | **+0.8833** | 0.0001 | 30 |
| `named_id` - `enhanced` | **+0.8833** | 0.0001 | 30 |

p = 0.0001 is the floor at 10,000 permutations - `(0 + 1) / (10000 + 1)`. No permutation
of the cluster labels produced a difference as large as the observed one. Read it as
*"below the resolution of this test"*, not as a precise probability. The MDE for this
design is 0.0404; the observed effect is roughly **twenty-two times** that.

---

## What this establishes

The model performs these operations at 0.93 when the element is identified for it, and at
0.04 - indistinguishable from supplying nothing - when the element must be picked out
from a description.

Stated at the width the evidence supports: **under this corpus, this prompt template,
this scorer and this model, explicit element ids produce high edit accuracy while
descriptive references do not, even with exact geometry supplied.** That is a statement
about a measured dissociation, not about the model's cognition. The tempting shorter
version - *"the model cannot work out which element is meant"* - asserts a general
inability this design cannot establish, and is avoided deliberately.

Within that scope the ambiguity V1 could not resolve is resolved:

- **R2 (execution) is rejected.** Inability to perform the edit does not explain V1's
  null. The capability is present and the manipulation had ample headroom to act in.
- **R1 (reference resolution) is supported** as the locus of the failure *in this
  setting*. What remains unexplained is the mechanism - see "What this does not
  establish" below.

The `NO_EDIT` rate is the clearest single number. It falls from **0.444-0.483** across
the V1 arms to **0.067** here - a factor of about seven. The V1 declines were not the
model failing to edit. They were the model declining *because it could not tell which
element to edit*, which is the behaviour the prompt explicitly invites:

> If the document does not contain enough information to identify which element the
> instruction refers to, say so instead of guessing.

Read against V1, that reframes the 44% from a symptom of incapacity into evidence of
appropriately-calibrated refusal.

## Secondary outcomes

**Per operation.** No operation is broken; the spread is narrow and the floor is high.

| operation | accuracy | `NO_EDIT` |
|---|---|---|
| `recolor_fill` | 1.0000 (44/44) | 0 |
| `add_stroke` | 0.9545 (42/44) | 2 |
| `delete` | 0.8958 (43/48) | 4 |
| `rotate` | 0.8636 (38/44) | 6 |

Uniform failure would have been consistent with R2. This is not that. Even `rotate`, the
weakest, sits nineteen times above the V1 arms.

**By family.** `SPATIAL` 0.9444 (85/90), `ORDINAL_SIZE` 0.9111 (82/90). Both families are
executable; neither is carrying the result.

**Malformed** 0/180. **Abstained** 0/180. Both match V1 exactly.

## Falsifier check

Both pre-registered falsifiers were evaluated before the primary outcome was interpreted.

| Falsifier | Status |
|---|---|
| Malformed rate materially above V1's 0 | **Clear** - 0/180, identical to V1 |
| `A_named` far below `baseline`'s 0.0444 | **Clear** - it is far above |

The malformed check required an intervention worth recording. A first pass produced 14
`MALFORMED` cases, which would have tripped the falsifier. All 14 carried
`ConnectError: [WinError 10061]` - the local model server had stopped during a session
interruption. They were not model outputs at all. Compounding it, the runner had **stored
the failures as completed records**, so resuming skipped them rather than retrying. The
errored rows were deleted, the server restarted, the 14 cases re-run, and the reported
figures come from 180 responses with zero transport errors.

That defect is the same shape as FA-012: a failure that presents as a result. Had it gone
unexamined it would have depressed `A_named` from 0.9278 to 0.8611 and produced a
spurious 7.8% malformed rate - still band A, so the conclusion would have survived, but
two published numbers would have been wrong and one falsifier would have appeared to
trip.

---

## What this does not establish

- **Nothing about other models.** One 3B model. The gap between 0.93 and 0.04 is large
  enough to be interesting, not large enough to be general.
- **Nothing about real SVGs.** The corpus is synthetic, with opaque geometry tokens that
  do not occur in practice.
- **It does not exercise the format-matched control.** V2 raises identification accuracy
  by removing the identification problem, not by supplying better information. The V1
  treatment effect remains zero, so there is still no quantity for the control to
  decompose. The central methodological contribution is still unexercised - see
  `LIMITATIONS.md`.
- **It does not explain *why* reference resolution fails.** Whether the model cannot
  parse the geometry table, cannot compare coordinates, or cannot connect a spatial
  description to numeric positions is not distinguished here.

## Effect on V1

Per the registration, V1's numbers, claims, scoring, corpus and freeze are unchanged, and
`instrument-freeze-v1` is not superseded. What changes is interpretation:

- V1's null is now **specific**: context did not improve reference resolution, in a
  setting where the model demonstrably could execute the requested edits.
- The construct-validity threat *"this may be measuring execution capability rather than
  reference resolution"* is **retired**, with a measurement rather than an argument.
- V1's 44% `NO_EDIT` rate is reinterpreted as calibrated refusal rather than incapacity.

The claim-strength entry that read *"the task measures reference resolution - THREATENED,
44% NO_EDIT, execution capability uncontrolled"* is now **supported**.
