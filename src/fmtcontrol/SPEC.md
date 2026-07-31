# Format-Matched Control — Specification v1.0

A format-matched control is a third experimental arm that is **format-identical** to a
context-augmented arm and **information-destroyed** relative to it.

This document specifies it precisely enough to implement in any language without reading
the Python. Conformance is checkable against
[`conformance_vectors.json`](conformance_vectors.json).

---

## 1. Scope

Given a set of entities, each carrying a fact, and a renderer that turns
entity→fact into prompt text, produce a second mapping that renders to text of the same
shape while carrying no information about which entity has which fact.

**Out of scope:** the renderer. It belongs to the caller. See §6.

## 2. Definitions

| term | meaning |
|---|---|
| **entity** | something the prompt refers to — a document, a tool, an element, a memory |
| **fact** | the value attached to one entity. Opaque; moved wholesale, never inspected or modified |
| **treatment** | the mapping entity→fact as it truly is (`enhanced`) |
| **control** | a mapping over the same entities, values redistributed (`permuted`) |
| **key** | an identifier for the item being permuted. Determines the permutation |
| **seed** | an experiment-level integer, combined with the key |

## 3. Invariants

An implementation is conformant only if every invariant holds for every input it accepts.

> **I1 — Entity preservation.** The control has exactly the entities of the treatment.
> No additions, no removals.

> **I2 — Order preservation.** Iteration order is identical. Row order must not become a
> difference between arms.

> **I3 — Multiset preservation.** The multiset of values is identical. Values are moved,
> never modified, generated, or dropped. This is what makes the arms information-matched
> in aggregate.

> **I4 — Displacement.** At least one entity is associated with a different value, compared
> **by value, not identity**. Two equal values exchanging positions is not displacement,
> because the rendered text is unchanged.

> **I5 — Determinism.** The same `(facts, key, seed)` yields the same control, on any run,
> in any process, in any order, under any parallelism.

> **I6 — Key sensitivity.** Different keys yield different permutations with high
> probability. Items must not share one shuffle.

> **I7 — Seed independence.** The seed must be independent of any seed used to generate
> the data. Otherwise the permutation can correlate with the structure it is meant to be
> independent of.

> **I8 — Purity.** The input mapping is not modified.

> **I9 — Refusal over degradation.** When no valid control exists, the implementation
> **must raise** rather than return something control-shaped. Two such cases:
> fewer than two entities (§5.1), and all values equal (§5.2).

## 4. Algorithm

```
permute(facts, key, seed):
    entities <- keys of facts, in iteration order
    values   <- values of facts, in the same order

    if len(entities) < 2:  RAISE                          # I9
    digest <- SHA-256( UTF-8 bytes of "{seed}:{key}" )
    rng    <- MT19937 seeded with big-endian uint64 of digest[0:8]

    repeat up to 64 times:
        shuffled <- Fisher-Yates(values, rng)
        if any position differs by value:                  # I4
            return mapping(entities -> shuffled)
    RAISE                                                  # I9
```

The digest is over `"{seed}:{key}"` — decimal seed, ASCII colon, key as UTF-8. A
locale-dependent or UTF-16 encoding diverges; the `unicode-key` vector exists to catch
exactly that.

## 5. Boundary cases

### 5.1 Fewer than two entities

Every permutation of fewer than two elements is the identity, so no control exists. The
item cannot be format-matched and must be excluded from the experiment or reported
separately. **Raise.** Returning the input unchanged hands back an arm that looks like a
control, is a second copy of the treatment, and will not fail any downstream test.

### 5.2 All values equal

No permutation displaces anything, so the control would render byte-identically to the
treatment. **Raise**, for the same reason.

### 5.3 Partial ties

Some values equal, some not: permit, provided I4 holds by value. The `partial-ties` vector
pins this.

## 6. Renderer requirements

**The same renderer must produce both arms.** This is not advice; it is the condition
under which the arms are format-matched at all. An implementation that renders internally
cannot guarantee it and should not try.

