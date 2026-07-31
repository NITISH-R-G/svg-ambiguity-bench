# Why trust any of this

The other documents accumulate evidence. This one connects it.

Every reason a sceptic might have for not trusting this work, what has been done about
each, what remains, and which experiment would settle it. It is deliberately organised by
**objection** rather than by artefact, because that is how a reader actually approaches
the question.

It doubles as the roadmap: the next study is whichever line has the strongest remaining
objection, not whichever feature seems interesting.

---

## The one page

**Thesis.** Evaluation methodology should distinguish *information* effects from *format*
effects.

**Observation.** Context-augmentation experiments generally do not isolate these. A
two-arm comparison — augmented against unaugmented — cannot tell whether the retrieved
facts helped or whether a table helped. A survey of the SVG-editing and structured-editing
benchmark literature found none applying such a control.

**Method.** Construct a format-matched control by permuting the entity→fact assignment
while preserving every representational property: rows, fields, widths, ordering, token
count, and the exact multiset of values. Then

```
enhanced − baseline   total effect
permuted − baseline   format component
enhanced − permuted   information component   ← the claim people actually make
```

**Validation.** The control is deterministic, invariant-checked, behaviour-preserving
under extraction from its original domain, independently implementable from a
specification, and falsifiable.

**Open question.** When — if ever — do models begin exploiting the preserved information
channel? Four models across two families and three scales showed no admissible evidence of
doing so.

**Broader hypothesis, held tentatively.** Evaluation instruments encode empirical
assumptions about model behaviour, and those assumptions can drift as models evolve, with
no test failing and no number looking wrong.

---

## Three concepts

If nothing else survives, these should:

1. **Format-matched control** — same shape, wrong contents. The permuted arm.
2. **Instrument drift** — a frozen scoring rule encodes assumptions about model behaviour
   that later models violate. The instrument holds still; the behaviour moves.
3. **A scoring rule is an empirical hypothesis**, not neutral plumbing. Freezing it makes
   it auditable, not timeless.

Everything else in this repository — provenance tiers, claim→evidence mapping, operational
invariance, designed vs emergent methodology, behaviour-preserving extraction — is
*supporting machinery* for those three. Useful internally; not concepts anyone else needs
to carry. Naming every internal distinction is how a vocabulary becomes unmemorable.

---

## The trust table

Status key: **Settled** — evidence exists and no known objection survives. **Partial** —
evidence exists, a named gap remains. **Open** — no evidence yet.

| # | Objection a sceptic would raise | What answers it | Status | What remains | Experiment that would settle it |
|---|---|---|---|---|---|
| 1 | *"The control doesn't really hold format fixed."* | Same renderer both arms; identical multiset, row count, order, token count; 6 mechanical checks; 10 conformance vectors | **Settled** | none known | — |
| 2 | *"The permutation might silently be the identity."* | Displacement required by value; refuses rather than degrades; asserted at n=2…16 over 200 trials each | **Settled** | none known | — |
| 3 | *"The numbers come from a scorer that was never itself checked."* | 9/9 mutation kills; 26 fixtures; verification-policy requiring fixtures to fail differently than the implementation | **Partial** | mutation set is author-chosen | An independent scorer over the 2,880 committed responses |
| 4 | *"You tuned the analysis after seeing results."* | Instrument frozen and git-tagged before any output; frozen tree provably contains **no** model output; three studies each pre-registered before running | **Partial** | *contents* auditable, *timing* testimonial — a local run leaves no trace | Nothing can fix retroactively. Stated in README Provenance |
| 5 | *"You'd have relaxed the rules if they'd blocked a result you wanted."* | V3's falsifier excluded the **only** model showing a positive information effect (+0.0944, p=0.0061). It stayed excluded | **Settled** | — | Already the strongest evidence in the project |
| 6 | *"Your predictions were made after the fact."* | V2 predicted band C, observed band A — wrong, on record. V3 predicted SILENT, observed SILENT on admissible data | **Settled** | — | — |
| 7 | *"It's SVG-specific engineering dressed as a method."* | Extracted to `fmtcontrol`, which cannot import the benchmark (asserted by test); 540/540 V1 prompts reproduce byte-for-byte through the extracted path | **Partial** | see the three independence claims below | Apply the control in a second domain — RAG is the obvious one |
| 8 | *"It's only reproducible because it's your Python."* | `SPEC.md`: 9 invariants, algorithm, boundary cases, 2 conformance levels, 10 vectors + 2 must-raise | **Partial** | no independent implementation exists | A Rust/Go/TS implementation passing Level 1 |
| 9 | *"The model just can't do the edit."* | V2: naming the target moves accuracy 0.0444 → 0.9278; replicates on all 4 models (0.61–0.93) | **Settled** | — | — |
| 10 | *"It's one model."* | V3: four models, two families, three scales | **Partial** | all small, all local, none frontier | Frontier models — **but see the dependency below** |
| 11 | *"The control has never actually done anything."* | Honest answer: correct. No admissible arm has produced an effect to decompose | **Open** | the central claim is unexercised | A model that uses the geometry channel |
| 12 | *"Your scorer mislabels behaviour it wasn't built for."* | Correct, and self-reported: 318/330 `MALFORMED` are prose refusals; 237/237 for the 7B. FA-013 | **Open** | abstention semantics known-wrong for ≥1 model | **V4**: revised `abstention_rule_version`, pre-registered, developed on held-out responses |
| 13 | *"Synthetic corpus with tokens that don't occur in reality."* | Stated, not defended. `LIMITATIONS.md`; opaque `{{GEOM_}}` placeholders are acknowledged as unlike real SVG | **Open** | external validity near zero by construction | A corpus of real SVGs with natural ambiguity |
| 14 | *"One author, so every judgement call is one person's."* | 13 documented self-corrections; every threshold justified in-line; rejection rates published | **Open** | no external eyes at all | Independent replication or an adversarial review |

