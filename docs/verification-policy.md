# Verification policy

One rule, promoted from FA-010 because it is a lesson about experimental design rather
than a bug that was fixed.

> **A verification fixture must be able to fail for a different reason than the
> implementation would fail.**
>
> The implementation and its oracle should solve the same problem *differently* wherever
> practical. Different code is not necessarily different reasoning.

## Where this came from

The leakage lint matched `"line "` as a bare substring, so it rejected every instruction
containing the word `"outline"` - which was every `add_stroke` case in the corpus.

The unit test written to independently verify that lint **contained the identical bug**
and failed on the identical instruction. It was written by the same person, on the same
day, from the same wrong mental model. It was different code. It was not different
reasoning, and only different reasoning provides assurance.

The lint failed loudly, so this cost nothing. A scorer with the same property would not
fail loudly. It would produce a number.

## What counts as independent reasoning

| Implementation | Weak oracle (mirrors it) | Independent oracle |
|---|---|---|
| Substring/regex lint | The same patterns, re-typed | Hand-authored strings with the expected verdict written down first |
| Structural diff scorer | A second diff written the same way | Hand-built input/output pairs, classified by eye, committed before the scorer exists |
| Allocation algorithm | Re-running the allocator and checking self-consistency | A manually authored allocation for one sample, asserted equal |
| Geometry engine | Re-deriving area with the same formula | A different implementation (raster vs analytic), plus known shapes with hand-computed answers |
| Permutation null | Trusting an analytic approximation | Simulating a distribution known to be uniform by construction |

The last two are already the strongest checks in the repository, and both got there by
this route: the geometry engine has two unrelated implementations that must agree
(ADR-0001, ADR-0004), and the leak detector was replaced after an empirical null showed
the analytic statistic was miscalibrated (FA-002).

## Practical tests before writing a fixture

1. **Would this fixture still fail if the implementation's core assumption is wrong?**
   If the fixture is derived from the implementation's own output, no.
2. **Was the expected value computed by a different method than the code uses?**
   Hand arithmetic, a second library, a known-answer shape, or a distribution that is
   uniform by construction all qualify. Re-running the code does not.
3. **Was the expected value written down before the implementation existed?**
   Not always possible, but it is the strongest form.

## Where this binds hardest

**Step 9, the evaluation engine.** Every claim after the pre-registration tag depends on
the scorer being right, and unlike the lint, a wrong scorer does not crash - it silently
produces a plausible number.

The review question for Step 9 is therefore not "do the fixtures pass" but:

> **Can the scorer be wrong while every fixture still passes?**

If the answer is *yes*, or *I don't know*, the fixture set is incomplete. Only
*"we actively tried to make it wrong and could not"* is grounds for freezing it.
