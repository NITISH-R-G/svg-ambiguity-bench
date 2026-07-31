# Study V3 results - model generality, and a falsifier that cost something

Pre-registered at [`study-v3-preregistration`](07-study-v3-preregistration.md) before any
V3 model was run. The decision rules below were fixed in advance and are applied as
written, including where doing so is expensive.

---

## Headline

**Pre-registered outcome: SILENT.** On the models that pass the pre-registered data-quality
falsifier, the format-matched control did not fire. `enhanced - permuted` was within the
minimum detectable effect for both.

**And the one model that would have fired it is excluded by that falsifier.** That is not
a footnote. It is the main event, and this document is organised around it.

| model | family | params | `enhanced - permuted` | MDE | admissible? |
|---|---|---|---|---|---|
| `qwen2.5-coder:1.5b` | Qwen | 1.5B | +0.0111 | 0.0211 | **excluded** - malformed 0.16-0.19 |
| `qwen2.5-coder:3b` | Qwen | 3B | +0.0000 | 0.0289 | admissible - **within MDE** |
| `llama3.2:3b` | Llama | 3B | -0.0111 | 0.0297 | admissible - **within MDE** |
| `qwen2.5-coder:7b` | Qwen | 7B | **+0.0944** | 0.0582 | **excluded** - malformed 0.14-0.65 |

I predicted SILENT in the registration. On the admissible evidence that prediction is
correct. I take no satisfaction in it, for reasons the rest of this document explains.

---

## Full frozen results

Every figure from the frozen scorer, `abstention_rule_version` 1.0, unmodified.

| model | condition | accuracy [95% cluster CI] | malformed |
|---|---|---|---|
| **1.5B** | baseline | 0.0389 [0.0111, 0.0778] | 0.156 |
| | permuted | 0.0167 [0.0000, 0.0389] | 0.189 |
| | enhanced | 0.0278 [0.0056, 0.0500] | 0.172 |
| | named-id | 0.6500 [0.5333, 0.7556] | 0.000 |
| **3B** *(V1/V2)* | baseline | 0.0444 [0.0167, 0.0778] | 0.000 |
| | permuted | 0.0444 [0.0167, 0.0778] | 0.000 |
| | enhanced | 0.0444 [0.0167, 0.0778] | 0.000 |
| | named-id | 0.9278 [0.8833, 0.9667] | 0.000 |
| **Llama 3B** | baseline | 0.0778 [0.0444, 0.1167] | 0.000 |
| | permuted | 0.0611 [0.0333, 0.0944] | 0.000 |
| | enhanced | 0.0500 [0.0222, 0.0833] | 0.000 |
| | named-id | 0.7389 [0.6444, 0.8278] | 0.000 |
| **7B** | baseline | 0.0111 [0.0000, 0.0278] | **0.650** |
| | permuted | 0.0833 [0.0389, 0.1333] | 0.144 |
| | enhanced | 0.1778 [0.1222, 0.2389] | 0.167 |
| | named-id | 0.6111 [0.5056, 0.7167] | 0.356 |

## The dissociation replicates on all four models

This is the one clean, general result here. Naming the target by id, changing nothing
else, moves identification accuracy by a large margin in every model tested, across two
families and three scales:

| model | descriptive (`enhanced`) | explicit (`named-id`) |
|---|---|---|
| 1.5B | 0.0278 | **0.6500** |
| 3B | 0.0444 | **0.9278** |
| Llama 3B | 0.0500 | **0.7389** |
| 7B | 0.1778 | **0.6111** |

Execution capability is not the limiting factor for any of them. Whatever is failing is
upstream of performing the edit. The 1.5B and 7B `named-id` figures sit under a
data-quality caveat below, but the direction is unambiguous in all four.

---

## The 7B, and why it is excluded

The registration says, written before any V3 model ran:

> **Malformed rate above ~0.10 for any model.** At that point the measurement is
> substantially about format compliance rather than reference resolution, and that
> model's numbers are reported but excluded from the pooled conclusion.

The 7B exceeds 0.10 in all four conditions. So it is excluded. Its primary outcome was:

```
enhanced - permuted = +0.0944    MDE 0.0582    p = 0.0061    ABOVE MDE
enhanced - baseline = +0.1667                  p = 0.0001
```

**That is the FIRES pattern.** A positive information effect, above the design's
detection threshold, surviving the format-matched control. It is the result this
repository was built to produce and has never produced. And it is inadmissible under a
rule written before it was observed.

The operational test from `RESULTS.md` decides it:

> Would this change have been made identically had the result come out the other way
> around?

If the 7B had shown `enhanced - permuted = 0.0000` and tripped the same falsifier, I
would not now be arguing for its inclusion. I would have written "excluded, and it made
no difference." Wanting to include it *because of which way it came out* is precisely the
reasoning the rule exists to block. **It stays excluded.**

## But the falsifier's premise was wrong

Applying the rule is not the same as endorsing its reasoning, and the post-hoc
characterisation shows the stated rationale does not describe what happened.

`scripts/characterise_malformed.py` classifies every `MALFORMED` response into disjoint
categories. It changes no scoring and is reported alongside the frozen numbers, never in
place of them.

| category | count | share |
|---|---|---|
| **prose refusal** - no document, explicit statement that the target cannot be identified | **318** | **0.964** |
| SVG present but unparseable | 7 | 0.021 |
| prose, not a refusal - partial working, no document | 4 | 0.012 |
| SVG parsed but contained no elements | 1 | 0.003 |
| truncated | 0 | 0 |
| transport error | 0 | 0 |
| **total** | **330** | |

