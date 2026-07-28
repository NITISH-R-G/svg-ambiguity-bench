# Scoring fixtures

Hand-authored, with the expected verdict **and the reason for it** written down before
the scorer existed. Per [`../../../docs/verification-policy.md`](../../../docs/verification-policy.md),
an oracle derived from the implementation's own output provides no assurance.

Each fixture carries a `reason` field, not only an `expected` one. Two purposes: a
contributor can understand the intent without reading scorer code, and if a fixture ever
fails it is possible to tell whether the *scorer* changed or the *reasoning* did.

## Semantic decisions these fixtures fix

Writing adversarial cases forced several questions that had been implicitly assumed.
Each is answered here, before any model output exists, and each has a fixture.

| Question | Decision | Why |
|---|---|---|
| Is whitespace-only output an abstention? | **No - `MALFORMED`** | `ABSTAINED` requires an explicit refusal. Silence is not a claim about insufficient information; treating it as one would flatter a model that simply failed to answer. |
| Are reordered attributes a change? | **No** | Attribute order is meaningless in XML. Comparison is on a canonical view with attributes sorted. |
| Is `rotate(450)` equal to `rotate(90)`? | **Yes** | This instrument exists to distinguish the rendered layer from the source layer. The two render identically, so rejecting one would penalise a correct edit for a cosmetic reason. Net rotation is compared modulo 360. |
| Is a non-rendering attribute change collateral? | **No** | Collateral is defined over *rendering-relevant* attributes only (`d`, `fill`, `stroke`, `stroke-width`, `transform`, `opacity`, …). An added `data-note` changes nothing a viewer sees. |
| Two ambiguity members edited identically? | **Depends on whether one is the target** | Target among them: `CORRECT_LOOSE` (correct edit plus collateral). Target not among them: `WRONG_TARGET`. The model hedged either way; whether it hedged *onto* the right element is the distinction that matters. |
| Is `#00f` the same as `#0000ff`? | **Yes** | Colour comparison is on a normalised value. Penalising notation would measure formatting, not identification. |
| Is `10` the same as `10.0`? | **Yes** | Numeric comparison uses the configured tolerance. |

## Outcome classes covered

Every class in `docs/02-experiment-design.md` §3 has at least one fixture, plus
adversarial cases: renamed ids, reordered elements, colour-notation variants, right
element with wrong operation, right edit plus collateral, and three phrasings of
abstention.
