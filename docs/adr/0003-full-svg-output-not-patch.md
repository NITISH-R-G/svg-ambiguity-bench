# ADR-0003 — Model returns a full SVG document, not a patch

**Date:** 2026-07-28 · **Status:** Accepted

## Decision

The model returns the complete edited SVG document. Not a diff, not a JSON edit description,
not an element id.

## Why

The experiment is about **identification under ambiguity**. Every output format adds its own
failure mode, and the question is which one contaminates the measurement least.

A patch or diff format adds patch-syntax failure — line offsets, context matching, hunk
headers — which small models are demonstrably bad at, and which has nothing to do with
resolving a visual reference. A full document isolates identification from that.

It also keeps the *hedging* behaviour observable. Returning "element id X" makes it
structurally impossible to edit three elements, which would hide the exact failure mode that
motivated the project. A full document lets the model hedge, and lets us count it.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Return the target element id only | Cleanest scoring, but makes hedging unobservable — and hedging is the phenomenon under study |
| Unified diff / patch | Adds patch-syntax failure, unrelated to the research question |
| JSON edit description (`{"id": ..., "op": ...}`) | Same objection as id-only, plus a JSON-compliance failure mode |
| Structured tool call | Ties the result to a model's tool-calling ability, which varies wildly across small models and would confound cross-model comparison |

## Tradeoffs

- **Gained:** the failure surface is dominated by the variable of interest; hedging is
  measurable; no dependence on tool-calling support.
- **Given up:** more output tokens per case, so slower runs and a real truncation risk on
  long documents. Mitigated by measuring prompt and completion length before committing to a
  full run, and by recording `truncated` per response so format failure is never silently
  counted as an identification failure.
- **Given up:** scoring is harder — it needs parse, align, canonical diff, and classify
  rather than a string comparison. Accepted: that complexity is testable against fixtures,
  and the fixtures are written before any model runs.
