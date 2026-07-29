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

What appears to be missing, at least as far as [a 2026 literature
review](docs/03-review.md) of the SVG-editing and structured-editing benchmark literature
found, is anyone applying that control to **prompt context**. Benchmarks in that family
report a single augmented-versus-unaugmented number.

So the contribution here is **an application, not an invention**, and the honest framing
is:

> A standard experimental control, applied to a confound that context-augmentation
> evaluations routinely leave uncontrolled.

That is a smaller claim than a new method, and it is the one the evidence supports.

---

## Where this applies

Anywhere added context is credited with an improvement:

- **RAG** — retrieved passages vs. passages permuted between queries
- **Tool use** — real schemas vs. schemas with arguments permuted between tools
- **Memory / personalisation** — a user's facts vs. facts permuted between users
- **Structured prompting** — a populated table vs. the same table with cells shuffled
- **Metadata augmentation** — correct labels vs. labels permuted between items

The recipe is constant: *same shape, wrong contents*.

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
