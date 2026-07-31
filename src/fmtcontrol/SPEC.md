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

## 6a. Which representations admit a control

§6 says the caller must render. This says which representations *can* be rendered such
that a control exists at all. It is a characterisation rather than a list of domains,
because a list is only ever as good as the domains someone thought of.

Let `E` be a finite entity set, `V` a value set, `f : E -> V` the assignment, and
`render : (E -> V) -> String` the caller's renderer. Let `S_E` be the permutations of `E`.

Define a **presentation functional** `P` — everything about the rendered string that is
not which entity has which value. Concretely: token count, line count, field names, column
widths, row order.

> **A representation admits a format-matched control iff:**
>
> **C1 — Permutability.** Values may be reassigned between entities independently. No
> value is constrained to a particular entity by the representation itself.
>
> **C2 — Presentation invariance.** `P(render(f)) = P(render(f ∘ π))` for every `π ∈ S_E`
> and every admissible `f`. Permuting changes *which* value appears where, and nothing a
> reader could measure about the container.
>
> **C3 — Assignment-carried semantics.** The information under test is carried **only** by
> the assignment `f`, not by the entity labels or by the values in isolation. If entity
> ids already encoded position, permuting values would leave the channel intact and the
> control would measure nothing.

**C2 is the discriminating condition**, and it is where free text fails. Passages of
differing length make token count a function of the assignment, so `P` is not invariant,
and the permuted arm differs from the treatment in a property a model can detect. Padding
or length-stratified permutation can restore C2, and each introduces a confound of its
own — which is a design decision, not a repair.

**C3 is the one most often violated silently.** A table whose row order is sorted by the
quantity of interest fails it: order carries the information, so permuting the values
leaves the ranking legible. This is why the reference implementation preserves iteration
order (I2) rather than sorting.

### The fourth condition, and why it is not listed

A natural fourth condition would be:

> **C4 — Non-substitution.** Permutation destroys the target information channel without
> introducing a *different* manipulation.

C4 is deliberately **excluded from the definition**, because unlike C1-C3 it is not a
property of the representation that can be checked by inspection. It is an empirical claim
about how a *model* responds: a model that treats an authoritative-looking table as
trustworthy may be actively misled by permuted values rather than merely uninformed, which
is a different manipulation from the intended one.

**This is currently untested.** See `TRUST.md`, "What would change our minds", falsifier 1.
Making C4 definitional would let the definition quietly assume the thing the experiment is
supposed to establish. It is recorded here as an open condition on *use* rather than a
closed condition on *representations*.

So: C1-C3 characterise where a control can be **constructed**. C4 governs whether the
constructed control means what it is taken to mean, and is a matter for measurement.

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

## 9. Versioning — a methodological contract, not an API one

Ordinary semantic versioning promises that code keeps compiling. That is the wrong
promise here. Someone citing a version needs to know their **numbers** still reproduce,
which is a stronger and different guarantee.

> **Within a major version, the published conformance vectors never change.**

| change | version | means |
|---|---|---|
| bug fix, docs, performance, new checks that reject nothing previously accepted | **patch** — 1.0.x | vectors unchanged; results unaffected |
| new optional capability; additional vectors appended | **minor** — 1.x.0 | every existing vector still reproduces exactly |
| **any change to the permutation, the digest, the RNG, or an existing vector** | **major** — 2.0.0 | results from 1.x do **not** reproduce under 2.x, and must not be compared as if they did |

A major bump is therefore a claim that the *method* changed, not that the code was
restructured. It requires a new spec version, regenerated vectors, and an account of what
the change does to previously published results.

**What this means if you cite it.** Cite the major version — `fmtcontrol 1.x` — and your
permutations are stable. If you need bit-exactness for a published table, pin the exact
version and record the `spec_version` from the vectors file alongside your results.

**The migration this anticipates.** §8 records that Level 2 conformance pins MT19937 for
inherited reasons, and that a future spec should use a portable PRNG. That is exactly a
major bump: it changes every permutation. It is deliberately deferred rather than done
quietly, because doing it quietly would silently invalidate every number published under
1.x while leaving all the code working.

## 10. Conformance vector format

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

## 11. Reference implementation

Python, in this directory. It is *a* conformant implementation, not the definition — the
definition is §3 plus the vectors.

The reference implementation is validated two ways: against the vectors, and against 540
prompts committed before it was extracted from the benchmark it came from. The second is
the stronger check, because those prompts were produced by different code.

## 12. Provenance and status

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
