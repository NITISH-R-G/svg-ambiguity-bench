"""Prompt assembly: one template, one context slot.

There is exactly one template. Arms differ only in what fills `{context}` - empty for
baseline. A mechanical diff of two arms' prompts must show changes confined to that slot,
and an audit asserts it.

The template is versioned and hashed into the config, because prompt phrasing is an
experimental variable. Biderman et al. 2024 identify undocumented prompt format as a
leading cause of irreproducible evaluation results, with swings above 20%.

Frozen at `instrument-freeze-v1`. Changing it after the tag is an amendment under
RESULTS.md, not a fix.
"""

from __future__ import annotations

TEMPLATE_ID = "edit_svg_v1"
# 1.1 - amended at Step 10, before any baseline run. The placeholder example rendered as
# `{GEOM_...}` because `str.format` collapses `{{` to `{`, so every prompt described the
# tokens as looking different from how they actually appear in the document. Found by
# the smoke test's plumbing check, which exists for exactly this. Affects every arm
# identically. See CHANGELOG for the disclosed amendment.
TEMPLATE_VERSION = "1.1"

# Notes on wording choices, each of which is a deliberate attempt to avoid measuring
# something other than reference resolution:
#
#   - The geometry placeholder is described as redacted, so the model does not try to
#     "repair" it and turn an identification experiment into a syntax experiment (R3).
#   - Returning the whole document is requested explicitly, because a patch format would
#     add a failure mode unrelated to the research question (ADR-0003).
#   - Declining is offered as a legitimate option. Suppressing abstention would hide the
#     behaviour the instrument is trying to measure, and would make C5 unobservable
#     (ADR-0008). It is phrased neutrally so as not to encourage it either.
_TEMPLATE = """\
You are editing an SVG document.

The `d` attribute of each shape has been redacted and replaced with an opaque \
placeholder such as `{{{{GEOM_1234abcd}}}}`. This is intentional. Copy every placeholder \
through to your output exactly as it appears; do not attempt to reconstruct or repair it.

SVG:
{svg}
{context}
Instruction: {instruction}

Return the complete edited SVG document and nothing else. Change only what the \
instruction asks for; leave every other element exactly as it is.

If the document does not contain enough information to identify which element the \
instruction refers to, say so instead of guessing.
"""


def build_prompt(svg: str, instruction: str, context: str) -> str:
    """Assemble the prompt. `context` is empty for the baseline arm."""
    block = f"\n{context}\n" if context.strip() else ""
    return _TEMPLATE.format(svg=svg.strip(), context=block, instruction=instruction)
