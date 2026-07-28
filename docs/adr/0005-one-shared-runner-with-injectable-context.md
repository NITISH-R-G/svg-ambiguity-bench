# ADR-0005 — One shared runner with an injectable ContextProvider

**Date:** 2026-07-28 · **Status:** Accepted

## Decision

There is **one** runner and **one** prompt template. Arms are produced by injecting a
different `ContextProvider` into the template's single context slot:

```
ContextProvider :: (model_visible_svg, svg_id) -> ContextBlock
```

`baseline` is the null implementation, returning an empty block.

## Why

**Fairness must be structural, not procedural.** If the arms were two separately-authored
prompts or two pipelines, they would drift — a retry policy tweaked here, a stop sequence
added there — and no amount of care downstream would recover the comparison. With one path,
the only thing that *can* differ is the injected block, and a mechanical prompt diff proves it.

**The signature is the leakage defence.** Note what is absent: the instruction is not a
parameter. A contributor cannot leak the instruction into the enhancement, accidentally or
otherwise, because it is not reachable from inside a provider. This is a stronger guarantee
than a code review or a runtime assertion, because it holds for code nobody has written yet.

**Caching per SVG is a proof, not an optimization.** Context is computed once per SVG and
reused across all its instructions. If the same block serves six different instructions, it
demonstrably does not depend on any of them.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Two scripts, one per arm | Guaranteed drift; the comparison becomes unverifiable |
| One script with `if arm == "enhanced"` branches | Better, but branches multiply and the diff between arms stops being mechanically checkable |
| Runtime assertion that the instruction was not used | Detects only what it thinks to check; a type-level exclusion cannot be bypassed |
| Provider receives the instruction but promises not to read it | Not a guarantee at all |

## Tradeoffs

- **Gained:** fairness is enforced by construction; blindness is enforced by the type system;
  adding an arm is adding one class.
- **Given up:** a provider genuinely needing the instruction (say, a retrieval-style method
  that fetches only relevant facts) cannot be expressed. Accepted deliberately — such a method
  would be conditioning on the query, which is the thing this design exists to forbid.
- **Residual limitation this does NOT fix:** the signature blinds the *code*, not the
  *designer*. Choosing to emit centroid and area is itself informed by knowing which predicate
  families are tested — task-distribution conditioning at design time. That is normal and
  defensible, but it is a real limit on the generality claim and is stated in
  `docs/02-experiment-design.md` §9.3 rather than papered over.
