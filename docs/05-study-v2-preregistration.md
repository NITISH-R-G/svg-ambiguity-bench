# Study V2 - target identification validation

**Status: PRE-REGISTERED. No model output for this condition has been observed.**

This document is written before the condition is implemented or run. Its predictions and
decision rules bind the interpretation of whatever comes back. If the analysis below is
edited after results exist, the edit is an amendment and must be disclosed as one, with
the pre-change text retained.

---

## Why this study exists

Study V1 measured a constrained null: `baseline`, `permuted` and `enhanced` all scored
identification accuracy **0.0444**, every pairwise difference **0.0000**, minimum
detectable effect **0.0289**.

V1 also recorded that the model declined to edit at all in **44-48%** of cases
(`NO_EDIT`). That number admits two incompatible readings, and V1 cannot distinguish
them:

| Reading | Claim | Consequence for V1 |
|---|---|---|
| **R1 - reference resolution** | The model can perform these edits. It cannot determine *which* element a geometric description refers to | V1 measured what it intended to measure. The null is informative about reference resolution |
| **R2 - execution** | The model cannot reliably perform these edits even when the target is unambiguous | V1's manipulation had no room to act. The null is largely uninformative about reference resolution |

Under R2, supplying better geometry could not have helped regardless of how good the
geometry was, because the bottleneck lies downstream of identification. A reader
encountering V1 will ask this within the first minute, and the honest answer today is
that the repository does not know.

**This study is designed to answer exactly that question and nothing else.**

## What this study is not

It is not a fourth arm of V1. V1 is complete, frozen, and its numbers do not change as a
result of anything measured here. V2 is a separate study that varies a different
independent variable, and its result is recorded as *interpretation* of V1 rather than
as a revision of it.

It is also not an attempt to rescue a null. The rule in `RESULTS.md` prohibits adding
arms to explain a result already in hand. This study is admissible because it does not
seek to change V1's measurement, its scoring, or its claims. It seeks to establish which
of two pre-existing readings of that measurement is correct - a question that was
recorded as open in `docs/essay.md` before any of this was run.

---

## Manipulation

V1 varied **context**, holding the instruction fixed. V2 varies the **instruction**,
holding context fixed at `baseline` (none).

That difference is forced by the architecture, and the constraint is worth stating
because it independently confirms the study's separateness. The `ContextProvider`
protocol is

```python
def provide(self, svg_id: str, geometry: dict[str, ElementGeometry]) -> str
```

There is no instruction parameter - instruction-blindness is enforced by the type
signature (ADR-0005). A provider therefore *cannot* know which element is the target,
because the target is a property of the instruction. Naming the target is not
expressible as a context arm. It has to be an instruction condition, which is precisely
why it belongs in a different study.

Concretely, for every one of the 180 frozen cases, the referring expression is replaced
by an explicit element reference while the operation and its parameters are preserved:

```
V1   Change the fill of the top-left shape to #ff0000.
V2   Change the fill of the element with id="e13415408" to #ff0000.
```

Everything else is held constant: the same 30 SVGs, the same 180 cases, the same target
element per case, the same prompt template, the same model, the same decoding settings,
the same scorer, the same metrics, the same cluster-level inference.

The ground-truth target element is unchanged, so **the scorer requires no modification**
and is used exactly as frozen.

---

## Primary outcome

**Identification accuracy in the `named_id` condition**, written `A_named`: the fraction
of the 180 cases scored `CORRECT_STRICT` or `CORRECT_LOOSE`, computed by the frozen
scorer, with a cluster bootstrap over the 30 SVGs.

## Pre-registered interpretation bands

These bands are fixed now. The band that `A_named` falls into determines the conclusion,
and the conclusion is written below for each band before the value is known.

| Band | Condition | Conclusion |
|---|---|---|
| **A** | `A_named >= 0.50` | Execution is substantially intact. Reading **R1** is supported: the model can perform these edits when told which element to edit, so V1's null is attributable to reference resolution rather than to inability to execute. **V1's interpretation strengthens.** |
| **B** | `0.1852 <= A_named < 0.50` | Execution is partial. Neither reading is cleanly supported; the V1 null reflects some mixture of both constraints, and the mixture is not separable with this design. **V1's interpretation is qualified and must say so.** |
| **C** | `A_named < 0.1852` | Execution is the binding constraint. Naming the target explicitly does no better than the V1 random-selection reference. Reading **R2** is supported: V1's manipulation had no headroom, and V1's null is **substantially uninformative about reference resolution**. |