For the 7B specifically the figure is **237 of 237 - every single one a prose refusal.**
Zero truncations, zero parse failures, zero transport errors. Representative:

> *"The SVG document provided does not contain any explicit sizing or positioning
> information that would allow us to determine which shape is 'largest.' Therefore, based
> on the given instructions and the available data, it's not possible to identify a
> specific shape to apply the 5px #000000 border to."*

That is not a format-compliance failure. It is the behaviour the prompt explicitly
invites:

> *If the document does not contain enough information to identify which element the
> instruction refers to, say so instead of guessing.*

The frozen scorer is not wrong as written - it classifies any response yielding no
well-formed SVG as `MALFORMED`, and that is what it was specified to do. The frozen
abstention patterns are deliberately narrow so that ordinary commentary cannot be
mistaken for refusal, which remains the right trade-off. What happened is that the
patterns were calibrated against the behaviour of one model, and a different model
declines in wording they do not match. A pipeline self-consistency check confirms the two
stages agree: the frozen abstention rule matches **0** of these 330 responses, as expected
given abstention is tested before extraction.

**So the exclusion is procedurally correct and substantively mis-motivated.** The 7B's
data is not corrupt. It is well-formed behaviour landing in a class named for corruption.

## What the 7B outcome mix shows

Reported as exploratory. It is not admissible evidence and is not used for any conclusion.

| condition | `NO_EDIT` | `WRONG_TARGET` | `MALFORMED` | correct |
|---|---|---|---|---|
| baseline | 0.044 | 0.228 | **0.650** | 0.011 |
| permuted | 0.017 | 0.728 | 0.144 | 0.083 |
| enhanced | 0.006 | 0.633 | 0.167 | 0.156 |

Adding *any* table converts refusals into attempts: `MALFORMED` falls from 0.650 to ~0.15
and `WRONG_TARGET` rises from 0.228 to ~0.68. That shift happens under `permuted` as well
as `enhanced`, so most of it is **format**, not information - which is exactly the
confound the control exists to expose. On top of that shared format effect, correctness is
roughly twice as high under `enhanced` (0.156) as under `permuted` (0.083).

If that pattern survived a scorer that recognised these refusals, it would be the first
real decomposition this instrument has produced: a large format effect *and* a smaller but
detectable information effect, separated. It cannot be claimed on this run.

---

## Behavioural styles differ by family, not only by scale

| model | baseline `NO_EDIT` | baseline `MALFORMED` | how it declines |
|---|---|---|---|
| 3B | 0.444 | 0.000 | silently returns the document unchanged |
| Llama 3B | 0.450 | 0.000 | silently returns the document unchanged |
| 7B | 0.044 | 0.650 | explains, in prose, that it cannot identify the target |

The two 3B models behave almost identically despite different families; the 7B is
qualitatively different. A plausible reading is that the larger model is better calibrated
- less willing to guess, more willing to state the difficulty explicitly. This design
cannot establish that, and it is recorded as an observation rather than a finding.

The consequence for measurement is concrete and general: **`NO_EDIT` and `MALFORMED`
are the same behaviour expressed in two registers, and a frozen scorer will only recognise
the register it was calibrated on.** Any benchmark comparing models on an
abstention-permitting task inherits this problem.

---

## Conclusions

**Q2 - does the control fire?** **SILENT** on admissible evidence. Two models with clean
data show no information effect above their MDE. `LIMITATIONS.md` section 14 stands: the
format-matched control has still never been exercised in the role it was built for.

**Q1 - generality.** The V1 pattern replicates on `llama3.2:3b` - a different family,
size-matched to the reference - with no context effect and a large `named-id` gap. The
V2 dissociation replicates on all four models. The claim strengthens from *"this model
did not use the supplied geometry"* to *"three models across two families showed no
detectable use of it, while all four could execute the edits when the target was named."*

**On the instrument.** The most consequential finding is not about the models. The frozen
scorer's `MALFORMED` class conflates corrupt output with unrecognised abstention, and that
conflation is invisible until a model with a different refusal style is run. It cost this
study its most informative data point. That is recorded as **FA-013**, under the name
**instrument drift** - the instrument held still while the behaviour it measures moved,
so the semantics of an outcome class changed underneath a name that no longer described
its contents. Nothing in the scorer was broken.

## What follows

**Study V4 does not fix V3.** V3 discovered instrument drift; V4 would test a revised
account of abstention semantics. That is a new hypothesis, not a patch:

```
V3  ->  discovers instrument drift  ->  V4  ->  tests revised abstention semantics
```

It requires a new pre-registration with a revised `abstention_rule_version`, developed
against held-out responses rather than tuned on these, and a re-run of the same four
models under it. Adjusting the rule now and re-scoring these responses would be exactly
the post-hoc adjustment this project has refused throughout, because the rule would be
chosen already knowing which result it produces.

**On the status of the 7B observation.** It happened, it is reported in full, and the
exclusion is not a way of pretending otherwise:

> The observed 7B pattern motivates a pre-registered V4. Because the pre-registered
> exclusion criterion was triggered, it is **not interpreted as confirmatory evidence**
> for the primary hypothesis.

That is the accurate description. An exploratory observation awaiting prospective
confirmation is a different thing from a finding - and also a different thing from
nothing.