## Three independence claims, often collapsed into one

Objection 7 is really three claims with three different evidence levels. Conflating them
is the easiest way to overclaim here, so they are kept apart:

| | Claim | Status |
|---|---|---|
| **Implementation independence** | the algorithm is not entangled with SVG code | **Supported.** Extraction; a test forbids importing the benchmark; 540/540 prompts byte-identical |
| **Method independence** | a valid control can be *constructed* for other structured contexts | **Conceptual only.** Never demonstrated outside this corpus. See the falsifier below - it may not hold for variable-length content |
| **Phenomenon independence** | the underlying scientific question behaves similarly across domains | **Untested.** No evidence either way |

Extraction bought the first and nothing else. The repository previously implied more than
that, and this row exists to stop it doing so again.

---

## What would change our minds

Distinct from future work. For each central claim: the observation that would make it
abandoned or substantially revised. Stated so the claims are visibly falsifiable, and
because at least one of these is a live risk rather than a formality.

### 1. The permuted arm is a clean control

> **Would change our minds:** `permuted` scoring *systematically below* `baseline` by more
> than the MDE, across admissible models.

If supplying scrambled-but-plausible facts is worse than supplying nothing, the arm is not
information-**destroyed** — it is information-**corrupted**. A model that trusts an
authoritative-looking table is actively misled by it, which is a different manipulation
from the one the design intends, and `enhanced − permuted` would then *overstate* the
information effect rather than isolate it.

**Where this stands today**, `permuted − baseline`:

| model | difference | MDE | admissible |
|---|---|---|---|
| qwen 1.5b | **−0.0222** | 0.0170 | no — malformed rate |
| qwen 3b | +0.0000 | 0.0289 | yes |
| llama 3.2 3b | −0.0167 | 0.0309 | yes |
| qwen 7b | **+0.0722** | 0.0456 | no — malformed rate |

On the two admissible models the difference is within the MDE, so there is no evidence of
corruption. But the direction is *inconsistent* across models, and the one model exceeding
its MDE negatively (1.5b) is inadmissible for an unrelated reason. **This is the most
serious unexamined threat to the control's validity**, and it should be a pre-registered
secondary outcome in V4 rather than something noticed afterwards.

The 7B's `+0.0722` is the same coin's other face: a large *format* effect, which is
precisely what the control exists to expose. Had it been admissible, the decomposition
would have read roughly 43% format / 57% information.

### 2. The method is broadly applicable

> **Would change our minds:** repeated failure to construct a valid control in
> structurally different domains.

