"""Extracting an SVG document from a raw model response, and detecting abstention.

Both are classifiers over free text, and both are frozen before the first model output
is observed (`abstention_rule_version` in config). A change to either after the
pre-registration tag is an amendment, not a fix.

Order matters and is deliberate: **abstention is checked first**. A model that explains
why it cannot answer and returns the document unedited has abstained, not produced a
no-op. Checking the document first would downgrade that to `NO_EDIT` and make a model
that explains itself score worse than one that stays silent.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# Explicit statements that the information is insufficient. Deliberately specific:
# ordinary commentary like "I changed the second path's fill" must not match, or every
# well-explained correct answer would be scored as a refusal.
#
# A clarifying question counts. Asking which element was meant is a refusal to guess,
# and RAcQUEt (arXiv 2412.13835) treats it as the behaviour of interest for exactly this
# reason.
_ABSTENTION_PATTERNS: tuple[str, ...] = (
    r"\bcannot determine\b",
    r"\bcan(?:'|no)?t (?:tell|determine|identify|know) which\b",
    r"\bunable to (?:determine|identify|tell)\b",
    r"\bno way to (?:tell|know|determine)\b",
    r"\bdoes not (?:say|specify|indicate|contain) which\b",
    r"\bdoesn'?t (?:say|specify|indicate|contain) which\b",
    r"\bwhich .{0,40}did you mean\b",
    r"\brather than guessing\b",
    r"\binsufficient information\b",
    r"\bnot enough information\b",
    r"\bno positional information\b",
    r"\bambiguous\b.{0,60}\bcannot\b",
)

_ABSTENTION_RE = re.compile("|".join(_ABSTENTION_PATTERNS), re.IGNORECASE | re.DOTALL)

_SVG_RE = re.compile(r"<svg\b.*?</svg\s*>", re.IGNORECASE | re.DOTALL)


def detects_abstention(response: str) -> bool:
    """Whether the response explicitly declines for lack of information.

    Silence is not abstention. Whitespace-only output makes no claim about the markup
    being insufficient, and crediting it would flatter a model that simply failed.
    """
    return bool(_ABSTENTION_RE.search(response))


def extract_svg(response: str) -> str | None:
    """Pull the SVG document out of prose, code fences, or a bare response.

    Returns the LAST complete `<svg>...</svg>` block. Models that narrate before
    answering leave the final document as the answer; models that revise leave the
    corrected version last.
    """
    matches = _SVG_RE.findall(response)
    return matches[-1] if matches else None


def parse_elements(svg_text: str) -> list[ET.Element] | None:
    """Parse and return the shape elements, or None if the document is not well-formed."""
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return None
    return [child for child in root.iter() if child.tag.endswith("path")]


def attributes_of(element: ET.Element) -> dict[str, str]:
    return dict(element.attrib)
