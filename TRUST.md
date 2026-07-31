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

**Observation.** A two-arm comparison — augmented against unaugmented — cannot tell
whether the retrieved facts helped or whether a table helped.

**Prior art, stated up front.** Permuting content while holding format fixed is **not
new**. Context-aware MT shuffles context as an ablation; RAG separates random from
distracting passages; representation learning permutes association pairs. An earlier
version of this document claimed otherwise and was corrected after an external critic
pointed at the prior art — **FA-014**. What is contributed is a *specification* of that
convention (invariants, conformance vectors, named failure modes) and the three-way
decomposition reported as the result rather than as a sanity check, plus the narrower
observation that SVG and structured-editing benchmarks do not use it.

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

## Card

The same facts in the shape labs already read model and dataset cards in. Kept on this
page rather than in a file of its own, so it cannot drift away from the evidence beside
it.

| | |
|---|---|
| **Question** | When added context improves a model, was it the information or the format? |
| **Measures** | The information component of a context-augmentation effect, isolated from the format component, via a third arm that is format-identical and information-destroyed |
| **Does not measure** | Whether context augmentation is worth doing; retrieval quality; anything about a model's internals; anything outside the applicability condition |
| **Applicability condition** | A representation that admits a value permutation while preserving its presentation-level invariants — token count, field structure, ordering, width. Fixed-schema bounded-width representations satisfy it. Raw variable-length text may not |
| **Core assumptions** | (1) permuting removes the information; (2) permuting introduces no *new* manipulation. **Assumption 2 has never been directly tested** — see falsifier 1 |
| **Known failure modes** | Identity permutation silently recreating the treatment arm (guarded); different renderers between arms (guarded by API shape); a permuted arm that misleads rather than merely uninforms (**untested**); representations that admit no format-preserving permutation |
| **Evidence** | 3 pre-registered studies, 4 models, 2,880 committed responses, 330 tests, 10 conformance vectors, 13 documented failed assumptions |
| **Central claim status** | **Unexercised.** No admissible arm has yet produced an effect to decompose |
| **Independent replications** | **0** — [how to report one](CONTRIBUTING.md#the-three-contributions-worth-the-most) |
| **Independent implementations** | **0** — [how to report one](CONTRIBUTING.md#the-three-contributions-worth-the-most) |
| **Independent proof reviews** | **0** — SPEC §6b is unreviewed; labelled *propositions*, not theorems |
| **Protocol version** | instrument `instrument-freeze-v1`; `abstention_rule_version` 1.0 (**known wrong for ≥1 model** — FA-013); `fmtcontrol` spec 1.0 |
| **Cost to adopt** | ~200 lines, standard library only, vendorable by copying two files |
| **Licence / DOI** | MIT · [10.5281/zenodo.21682240](https://doi.org/10.5281/zenodo.21682240) |

## Two independent hypotheses

Every study through V4 tests one thing. The survey tests a different one, and conflating
them is how a project spends years perfecting a method nobody needs.

| | **Hypothesis A — validity** | **Hypothesis B — applicability** |
|---|---|---|
| **Claim** | The control does what it says: isolates information from format | Enough published work satisfies its preconditions for it to matter |
| **Tested by** | V1, V2, V3, V4 | the [applicability survey](docs/09-applicability-survey-preregistration.md) |
| **Status** | instrument validated; central claim **unexercised** | **3-paper pilot only.** 2 of 3 fell outside the applicability condition |
| **Failure looks like** | the control fires but does not decompose cleanly | a valid method with a domain too small to be worth specifying |

**These are independent.** A method can be perfectly valid and apply almost nowhere. Every
objection in the table below is about A. Until this session, nothing in the repository
tested B — which meant the project could not fail in the way that matters most.

If Survey 1 returns ~10% applicability, Hypothesis B is substantially rejected, and the
right response is to present the method as **specialised** from the first line rather than
to argue the number up. That is stated here, before the number exists.

## The research programme, as questions

The objection table below says why to believe the answers. This says why the questions
were asked, which is the part that becomes invisible six months later. Machine-readable in
[`protocol.json`](protocol.json); `python -m svgbench.cli status` prints it and verifies
the identifiers against the artefacts.

| | Question | Study | Answer |
|---|---|---|---|
| **Q1** | Does supplying the missing geometry improve reference resolution — and if so, is the gain *information* or *format*? | **V1** | No detectable effect at all. Constrained null, all arms 0.0444, MDE 0.0289. The decomposition had nothing to operate on |
| **Q2** | Is that a failure of *reference resolution*, or can the model simply not perform the edit? | **V2** | Reference resolution. Naming the target moves accuracy to 0.9278. Execution is not the limiting factor |
| **Q3** | Does the pattern hold across model scale and family — and does the control ever fire? | **V3** | Replicates on four models. Control **SILENT** on admissible evidence. The one model that would have fired it was excluded by a pre-registered falsifier |
| **Q4** | Do the scoring rules recognise how *other* models decline? | **V3, unplanned** | No — FA-013, instrument drift. 318/330 `MALFORMED` responses are reasoned refusals |
| **Q5** | Is the permuted arm neutral, or actively misleading? | **not yet asked** | Untested. Pre-registered as a secondary outcome for V4 |

Each question exists because the previous answer raised it. None was chosen because it
would be interesting to build.

## Reference implementation

[`src/fmtcontrol/`](src/fmtcontrol/) is the **reference implementation** of the
[specification](src/fmtcontrol/SPEC.md) — the term used in its ordinary sense: *a*
conformant implementation that resolves ambiguity by example, not the definition. The
definition is the nine invariants plus the
[conformance vectors](src/fmtcontrol/conformance_vectors.json).

An implementation that disagrees with the reference but satisfies the specification has
found a specification defect, and that is the outcome
[worth reporting most](CONTRIBUTING.md#the-two-contributions-worth-the-most).

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

> **Would change our minds:** repeated failure to construct a valid control for
> representations that satisfy the applicability condition.

The condition is stated in `METHOD.md` as a property rather than a list of domains:

> The method requires a representation that admits a value permutation while preserving
> its presentation-level invariants — token count, field structure, ordering, width.

Fixed-schema bounded-width representations satisfy it. **Retrieved passages may not**:
they differ in length, so permuting them between queries changes each query's token count
and breaks the match on the property that matters most. RAG is simultaneously the most
valuable application and the one most likely to break the method.

Note this claim has been **narrowed**, not broadened, as evidence accumulated. That is the
intended direction. A method with explicit assumptions is more useful than one whose scope
is asserted broadly and found to be narrow by someone else.

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

Independent implementation (8), independent replication (14) and review of the §6b proofs
are parallel and depend on nobody but a volunteer. They are the two things that cannot be bought with more effort by
the author, which is precisely why they are worth the most.

### External evidence, as it arrives

Empty by design, and published empty on purpose: the absence is part of what a reader
should know, and treating it as a section that exists from the start makes clear that
independent evidence was designed for rather than hoped for. Issue templates and the
contribution path are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

| Source | Kind | Language / setup | Spec or protocol | Result |
|---|---|---|---|---|
| this repository | reference implementation | Python | spec 1.0 | Level 2, 10/10 vectors |
| — | proof review of SPEC §6b | — | spec 1.0 | **none yet** |
| — | independent implementation | — | — | **none yet** |
| — | independent replication | — | — | **none yet** |
| — | different-domain application | — | — | **none yet** |

A row is added for every report received, including ones that **fail** or **disagree**. A
failing implementation report means the specification is ambiguous; a disagreeing
replication is recorded as a disagreement rather than resolved in the project's favour.

### Three kinds of work, with three different bottlenecks

Easy to conflate, because all three feel like progress.

| | **Evidential** | **Adoptability** | **Ecosystem** |
|---|---|---|---|
| **Changes** | what the evidence warrants | the cost of adopting it | who knows or trusts it |
| **Controlled by** | the author, given effort | **the author, entirely** | other people, given interest |
| **Examples** | V4; frontier models; a second domain; whether the permuted arm is neutral | `SPEC.md`; conformance vectors; this document; stdlib-only packaging; the runnable example | a paper; an independent implementation; an external replication; a lab reporting a format-matched result |
| **Build before demand?** | yes | **yes** | no — it is pulled, not pushed |

The distinction that matters is **adoptability versus scale**. Adoptability removes
friction that exists *today* for a hypothetical adopter; scale optimises for demand that
does not exist yet.

Concretely: a specification removes the "I can't reimplement this" barrier whether or not
anyone is reimplementing. A GPT-5 adapter removes no barrier at all until somebody wants
to run GPT-5, and by then it is an afternoon's work informed by an actual requirement.

The test is: **if a researcher wanted to adopt this tomorrow, what would stop them?**

| Barrier | Answer | Status |
|---|---|---|
| can't understand the method | `METHOD.md`, `README.md` | done |
| can't reimplement it | `SPEC.md` — 9 invariants, algorithm, boundary cases | done |
| can't verify their implementation | 10 conformance vectors + 2 must-raise | done |
| don't know the limitations | this document; `LIMITATIONS.md` | done |
| **can't install it without a Rust rasterizer** | stdlib-only; vendorable by copying two files; asserted by test | done |
| **can't see it work in 30 seconds** | `examples/rag_style_control.py`, runnable on bare Python | done |
| want it in their eval framework | — | **not yet, and correctly so** |

The current **evidential** bottleneck is that the control has never fired and the
abstention rule is known wrong for one model. **Ecosystem** work before that resolves
would make more people encounter a method whose central claim is unexercised.

So: model adapters for hosted providers are worth building **after V4**, because frontier
models are blocked behind it. Building them now is building ahead of the roadmap this
document derives.

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

## The ratchet rule

There is a failure mode on the other side of all this, and it is easier to fall into than
the one this document mostly guards against.

Every study so far has produced a new subtlety. V2 raised the execution confound. V3
raised instrument drift. Writing the falsifiers raised the possibility that the permuted
arm is misleading rather than neutral. Each was legitimate. But a process that generates a
new objection every time it runs a study, and treats each as a reason to withhold a
conclusion, will never conclude anything — and it would *feel* rigorous the whole way
down. Perpetual scepticism is not a higher standard; it is an unfalsifiable position
wearing the costume of one.

So, fixed now, before the study it governs:

> **A study's acceptance criteria are fixed at its registration. A threat discovered
> afterwards does not retroactively raise that study's bar. It becomes the next study's
> business.**

Concretely: if V4 meets the criteria in its own pre-registration, its conclusion stands —
even if, by the time it finishes, something new has occurred to me. The new concern gets
registered as V5's, in writing, in advance. It does not get applied backwards.

This is the same discipline that excluded the 7B, pointed the other way. That rule stopped
a result being admitted because it was wanted. This one stops a result being withheld
because a further doubt is always available. Both are the same commitment: **the criteria
are set before the outcome is known, and then they are honoured.**

The test is symmetrical to the one in `RESULTS.md`:

> Would this standard have been applied identically had the result come out the other way
> around?

**Applied to what is already on record:** the permuted-corruption threat was found after
V3 concluded. Under this rule it does **not** invalidate V3. V3's conclusion — SILENT on
admissible evidence — stands as registered. The threat is V4's business, and is listed as
a pre-registered secondary outcome there rather than as a retrospective caveat here.

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
