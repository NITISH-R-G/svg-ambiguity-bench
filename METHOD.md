# Format-matched controls for context-augmentation experiments

**The problem this solves is domain-independent.** SVG is the worked example, not the
point.

---

## The confound

You have a task. You add context to the prompt — retrieved passages, tool schemas,
memory, metadata, structured facts. Accuracy improves. You conclude the *information*
helped.

That conclusion is usually unsupported, because adding context changes **two things at
once**:

```
                 ┌─ the INFORMATION it carries      ← what you claim helped
  added context ─┤
                 └─ the FORMAT it arrives in         ← what may actually have helped
```

Format alone can move accuracy substantially. An enumerated list gives every item a
referential handle it did not previously have. A table imposes structure on an
unstructured problem. A longer prompt shifts attention. None of that requires the content
to be *true* — or even meaningful.

If you only compare **augmented vs. unaugmented**, these two explanations are
observationally identical.

Anyone claiming *"supplying X improves performance"* on the strength of that comparison
alone is entitled only to the weaker claim: *"a prompt shaped like X improves
performance."*

---

## The control

Run a third arm that is **format-identical and information-destroyed**.

Take the augmented context. Keep the field names, the row count, the column widths, the
ordering, the token count. **Permute the values between entities** so the mapping from
entity to fact is destroyed while every other property is preserved.

```
  enhanced                      permuted
  ─────────────────────         ─────────────────────
  id      x      y   area       id      x      y   area
  e11a  184.8  207.7 17506      e11a  448.9  130.4  2015   ← values shuffled
  e33f   77.7  297.4   972      e33f  184.8  207.7 17506      between rows
  e0d6  186.5  411.8 10993      e0d6   77.7  297.4   972
  e301  426.6  292.5  6306      e301  186.5  411.8 10993

  same header, same rows, same columns, same token count
  identical marginal distribution of every number
  only entity→fact assignment destroyed
```

Then the comparison you actually want is available:

| comparison | isolates |
|---|---|
| `enhanced` − `baseline` | total effect of adding context |
| `permuted` − `baseline` | **format** component |
| `enhanced` − `permuted` | **information** component ← the claim |

Without the third arm, the first comparison is all you have, and it does not license the
claim people usually make from it.

---

## Why permutation rather than something simpler

| Alternative | Why it is weaker |
|---|---|
| Random values | Changes the marginal distribution. Token lengths shift, digit statistics shift, implausible values may be detectable |
| Empty enumerated list (headers only) | Different token count and shape — format is no longer held fixed |
| Removing one field | Changes format *and* information together, which is the original problem |
| Arguing the confound away in Discussion | Not a substitute for a measurement that costs one extra run |

Permutation preserves the **exact multiset** of values. Verify this: the sorted list of
all numbers must be identical between arms, and the token counts must match.

---

## Implementation

Domain-independent. Roughly forty lines.

```python
def permuted_context(entities, facts, seed, entity_key) -> str:
    """Format-identical to the enhanced context; entity→fact mapping destroyed."""
    rows = [(e, facts[e]) for e in entities]  # document order preserved
    values = [f for _, f in rows]

    # Seed from the ITEM, not the corpus seed, so the shuffle cannot correlate
    # with whatever structure the corpus seed generated.
    rng = Random(derive(seed, entity_key))

    shuffled = values[:]
    for _ in range(32):
        rng.shuffle(shuffled)
        if any(a != b for a, b in zip(values, shuffled)):
            break  # an identity permutation would silently recreate `enhanced`

    return render(zip([e for e, _ in rows], shuffled))  # SAME renderer as enhanced
```

Two details that are easy to get wrong and load-bearing:

1. **Use the same renderer for both arms.** If `enhanced` and `permuted` are formatted by
   different code, format is no longer held fixed and the control is void.
2. **Reject the identity permutation.** With small entity counts it occurs often enough to
   matter, and when it does, that case silently becomes a second `enhanced` case with no
   test failing.

---

## Checks that make the control credible

Each of these is mechanical, and each catches a way the control can quietly stop working.

| Check | What it prevents |
|---|---|
| Sorted multiset of values identical across arms | Permutation altered the information content |
| Token counts within a few characters | Prompt length became a confound |
| Headers, row count, column widths identical | Format not actually matched |
| Permutation never the identity | An arm silently duplicating `enhanced` |
| Excising the context block leaves prompts byte-identical | The template contributed something beyond the slot |
| Context byte-identical across items sharing an entity set | The context depends on the query — see below |

The last one deserves emphasis. **Make the context provider unable to see the query.**

```python
def provide(item_id, entities) -> str:      # NOTE: no query parameter
```

Blindness enforced by the signature holds for code nobody has written yet, which no
runtime assertion can achieve. If the same context block serves many different queries, it
demonstrably depends on none of them.

---

## Reporting

**When the effect is zero, report the minimum detectable effect, not the p-value.**

With an observed difference of exactly zero, no permutation of the data can be more
extreme, so p = 1.000 by construction. It is degenerate and carries no information. The
question a reader actually has is *"how large an effect could you have missed?"* — which
is what the MDE answers.

State the null in bounded form:

> No effect larger than **X** occurred — not: the effect is zero.

---

## Provenance, stated plainly

