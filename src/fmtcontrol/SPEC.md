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

### Setting

Everything below is a statement about **representations and functions**. No model appears
in any definition or proof, which is deliberate: a result that mentions no model survives
model turnover.

| | |
|---|---|
| `E` | finite entity set, `\|E\| = n >= 2` |
| `V` | value set |
| `f : E -> V` | the assignment |
| `S_E` | permutations of `E` |
| `render : (E -> V) -> String` | the caller's renderer |
| `P : String -> Π` | the **presentation functional** — everything about the rendered string other than which entity holds which value: token count, line count, field names, column widths, row order |
| `τ : (E -> V) -> A` | the **target**: what the experiment wants computed from the context |
| `S : String -> A` | a **strategy**: any function from rendered context to answer. Unrestricted — no computability, complexity or continuity assumption |

The last row matters. `S` ranges over *all* functions, so the results below hold for any
solver whatsoever: a model, a program, an oracle, a person.

> **A representation admits a format-matched control if:**
>
> **C1 — Permutability.** Values may be reassigned between entities independently. No
> value is constrained to a particular entity by the representation itself.
>
> **C2 — Presentation invariance.** `P(render(f)) = P(render(f ∘ π))` for every `π ∈ S_E`
> and every admissible `f`.
>
> **C3 — Assignment-carried semantics.** The target `τ` does **not** factor through `P`:
> there is no `h : Π -> A` with `τ = h ∘ P ∘ render`.

**C2 is where free text fails.** Passages of differing length make token count a function
of the assignment, so `P` is not invariant. Padding or length-stratified permutation can
restore C2, and each introduces a confound of its own — a design decision, not a repair.

**C3 is where a sorted table fails**, and §6b shows C3 is not an independent requirement
but a consequence of wanting the contrast to have any power at all.

Note the precise form of C3. It is **not** "presentation reveals nothing" — presentation
always reveals something. It is the exact statement that the *target* is not a function of
the presentation alone. That is what the quantifier `∃h` pins down, and the earlier
informal phrasing ("the information is carried only by the assignment") did not.

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

### 6b. Why C2 and C3 are not stipulations

Both are forced. The arguments are elementary and given in full so they can be checked
rather than believed. They convert *"this representation does not work with our tool"*
into *"no value-permutation control exists for this representation"* — a statement about
the problem, not the implementation.

Write `T = render(f)` for the treatment arm and `C = render(f ∘ π)` for the control arm,
with `f ∘ π ≠ f`.

---

**Proposition 1 — C2 is necessary for identification.**

*If `P(T) ≠ P(C)`, the contrast between the arms does not identify an effect of the
assignment.*

*Proof.* The arms differ in two respects: the assignment, and at least one component of
`P`. Both are present in the rendered string, so a strategy may depend on either. For any
strategy `S`, the difference `S(T) − S(C)` is a sum of a term attributable to the
assignment and a term attributable to the `P`-difference. The two arms provide one
equation in two unknowns, and no further observation on these arms separates them, because
every case in which the assignment differs is also a case in which `P` differs. ∎

*Corollary.* A representation violating C2 does not make the control weaker. It reproduces
the augmented-vs-unaugmented confound *inside* the control, so the control is **inert**.

---

**Proposition 2 — a target that factors through `P` makes the contrast powerless.**

*Assume C2. If `S = h ∘ P` for some `h : Π -> A` — that is, the strategy depends on the
rendered context only through its presentation — then `S(T) = S(C)`. Consequently the
contrast has zero power against every such strategy, whatever `h` is.*

*Proof.* `S(T) = h(P(T)) = h(P(C)) = S(C)`, the middle equality by C2. ∎

*Corollary (C3 is derived, not assumed).* Suppose the target `τ` factors through `P`, so
some `h` computes it exactly. Then by Proposition 2 that strategy is **perfectly correct
and perfectly invariant**: it scores identically on both arms. The contrast returns zero
not because the strategy ignores the information, but because the information it uses was
never manipulated. C3 is therefore not an extra requirement imposed by this method — it is
the condition under which the contrast has any power at all.

*Corollary (sorted tables).* If rows are ordered by the quantity of interest, rank is
legible from row position; row order is a component of `P`; so `τ` factors through `P` and
the contrast is powerless. This is why the reference implementation preserves document
order (**I2**) rather than sorting — **sorting would satisfy C2 and destroy the
experiment**, which is exactly the combination that is easiest to ship by accident.

---

**Proposition 3 — impossibility.**

*If a representation violates C2 or C3, no value-permutation control isolates the effect
of the assignment while preserving observable structure.*

*Proof.* If C2 fails, Proposition 1: the contrast is confounded. If C2 holds and C3 fails,
Proposition 2: the contrast is powerless against a strategy that solves the task. Those
cases are exhaustive. ∎

---

### What these do and do not say

**They are about representations, not about models.** `S` ranges over all functions with
no computability or complexity restriction, so nothing here depends on which model is used
or on how models behave. That is the point of stating it this way: a result naming no
model does not expire when models change.

**"Recoverable" is not used.** An earlier draft said the information must not be
"recoverable" from the presentation, which meant nothing precise — recoverable by whom,
under what resource bound? The statement above replaces it with **factoring**: `∃h` such
that `τ = h ∘ P ∘ render`. That is a definite mathematical condition, and it is
deliberately generous — it quantifies over *all* `h`, so C3 fails whenever *any* function
could extract the target from presentation, however impractical.

**They are necessary, not sufficient.** A representation satisfying C1–C3 admits a
*constructible* control. Whether that control means what it is taken to mean depends on
C4, which is empirical and untested.

**The tension is structural.** C2 requires presentation to be **insensitive** to the
assignment; C3 requires the target to be **absent** from presentation. Presentation must
be rich enough to be identical across arms and poor enough to determine nothing. The
admissible region is the intersection, and it is small — which is the likeliest
explanation for why the applicability estimate has fallen at every revision. That is a
property of the constraints, not a weakness of the method.

### Status of these arguments

Deliberately labelled **propositions**, not theorems, and the reason is the project's own
standard rather than modesty. They are elementary, they have been written out in full so
that the assumptions are visible, and they have had **no independent review**. Calling
something a theorem invites scrutiny of the proof, which is healthy but raises the
evidential bar — and the bar should rise with the strength of the claim.

The same rule applied to the experiments applies here: a claim is worth exactly the
evidence behind it, and "I checked it myself" is the weakest admissible evidence in this
repository. **Review of these proofs is solicited** as a first-class contribution, on the
same footing as an independent implementation — see
[`CONTRIBUTING.md`](../../CONTRIBUTING.md). A refutation, or a demonstration that an
assumption is doing hidden work, is more useful than a confirmation.

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
