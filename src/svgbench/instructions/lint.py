"""Leakage lint over instruction text.

Supports C1. The instruction names the target by how it *looks*. If it also carries
anything a model could match against the markup - an id, a geometry token, a fill value,
a document position - the task stops being reference resolution and becomes string
matching, and the baseline arm would beat its 1/K floor for a reason that has nothing to
do with the phenomenon under study.

Enforced by checking emitted text rather than by trusting the templates, because the
templates are edited by hand and the check is not.
"""

from __future__ import annotations

import re

# Phrasings that would hand over a position in the markup. `third_largest` legitimately
# contains an ordinal word, so ordinals are not forbidden in general - only phrases that
# refer to the DOCUMENT rather than to the picture.
#
# Matched on WORD BOUNDARIES, not as bare substrings. A naive substring check rejected
# "Add a 3px outline to ..." because "outline" contains "line", which would have
# silently removed every add_stroke instruction from the corpus. A lint that is too
# aggressive is not the safe direction to err in: it quietly shrinks the corpus rather
# than announcing a problem.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "first element",
    "last element",
    "index",
    "line",
    "nth",
    "attribute",
    "path data",
    "document order",
)

_FORBIDDEN_PATTERN = re.compile(
    "|".join(rf"\b{re.escape(phrase)}\b" for phrase in FORBIDDEN_PHRASES)
)


class LeakageError(ValueError):
    """Raised when instruction text contains something matchable against the markup.

    Handled by failing generation, never by rewording the instruction after the fact -
    a leak that reaches the corpus invalidates the baseline arm silently.
    """


def lint_instruction_text(text: str, forbidden: set[str]) -> None:
    """Reject text carrying anything that identifies an element by markup rather than sight.

    Args:
        text: the instruction as the model will receive it.
        forbidden: every element id, geometry token and fill value in the document.

    Raises:
        LeakageError: on the first violation, naming it.
    """
    lowered = text.lower()

    for token in forbidden:
        if token and token.lower() in lowered:
            raise LeakageError(f"instruction leaks {token!r}: {text!r}")

    match = _FORBIDDEN_PATTERN.search(lowered)
    if match:
        raise LeakageError(f"instruction reveals document position ({match.group()!r}): {text!r}")