**On the boundaries.** 0.1852 is not arbitrary - it is V1's own per-case random-selection
reference, the score obtained by picking uniformly among the K candidate elements. If
explicitly naming the target does not beat blind guessing among the candidates, the model
is not performing the task in any meaningful sense. 0.50 is a judgement call, chosen as
the point at which a majority of cases succeed; it is set now, at a moment when I do not
know which side of it the answer falls on, which is the only condition under which such a
threshold can be set honestly.

**Band C is the outcome that damages the project most, and it is the one I consider most
likely** given a 3B model and a 44% no-edit rate. Writing that down now is the point.

---

## Secondary outcomes

Reported regardless of the primary result. None of them can override the band above.

1. **`NO_EDIT` rate** in `named_id`, against V1's 0.444 / 0.483 / 0.478. This is the
   most direct measure of execution capability and is expected to move together with
   `A_named`.
2. **Paired comparison `named_id` vs `enhanced`**, same 180 cases, paired cluster-level
   permutation test at the SVG level - the identical procedure V1 used. Reported with
   the MDE, and with the same standing instruction: if the difference is exactly zero,
   the p-value is degenerate and the MDE is the number that carries information.
3. **Per-operation breakdown** across `recolor_fill`, `add_stroke`, `delete`, `rotate`.
   If execution capability is strongly operation-dependent - for instance, if `delete`
   succeeds and `rotate` never does - that is a materially different finding from
   uniform failure, and it is not visible in the aggregate.
4. **Malformed-output rate.** V1 had 0/180 in every arm.

## Manipulation checks

Run before the primary outcome is computed, because each of them can invalidate the
study rather than inform it:

- Every generated instruction contains the target element's id, verbatim. Asserted per
  case, not sampled.
- The id named is the ground-truth target for that case. Asserted per case.
- The operation and its parameters are byte-identical to V1's for the same case.
- Prompts differ from the V1 `baseline` prompts **only** within the instruction line.
- The 180 case ids are exactly V1's 180 case ids.

If any check fails, the run is void and no outcome is reported from it.

## Falsifiers for this study

- **A malformed rate materially above V1's 0.** Naming an element by id should not make
  the output harder to parse. If it does, the manipulation is doing something other than
  what it claims, and the primary outcome is not interpretable.
- **`A_named` far below `baseline`'s 0.0444.** Supplying strictly more information
  should not perform worse than supplying none. That pattern would indicate the
  instruction rewrite broke something rather than that execution is weak.

---

## What may and may not change as a result

**May change:** `docs/04-results.md` gains an interpretation section citing this study.
`VALIDITY.md` gains or resolves a construct-validity threat. `LIMITATIONS.md` is updated
where this study narrows or widens a stated limitation. `README.md` may state which
reading is supported.

**May not change:** V1's corpus, scoring rules, predicates, leakage checks, evaluation
rules, arm definitions, or reported numbers. The claims C1-C8 keep their V1 outcomes.
`instrument-freeze-v1` is not superseded, reissued, or amended.

If band C obtains, `README.md` and `docs/04-results.md` must say so **in the same
position and with the same prominence** they would have given band A. The operational
test from `RESULTS.md` applies unchanged:

> Would this change have been made identically had the result come out the other way
> around?

---

## Analysis plan

Fixed before running:

- Primary: `A_named` with a 95% cluster bootstrap interval over the 30 SVGs, 10,000
  resamples, the same procedure and seed policy as V1.
- Paired: `named_id` - `enhanced`, cluster-level paired permutation, 10,000 permutations,
  reported with MDE.
- No other comparison is promoted to a headline. Anything additional is exploratory and
  is labelled as such.
- One replicate, greedy decoding, matching V1. No replicate count is chosen after seeing
  variance.

## Registration

This document is committed and tagged **before** the `named_id` condition is implemented
and **before** any model output for it exists.

```
tag  study-v2-preregistration
```

The tag message records the commit, the V1 dataset hash, and the line
`NO V2 MODEL OUTPUTS HAVE BEEN OBSERVED.`
