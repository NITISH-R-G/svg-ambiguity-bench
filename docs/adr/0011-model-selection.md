# ADR-0011 — Model selection

**Date:** 2026-07-29 · **Status:** Accepted

## Decision

**`qwen2.5-coder:3b`** via Ollama, CPU, greedy decoding.

Chosen by measurement, before any baseline run, from two candidates pulled specifically
so the choice would not have to be a guess.

## Why a measurement was needed

Assumption **A1**: the model emits syntactically valid SVG often enough that malformed
output is a *minority* failure mode. If it does not, the experiment measures format
compliance rather than reference resolution — risk **R3** — and the headline number
becomes uninterpretable.

**R4** explicitly sanctions swapping models before the baseline provided the reason is
recorded. This is that record.

## The measurement

Both models, the same 12 cases sampled across the frozen corpus, `enhanced` context,
temperature 0.

| | `qwen2.5-coder:1.5b` | `qwen2.5-coder:3b` |
|---|---|---|
| **Unparseable output** | **4/12 (33%)** | **0/12 (0%)** |
| Scored `MALFORMED` | 3/12 | 0/12 |
| Truncated | 0/12 | 0/12 |
| Median latency | 6.6 s | 15.2 s |
| Median output | 340 tokens | 366 tokens |
| Projected 540 calls | ~1.0 h | ~2.3 h |

## Why 3b

A third of responses failing to parse is not a minority failure mode in any useful
sense. It would mean a substantial share of every arm's score was determined by whether
the model could emit well-formed XML, which is not the question. The 3b eliminates that
failure entirely on this sample at 2.3x the runtime, and 2.3 hours is affordable.

Note that the smoke test script printed `PASS` for the 1.5b against a 30% threshold. That
threshold was an arbitrary constant written into the script without justification, and it
is not the basis of this decision — the measured 0% versus 33% is. The constant has been
left in place as a rough guard but should not be read as a considered criterion.

## Alternatives considered

| Option | Rejected because |
|---|---|
| `qwen2.5-coder:1.5b` | 33% unparseable. Fast, but the experiment would substantially measure format compliance |
| `qwen2.5-coder:7b` | The original config default. Never pulled: the 3b already satisfies A1 at 0%, so the extra 4.7 GB and ~7 h buys nothing measurable |
| A general instruct model | Code-specialised models are more reliable at emitting well-formed markup, which is precisely the failure mode A1 is about |
| Deciding without measuring | The 33% versus 0% gap was far larger than expected. A guess would probably have been wrong |

## Tradeoffs

- **Gained:** A1 satisfied at 0% malformed on the smoke sample, so the headline measures
  identification rather than syntax.
- **Given up:** runtime, 1.0 h → 2.3 h. Cheap.
- **Given up:** the "smallest model that works" framing. 3b is still small and CPU-only,
  which is what the assignment asks for.
- **Not established:** that 0/12 generalises to 0/180. The full run reports the malformed
  rate per arm, and if it turns out materially non-zero that is reported rather than
  explained away.

## What did not change

The dataset, scoring rules, predicates, leakage checks and evaluation rules are untouched.
Model choice is not among the things `RESULTS.md` freezes, and `corpus_config_hash` is
unaffected by design — model settings were deliberately excluded from corpus identity
(ADR-0007, and the two-hash split at Step 2) precisely so this decision could be made
without invalidating the corpus.
