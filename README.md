# svg-ambiguity-bench

**Can a language model edit the shape you meant, when the markup cannot tell it which shape that is?**

An SVG is a drawing program. Its *rendered output* has position, size, and adjacency.
Its *source text* often does not encode any of them in readable form. An instruction like
"make the top-left shape blue" refers to the rendered layer; the edit has to happen in the
source layer. When several elements share a tag and a fill, and their path data is opaque,
the markup contains nothing that tells them apart.

This repository builds a controlled benchmark around that gap, measures a small local model
on it, and tests a method for supplying what the markup is missing.

---

## Status

> **Sprint 2, Step 1 of 14 — repository scaffolding.**
> **No experiments have been run. No results exist yet.**
> This section will carry the headline table once there are numbers. Until then it says so.

The design is frozen: see [`DESIGN_FREEZE.md`](DESIGN_FREEZE.md).

---

## The claim structure (read this before the numbers exist)

The framing matters, so it is stated up front rather than discovered in the discussion section.

**The enhanced arm is the benchmark. The baseline arm is a manipulation check.**

The baseline arm has no dynamic range by construction: if the corpus is genuinely
underdetermined, *every* model scores at the random-selection floor of `1/K`, so the
baseline cannot discriminate between models. Its job is to demonstrate that the corpus
really is underdetermined — that the information was removed, not merely obscured. The
discriminative measurement lives in the enhanced arm, where a model that has the facts
must still resolve the reference correctly.

Stating it the other way round — "we prove models fail, then we fix them" — would be
close to tautological, because the treatment restores information the design deliberately
removed.

---

## What is being measured

**Corpus.** 20–30 generated SVGs. Each contains an *ambiguity set* of K ∈ [4,7] elements
sharing an identical tag and fill, with path data replaced by fixed-length opaque tokens so
position cannot be read off the source. All geometry lives inside `d` — no `transform`, no
`x`/`cx` — because a positional attribute would silently reintroduce the answer.

**Instructions.** Two families, each resolving to exactly one element under a
machine-checked ground truth:

- **Spatial** — `top_left`, `bottom_right`, `leftmost`, `topmost`, …
- **Ordinal size** — `largest`, `second_largest`, `third_largest`, `smallest`

**Arms.** One runner, one prompt template, one difference — an injected context block:

| Arm | Context supplied | Role |
|---|---|---|
| `baseline` | nothing | manipulation check: is the corpus really underdetermined? |
| `permuted` | correctly-formatted facts, **values shuffled between elements** | isolates *format* from *information* |
| `enhanced` | derived visual facts | the benchmark |
| `ceiling` | facts *plus* predicate labels | upper bound; excluded from headline |

The `permuted` arm is the one that decides whether the result means anything. An enumerated
list of elements gives a model referential handles it did not have before — that alone could
move the score with no geometric content whatsoever. Without a control that holds the format
fixed and destroys only the information, "supplying geometry helps" and "supplying a list
helps" are indistinguishable.

**Primary metric: identification accuracy** — did the model act on the intended element?
Reported separately from execution correctness and from collateral edits, because collapsing
those three into one number would attribute a formatting failure to a reasoning failure.
**Abstention is a distinct outcome, not a failure.** Declining to guess on a provably
underdetermined instruction is the epistemically correct response, and a metric that punishes
it would reward confident guessing while the project's own motivation is that models hedge.

---

## Reproducing the numbers

Four tiers, in increasing cost. **A reviewer can stop at Tier 1 and still have checked every
published number.**

| Tier | Verifies | Needs | Time |
|---|---|---|---|
| 1 | every reported number, from committed evaluation rows | Python | ~1 min |
| 2 | the whole scoring chain, from committed raw responses | Python | ~2 min |
| 3 | the corpus is a deterministic function of its seed | + renderer | ~10 min |
| 4 | the model results | + local model | hours |

Tiers 1 and 2 need no model and no GPU. Raw responses are committed, so a skeptical reviewer
can write their own scorer and check whether it reproduces our numbers — which is the
strongest verification this project can offer.

Tier 4 will *not* reproduce bit-for-bit. Small local models vary with backend build,
threading, and quantization even at temperature 0. What must reproduce is the conclusion:
aggregate rates within the reported interval. Claiming exact reproduction would be false.

Commands land as the steps that implement them land.

---

## Repository layout

```
docs/           specs, experiment design, ADRs, results write-up
configs/        experiment configs; every run is reproducible from one
src/svgbench/   the library
tests/          unit, property, integration, and audit suites
scripts/        thin CLI wrappers - no logic lives here
data/frozen/    the immutable corpus. Committed: it is the scientific record
experiments/    raw model responses + per-case evaluations. Committed
results/        computed metrics and figures. Committed
```

## Development

```bash
python -m pip install -e ".[dev]"
```

```bash
python -m pytest
```

Design rationale lives in [`docs/adr/`](docs/adr/) — one short record per non-obvious
decision, with the alternatives considered and what was traded away.

## Limitations

[`LIMITATIONS.md`](LIMITATIONS.md) is a first-class document, not an appendix. It is written
against actual results and is expanded, never softened. Some weaknesses — cluster count,
single-corpus generality — cannot be fixed within a 20–30 SVG budget; the response to those
is narrower claims, stated up front.

## License

MIT — see [`LICENSE`](LICENSE).
