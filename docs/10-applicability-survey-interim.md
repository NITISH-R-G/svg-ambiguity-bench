# Applicability survey - interim, and underpowered

**Status: INCOMPLETE. 3 of 15 papers assessed. A pre-registered falsifier has fired.**

Pre-registered at
[`docs/09-applicability-survey-preregistration.md`](09-applicability-survey-preregistration.md).
That document says:

> **Fewer than 8 papers can be assessed** from available sources: the pilot is
> underpowered and reports counts only, no ratio.

Three were assessed to the standard the coding scheme requires — reading the ablation
setup, not the abstract. **So no ratio is computed here and no outcome band is claimed.**
Padding to fifteen from abstracts would have violated the second falsifier, which
prohibits coding "separating control present" from an abstract for more than half the
sample. Fifteen shallow rows would have looked like a result and been worth less than
three real ones.

---

## What was assessed

| # | Paper | Claim present? | Applicability condition | Separating control | Conclusion could change? |
|---|---|---|---|---|---|
| 1 | [LLM-Generated Metadata to Enhance RAG](https://arxiv.org/html/2512.05411v1) | **Yes** — "metadata-enriched approaches consistently outperform content-only baselines", 82.5% vs 73.3% precision | **Met** — fixed schema: content type, keywords, entities, categories, services, tools, summaries, intents | **None.** Compares content-only vs metadata-enriched. No condition corrupts or scrambles the metadata | **Unknown, and material.** Prefix-fusion prepends structured text; part of the gain could be structural |
| 2 | [CRUX: Controlled RAG Context Evaluation](https://arxiv.org/html/2506.20051) | Framework, not an improvement claim | **Not met** — retrieved passages are variable-length free text | **None of this kind.** Controls vary presence, relevance and completeness; they "do not scramble, destroy, or randomize information content" | n/a |
| 3 | [PersonaAgent](https://arxiv.org/html/2506.06254v2) | **Yes** — removing persona drops LaMP-1 F1 from 0.918 to 0.855 | **Not met** — persona is free-text narrative | **None.** Ablations are `w/o persona`, `w/o memory`, `w/o action` — all removals. Never mismatched or another user's memory | **Unknown.** Nothing distinguishes "this user's persona helps" from "a persona-shaped block helps" |

## What three papers can and cannot support

**Cannot support:** any ratio, any outcome band, any claim about the field.

**Can support, weakly, as a hypothesis for the full survey:** two observations that were
not in the pre-registered prediction and are worth carrying forward.

**The controls that exist are removals, not substitutions.** All three vary context by
*taking it away*. None substitutes content while holding the container fixed. That is the
distinction the method is about, and its absence here is at least consistent with the gap
being real — on three papers, which is to say barely at all.

**The applicability condition bit harder than predicted.** I predicted 40-60% of papers
would meet it. Two of three did not, both for the same reason: **the context is
variable-length free text.** Retrieved passages and narrative personas cannot be permuted
without changing token counts.

If that holds at N=15, the honest framing changes. The method would not be "a control for
context augmentation" but "a control for **structured** context augmentation" — metadata
records, tool schemas, attribute tables, typed fields. That is a narrower claim than
`METHOD.md` currently makes even after the FA-014 correction, and RAG-with-passages, the
headline application, would be mostly **out of scope** rather than the flagship case.

That is the **INAPPLICABLE** outcome the pre-registration names as most damaging to the
framing. Three papers cannot establish it. They are enough to say it is live.

## An observation about who noticed

Paper 3's own missing control was flagged during assessment as *"a meaningful robustness
check"* that the authors did not run. That is the method's exact use case, arrived at
independently while reading. One instance is an anecdote; it is recorded because if the
pattern repeats at N=15 it stops being one.

## To finish this

12 more papers, read to ablation-setup depth, across RAG-with-metadata, tool schemas,
memory and personalisation, and structured prompting. Sampling should deliberately
oversample **structured** context, since the pilot suggests that is where applicability
lives — and that sampling change must be declared as an amendment to the pre-registration
rather than made quietly, because it will raise the applicability rate by construction.

Roughly a day. It is the highest-value day available, because it tests whether the project
addresses a problem the field has, and it can return the answer *no*.