**Matched controls are not new.** Holding a manipulation's incidental properties fixed
while varying only the factor of interest is standard experimental design — placebo
controls in clinical trials, matched-noise conditions in psychophysics, matched-random
ablations in the ML component-ablation literature. The
[format-restriction literature](https://arxiv.org/html/2408.02442v1) already treats
prompt format as a first-order effect.

**Permuting content while holding format fixed is also not new, and an earlier version of
this document implied otherwise.** It is established practice in adjacent fields:

- **Context-aware machine translation** shuffles context between sentences as an ablation,
  to verify that a context-aware model relies on context at all
  ([Divide and Rule, 2021](https://arxiv.org/pdf/2103.17151))
- **RAG** distinguishes random from *distracting* irrelevant passages and finds they behave
  differently ([Cuconasu et al. 2024](https://arxiv.org/pdf/2505.06914); [The Distracting
  Effect, ACL 2025](https://aclanthology.org/2025.acl-long.892.pdf))
- **Representation learning** permutes association pairs while holding the training
  procedure fixed, to show a model learns nothing from arbitrary pairings

So the idea is standard, and it was standard before this project. That correction was
prompted by an external critic pointing at prior art a review scoped to SVG and
structured-editing benchmarks had missed. It is recorded as **FA-014**.

What remains, stated at the width the evidence actually supports:

> This is a **specification and reference implementation** of a control that is used
> informally elsewhere — with named invariants, conformance vectors, and stated
> boundary conditions — together with the observation that the SVG-editing and
> structured-editing benchmark literature does not use it.

Concretely, what is contributed is not the idea but:

1. **An executable definition.** Nine invariants, an algorithm, and 10 conformance vectors,
   so two implementations can be checked against each other rather than against a
   description. The shuffled-context ablations above are described in prose, per paper,
   and are not reusable across them.
2. **The three-way decomposition as the reported quantity.** Prior uses ask a binary
   question — *does the model use the context at all?* This reports
   `enhanced − permuted` as the information component alongside `permuted − baseline` as
   the format component, as the headline rather than as a sanity check.
3. **The failure modes, named.** Identity permutation, differing renderers, multiset
   drift, the applicability condition. These are the things that silently invalidate the
   control, and they are what a specification buys over a convention.

That is a much smaller claim than "a new method", and it is the one that survives contact
with the literature.

---

## Where this applies

Wherever added context is credited with an improvement **and the context is structured**.
That second clause is not a caveat; it is the boundary, and the examples are ordered by
how well they satisfy it:

| | Treatment vs control | Satisfies the condition? |
|---|---|---|
| **Metadata conditioning** | correct field values vs. values permuted between items | **Yes** — fixed schema, bounded width |
| **Tool arguments** | real schemas vs. arguments permuted between tools | **Yes** — typed fields |
| **Attribute augmentation** | a user's attributes vs. attributes permuted between users | **Yes**, when attributes are a record |
| **Structured prompting** | a populated table vs. the same table with cells shuffled | **Yes** |
| **Retrieved *records*** | row values permuted between queries | **Yes** — if retrieval returns rows |
| **Retrieved *passages*** (classic RAG) | passages permuted between queries | **Often no** — passages differ in length, so permuting changes token counts and breaks the format match |

The recipe is constant: *same shape, wrong contents*. What varies is whether a
representation *has* a shape that survives having its contents replaced.

**A note on RAG.** Earlier versions of this document led with RAG as the headline
application. That was a framing error: retrieved free-text passages are the case
**least** likely to satisfy the applicability condition, and leading with it advertised
the method at its weakest point. A [pilot survey](docs/10-applicability-survey-interim.md)
found free-text context to be the dominant reason papers fall outside the condition.
Length-stratified permutation or padding can sometimes restore the match, and each
introduces a confound of its own.

### The applicability condition

That list is examples. The condition is a property, and stating it as a property rather
than a list leaves room for representations nobody has thought of yet:

> **The method requires a representation that admits a value permutation while preserving
> its presentation-level invariants** — token count, field structure, ordering, and
> width. Where a representation does not admit such a permutation, a format-matched
> control cannot be constructed for it by this method.

Fixed-schema, bounded-width representations satisfy this: tables, metadata records, tool
argument lists, structured facts. **Whether other representations do is an open question**,
and there is one foreseeable failure.

Retrieved passages are not fixed-schema. They differ in length, so permuting them between
queries changes each query's token count and breaks the match on the property that matters
most. Length-stratified permutation or padding can restore it, and each introduces a
confound of its own. **RAG is simultaneously the most valuable application and the one
most likely to break the method** — see `TRUST.md`, *"What would change our minds"*.

This narrowing is deliberate. A method whose assumptions are explicit is more useful than
one whose scope is asserted broadly and discovered to be narrow later.

---

## The worked example

This repository applies the control to SVG element identification. The instrument was
frozen before any model output was observed; the corpus, scoring rules and analysis plan
are content-addressed and committed.

**The result was a null** — all three arms scored identically (0.0444), so the treatment
effect was zero and there was no quantity to decompose. The control was therefore never
exercised in its intended role, which is stated as a limitation rather than obscured.

That outcome does not invalidate the method. It illustrates the failure mode the method
exists to prevent: had only `baseline` and `enhanced` been run and had a difference
appeared, there would have been no way to tell which component produced it.

See [`docs/04-results.md`](docs/04-results.md) for the full write-up and
[`LIMITATIONS.md`](LIMITATIONS.md) for what it does not show.