There is a specific, foreseeable version of this. The control preserves token count by
permuting values within a fixed schema. **Retrieved passages are not fixed-schema** — they
differ in length, so permuting passages between queries changes each query's token count,
and the format match fails on the property that matters most.

So the method may be limited to **fixed-schema, bounded-width contexts** — tables,
metadata, tool arguments, structured records — and may not extend to free-text retrieval
at all without a different matching strategy (length-stratified permutation, or padding,
each of which introduces its own confound). RAG is the headline application in
`METHOD.md`; it is also the case most likely to break it.

### 3. Instrument drift is a real phenomenon rather than one bad regex

> **Would change our minds:** diverse models evaluated under revised abstention semantics
> showing no measurable difference attributable to output style; or a demonstration that a
> single well-written rule handles every register.

FA-013 is one observation on one axis. If a modest widening of the abstention patterns
absorbs every model's refusal style, then this was a bug in a regex dressed up as a
methodological finding, and it should be demoted. **V4 is the test.**

### 4. Execution and reference resolution are separable

> **Would change our minds:** a model with high `named-id` accuracy whose *descriptive*
> accuracy also rises substantially with better-formatted geometry — indicating the two
> abilities are not cleanly separable but sit on a shared continuum of context handling.

Currently the dissociation is stark (0.61–0.93 vs 0.03–0.18) on every model tested, which
is why this is the best-supported claim in the project.

---

## What this table says about priority

Objections **11, 12, 13, 14** are Open. Of those, one has a dependency the others don't,
and noticing it is the main reason this document was worth writing:

> **V4 must precede frontier models.**

The obvious next move is objection 10 — run a frontier model, which might also resolve 11.
But FA-013 shows the 7B declined *in prose* and had 237 reasoned refusals scored
`MALFORMED`. A frontier model will almost certainly abstain the same way, or more
articulately. Running one under the current abstention rule would reproduce the identical
instrument-drift failure, at higher cost, and produce numbers that are inadmissible for
exactly the same reason.

So the order is forced:

```
V4  (fix abstention semantics, pre-registered)
 ↓
frontier models  (objection 10, and possibly 11)
 ↓
second domain    (objection 7)
```

Independent implementation (8) and independent replication (14) are parallel and depend on
nobody but a volunteer. They are the two things that cannot be bought with more effort by
the author, which is precisely why they are worth the most.

---

## What is genuinely settled

Worth stating positively, because the table above is deliberately adversarial:

- The control is correctly constructed and mechanically verified.
- The instrument was frozen before observation, and that is checkable by a stranger in one
  command.
- The pre-registration held under maximum pressure — it excluded the result the author
  most wanted.
- Predictions were recorded in advance and one was wrong.
- The dissociation between execution and reference resolution replicates on every model
  tested.
- The method survives extraction from its domain with byte-identical behaviour.

## What is not

- The control has never decomposed a real effect. **This is the central open item.**
- The abstention rule is known to be wrong for at least one model.
- Whether the permuted arm is *neutral* or *misleading* has never been directly tested.
- The method has never been constructed for a non-tabular context, and may not be
  constructible for one.
- Nothing has been externally replicated, implemented, or reviewed.
- Nothing generalises beyond a synthetic corpus and four small local models.

---

## The principle

Every improvement in this project came from the same question:

> **If someone completely disagreed with me, what experiment would convince them?**

- *"Maybe the model can't edit."* → V2.
- *"Maybe it's one model."* → V3.
- *"Maybe it's SVG-specific engineering."* → the extraction.
- *"Maybe it's only reproducible because it's Python."* → the specification.

Each removed one **legitimate** reason for scepticism. None was a feature idea, and none
would have been chosen by asking what would be interesting to build.

The rule this yields is simple enough to keep: **let the next study be dictated by the
strongest surviving objection in the table above.** When that objection is Open and has no
dependency, run it. When it has one, run the dependency first.

Today the strongest surviving objection is #12, and the next study is V4.

---

## Current figures

| | |
|---|---|
| Studies | 3, each pre-registered before running |
| Models | 4 — two families, three scales |
| Committed model responses | 2,880 |
| Tests | 330 |
| Documented failed assumptions | 13 |
| Conformance vectors | 10, plus 2 must-raise |
| Reproduction tiers | 4; Tier-1 in ~2s with no model and no renderer |
