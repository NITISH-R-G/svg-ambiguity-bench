"""Matching returned elements to original ones.

A model may rename ids, reorder elements, or rewrite geometry. Identity has to survive
all three, or ordinary output variation would be scored as editing.

Four tiers, tried in order, and the WEAKEST tier used anywhere in a document is recorded
for that case. That matters: if results ever depend on position-based matching, the
scoring is resting on an assumption about output ordering that nothing guarantees, and
the reported tier makes that visible instead of leaving it buried.

  TOKEN     the opaque geometry token, unique per element and preserved by contract.
            Primary, and it survives a model that renames every id.
  ID        the `id` attribute. Survives a model that rewrites geometry.
  POSITION  document index. Last resort; assumes the model preserved ordering.
  FAILED    no correspondence - scored MALFORMED rather than guessed at.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from svgbench.evaluation.records import AlignmentTier

_TOKEN_RE = re.compile(r"^\{\{GEOM_[0-9a-f]{8}\}\}$")

_TIER_ORDER: dict[AlignmentTier, int] = {
    "TOKEN": 0,
    "ID": 1,
    "POSITION": 2,
    "FAILED": 3,
}


def _token_of(element: ET.Element) -> str | None:
    data = element.get("d", "")
    return data if _TOKEN_RE.match(data) else None


def align(
    original: list[ET.Element],
    returned: list[ET.Element],
) -> tuple[dict[str, ET.Element | None], AlignmentTier]:
    """Map each original element id to its counterpart, or None if absent.

    Absence is a legitimate result, not a failure: for the `delete` operation it is the
    correct edit. The caller distinguishes absent-and-expected from absent-and-not.
    """
    unmatched = list(returned)
    mapping: dict[str, ET.Element | None] = {}
    worst: AlignmentTier = "TOKEN"

    by_token: dict[str, list[ET.Element]] = {}
    for element in unmatched:
        token = _token_of(element)
        if token is not None:
            by_token.setdefault(token, []).append(element)

    by_id: dict[str, list[ET.Element]] = {}
    for element in unmatched:
        element_id = element.get("id")
        if element_id:
            by_id.setdefault(element_id, []).append(element)

    for index, source in enumerate(original):
        source_id = source.get("id", f"__index_{index}")

        token = _token_of(source)
        if token and by_token.get(token):
            mapping[source_id] = by_token[token].pop(0)
            continue

        if by_id.get(source_id):
            mapping[source_id] = by_id[source_id].pop(0)
            worst = _weaker(worst, "ID")
            continue

        # Position, only if the returned document has an element at that index which
        # nothing else has claimed.
        if index < len(returned) and returned[index] in unmatched:
            candidate = returned[index]
            if _token_of(candidate) is None or candidate.get("id") is None:
                mapping[source_id] = candidate
                worst = _weaker(worst, "POSITION")
                continue

        mapping[source_id] = None

    return mapping, worst


def _weaker(current: AlignmentTier, candidate: AlignmentTier) -> AlignmentTier:
    return candidate if _TIER_ORDER[candidate] > _TIER_ORDER[current] else current


def unmatched_returned(
    original: list[ET.Element],
    returned: list[ET.Element],
    mapping: dict[str, ET.Element | None],
) -> list[ET.Element]:
    """Returned elements with no original counterpart - invented by the model."""
    claimed = {id(element) for element in mapping.values() if element is not None}
    return [element for element in returned if id(element) not in claimed]
