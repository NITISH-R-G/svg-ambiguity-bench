"""Context providers - the manipulated variable, and the only difference between arms.

The signature is deliberately narrow:

    provide(model_visible_svg, svg_id) -> ContextBlock

**The instruction is not a parameter.** Instruction-blindness is therefore enforced by
the type system rather than by reviewer discipline: a contributor cannot leak the
instruction into the context because it is not reachable from inside a provider. That
guarantee holds for code nobody has written yet, which no runtime assertion can do
(ADR-0005).

Context is computed once per SVG and reused across every instruction targeting it. That
is both an efficiency win and a structural proof of blindness - if one block serves six
different instructions, it demonstrably depends on none of them.

The `enhanced` provider emits PRIMITIVE FACTS ONLY - never a predicate label. Emitting
"this is the top-left one" would make the task a dictionary lookup rather than a
reference resolution, and would measure the provider rather than the model. That
condition exists separately as `ceiling`, excluded from the headline by construction.
"""

from __future__ import annotations

from typing import Protocol

from fmtcontrol import permute
from svgbench.geometry import ElementGeometry


class ContextProvider(Protocol):
    """One arm's context. Note the absence of an instruction parameter."""

    name: str

    def provide(self, svg_id: str, geometry: dict[str, ElementGeometry]) -> str: ...


def _format_facts(rows: list[tuple[str, float, float, float]]) -> str:
    """Render element facts as a fixed-width table.

    Identical formatting is used by `enhanced`, `permuted` and `ceiling`, so that the
    only thing differing between those arms is which numbers sit in the cells. If the
    formats differed, `permuted` would no longer be a format-matched control and C3
    would be untestable.
    """
    lines = [
        "Element geometry (rendered):",
        "  id           centre_x  centre_y      area",
    ]
    for element_id, x, y, area in rows:
        lines.append(f"  {element_id:<12} {x:8.1f}  {y:8.1f}  {area:8.0f}")
    return "\n".join(lines)


def _rows(geometry: dict[str, ElementGeometry]) -> list[tuple[str, float, float, float]]:
    """Facts in document order, so the context introduces no ordering the markup lacks."""
    return [
        (element_id, g.centroid[0], g.centroid[1], g.area) for element_id, g in geometry.items()
    ]


class NullProvider:
    """The `baseline` arm: no context at all.

    Not a degenerate case to be optimised away - it is the manipulation check. If the
    corpus is genuinely under-determined, every model scores at the 1/K floor here.
    """

    name = "null"

    def provide(self, svg_id: str, geometry: dict[str, ElementGeometry]) -> str:
        return ""


class EnhancedProvider:
    """The `enhanced` arm: the geometric facts the markup does not encode.

    Centroid and area, per element, in document order. Nothing else - no ranks, no
    labels, no predicate names. The model must still do the resolution.
    """

    name = "enhanced"

    def provide(self, svg_id: str, geometry: dict[str, ElementGeometry]) -> str:
        return _format_facts(_rows(geometry))


class PermutedProvider:
    """The `permuted` arm: the same table, with the values shuffled between elements.

    **The control the central claim rests on.** An enhanced prompt changes two things at
    once - it adds geometric facts, and it adds an enumerated list giving every element a
    referential handle it did not previously have. Enumeration alone could move the score
    with no geometric content whatsoever.

    Permutation preserves the marginal distribution of every number exactly, the row
    count, the column widths and the token count. Only the mapping from element to fact
    is destroyed. Whatever remains of the gain over baseline is format, not information.

    The shuffle is seeded independently of the corpus seed, so it cannot correlate with
    the layout it is meant to be independent of.
    """

    name = "permuted"

    def __init__(self, permutation_seed: int) -> None:
        self._seed = permutation_seed

    def provide(self, svg_id: str, geometry: dict[str, ElementGeometry]) -> str:
        rows = _rows(geometry)
        # Delegates to `fmtcontrol`, which is domain-independent and knows nothing about
        # SVG. The extraction is behaviour-preserving: an audit asserts that all 540
        # committed V1 prompts still reconstruct byte-for-byte through this path, so the
        # frozen instrument is unchanged and V1's numbers still describe this code.
        facts = {element_id: (x, y, area) for element_id, x, y, area in rows}
        permuted = permute(facts, key=svg_id, seed=self._seed)
        return _format_facts([(element_id, *permuted[element_id]) for element_id, *_ in rows])


class CeilingProvider:
    """The `ceiling` arm: facts plus predicate labels. EXCLUDED FROM THE HEADLINE.

    Hands over the answer, so it will score near-perfectly and proves nothing about
    reference resolution. It earns its place only as a diagnostic: if `ceiling` is also
    imperfect, the residual errors in `enhanced` are reasoning or execution failures
    rather than information failures.

    Not used in the three-arm run.
    """

    name = "ceiling"

    def provide(self, svg_id: str, geometry: dict[str, ElementGeometry]) -> str:
        rows = _rows(geometry)
        by_area = sorted(rows, key=lambda r: r[3], reverse=True)
        ranks = {r[0]: i + 1 for i, r in enumerate(by_area)}
        leftmost = min(rows, key=lambda r: r[1])[0]

        lines = [_format_facts(rows), "", "Derived labels:"]
        for element_id, *_ in rows:
            labels = [f"area rank {ranks[element_id]}"]
            if element_id == leftmost:
                labels.append("leftmost")
            lines.append(f"  {element_id:<12} {', '.join(labels)}")
        return "\n".join(lines)


def build_provider(name: str, permutation_seed: int) -> ContextProvider:
    if name == "null":
        return NullProvider()
    if name == "enhanced":
        return EnhancedProvider()
    if name == "permuted":
        return PermutedProvider(permutation_seed)
    if name == "ceiling":
        return CeilingProvider()
    raise ValueError(f"unknown context provider {name!r}")