It follows that the API must accept and return **structured** entity→fact mappings, not
rendered strings. Once text exists, the distinction between value, format and renderer is
gone, and no implementation can determine whether it is producing a valid control. This is
an information-theoretic boundary, not a stylistic preference.

## 7. Validation

An implementation should also provide checks over a candidate control, since the failures
above are silent:

| check | catches |
|---|---|
| I1, I2, I3, I4 | a permutation that altered, reordered, or failed to move information |
| token count within tolerance | prompt length becoming a confound |
| line count identical | arms not actually format-matched |
| rendered texts differ | no manipulation occurred |

Tolerance on token count is necessary because values of differing width can shift
alignment padding. Report the delta rather than only a verdict.

## 8. Conformance levels

**Level 1 — Invariant conformance.** All of §3 hold for all accepted inputs, and §5 raises.
Sufficient for running valid experiments. **Portable: any PRNG may be used.**

**Level 2 — Vector conformance.** Reproduces `expected_permuted_values` in
`conformance_vectors.json` exactly, and raises on every `must_raise` case. Required to
reproduce prompts from a published experiment bit-for-bit.

### The Level 2 wart, stated plainly

Level 2 requires **MT19937 as implemented by CPython's `random.Random`**, and Fisher-Yates
as implemented by CPython's `random.shuffle` (descending index, `j = _randbelow(i + 1)`,
`_randbelow` via `getrandbits`). That is reimplementable — MT19937 is standard and
`shuffle` is short — but it is a genuine burden, and it is not a design choice.

It is inherited. The corpus, prompts and published numbers of
[svg-ambiguity-bench](../../README.md) were frozen against this pipeline before any model
output was observed. Substituting a portable PRNG would change every permutation and
break byte-identity with 540 committed prompts, so it cannot be changed retroactively
without invalidating the frozen instrument.

**A v2 of this specification should define a portable PRNG** — ChaCha20 or a
SHA-256-counter stream — so Level 2 costs nothing extra. That is a deliberate deferral,
recorded here rather than discovered by whoever implements it second.

**Level 1 is what most users need.** If you are running your own experiment rather than
reproducing this one, ignore Level 2 entirely and use any PRNG you like.

## 9. Conformance vector format

```json
{
  "spec_version": "1.0",
  "algorithm": { "digest": "...", "rng": "...", "shuffle": "..." },
  "vectors": [
    {
      "id": "basic-3",
      "why": "why this case exists",
      "seed": 991,
      "key": "item-1",
      "entities": ["a", "b", "c"],
      "values": [1, 2, 3],
      "expected_permuted_values": [2, 3, 1]
    }
  ],
  "must_raise": [
    { "id": "single-entity", "entities": ["only"], "values": [1], "error": "..." }
  ]
}
```

`expected_permuted_values` is positional against `entities`. Values are JSON, so a tuple
fact appears as an array; compare in the JSON domain to avoid a type mismatch that is not
a conformance failure.

## 10. Reference implementation

Python, in this directory. It is *a* conformant implementation, not the definition — the
definition is §3 plus the vectors.

The reference implementation is validated two ways: against the vectors, and against 540
prompts committed before it was extracted from the benchmark it came from. The second is
the stronger check, because those prompts were produced by different code.

## 11. Provenance and status

Matched controls are standard experimental design — placebo arms, matched-noise conditions
in psychophysics, matched-random ablations. **Applying one to prompt context appears to be
uncommon**; a 2026 review of the SVG-editing and structured-editing benchmark literature
found none. So this is an application, not an invention.

**The control has not yet been exercised in the role it was built for.** Across three
pre-registered studies and four models, no admissible arm has shown a positive effect for
it to decompose. It is known to be buildable, auditable, and behaviour-preserving under
extraction; it is not known to resolve what it was designed to resolve.

**The implementation currently has stronger evidence behind it than the hypothesis it was
built to test.** That is an unusual state for a research artifact and is stated here so
nobody has to infer it.
