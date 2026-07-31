"""Does *your* representation admit a format-matched control?

`SPEC.md` §6a-6b proves C2 (presentation invariance) and C3 (assignment-carried
semantics) are necessary: violate either and no value-permutation control can isolate
information from presentation. Those are properties of a representation, so they are
checkable **without calling a model** - which makes them worth checking before spending
an experiment finding out.

This is the executable form of that argument. Pass your renderer and a representative
mapping; get back which conditions fail and why.

    from fmtcontrol import admits_control

    report = admits_control(my_renderer, my_facts)
    if not report.ok:
        print(report)            # names the failing condition and shows a counterexample

Standard library only, like the rest of the package.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Hashable, Mapping
from dataclasses import dataclass, field
from itertools import combinations, pairwise

# Checking every permutation is n! renders - 3.6 million at n=10, infeasible and
# unnecessary. Transpositions are the cheap high-yield family: they are the smallest
# non-identity permutations, they generate S_n, and a renderer whose presentation is
# assignment-sensitive almost always reveals it by swapping one pair. Random draws cover
# the rest of the group probabilistically. Neither is a proof of invariance and the report
# says so.
_MAX_TRANSPOSITIONS = 190  # n(n-1)/2 for n = 20
_DEFAULT_RANDOM_DRAWS = 64

# P has been wrong twice, and both mistakes are worth recording because they are the two
# ways this functional can fail.
#
# First attempt collapsed letters and digits into a shape string. `annual-report` and
# `press-q2` then differed even when padded to identical width, so P measured VALUE
# CONTENT and rejected the canonical passing case.
#
# Second attempt recorded where fields begin on each line. In a right-aligned numeric
# column the first digit sits at an index determined by the value's magnitude, so those
# indices move whenever values move - which is the manipulation, not a confound. A
# component that changes precisely when the assignment changes makes C2 unsatisfiable by
# construction, and it rejected the benchmark's own renderer.
#
# The surviving rule: every component of P must be invariant under permutation for a
# fixed-width renderer, and must vary for a width-sensitive one. Ordered line lengths
# satisfy exactly that. A multiset of line lengths would not - it is invariant even for
# free text when the keys are equal width, so it would miss the case that matters most.


@dataclass(frozen=True)
class Presentation:
    """Everything about a rendered string except which entity holds which value.

    This is `P` in the specification. Equality of two `Presentation` values is the
    operational meaning of `P(render(f)) == P(render(f o pi))`.

    Every component must depend only on the container. A component that varies with the
    values themselves would make P assignment-dependent by construction, and every
    representation would fail C2.
    """

    tokens: int
    lines: int
    characters: int
    line_lengths: tuple[int, ...]

    def differences(self, other: Presentation) -> list[str]:
        """Which components differ. Empty means presentation-invariant on this pair."""
        out: list[str] = []
        if self.tokens != other.tokens:
            out.append(f"token count {self.tokens} -> {other.tokens}")
        if self.lines != other.lines:
            out.append(f"line count {self.lines} -> {other.lines}")
        if self.characters != other.characters:
            out.append(f"character count {self.characters} -> {other.characters}")
        if self.line_lengths != other.line_lengths:
            out.append("line widths changed (line length is assignment-dependent)")
        return out


def presentation_of(text: str) -> Presentation:
    """Compute `P`. Line order is preserved, because row order is part of presentation."""
    lines = text.splitlines()
    return Presentation(
        tokens=len(text.split()),
        lines=len(lines),
        characters=len(text),
        line_lengths=tuple(len(line) for line in lines),
    )


@dataclass(frozen=True)
class AdmissibilityReport:
    """Which necessary conditions hold, and the evidence."""

    ok: bool
    c1_permutable: bool
    c2_presentation_invariant: bool
    c3_assignment_carried: bool
    permutations_checked: int
    permutations_total: str
    failures: tuple[str, ...] = ()
    counterexample: str | None = None
    notes: tuple[str, ...] = field(default=())

    def __str__(self) -> str:
        head = "admits a format-matched control" if self.ok else "does NOT admit a control"
        lines = [
            f"{head}  (C1={self.c1_permutable} C2={self.c2_presentation_invariant} "
            f"C3={self.c3_assignment_carried})",
            f"  checked {self.permutations_checked} of {self.permutations_total} permutations",
        ]
        lines += [f"  FAIL  {f}" for f in self.failures]
        lines += [f"  note  {n}" for n in self.notes]
        if self.counterexample:
            lines.append("  counterexample:")
            lines += [f"    {line}" for line in self.counterexample.splitlines()]
        return "\n".join(lines)


def _permutation_count(n: int) -> int:
    """|S_n|, capped so the sampling budget arithmetic stays cheap for large n."""
    if n > 12:
        return 1 << 62
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def _factorial_str(n: int) -> str:
    if n > 12:
        return f"{n}! (astronomically many)"
    return f"{_permutation_count(n):,}"


def _apply[E: Hashable, V](facts: Mapping[E, V], order: list[E]) -> dict[E, V]:
    """Reassign values along `order`, preserving entity iteration order."""
    entities = list(facts)
    return dict(zip(entities, (facts[e] for e in order), strict=True))


def _looks_sorted_by_value[E: Hashable, V](facts: Mapping[E, V]) -> bool:
    """Whether values appear in sorted order - the classic C3 violation.

    If rows are ordered by the quantity of interest, rank is legible from position, so
    permuting values leaves the information channel intact (SPEC Proposition 2) and the
    control is vacuous rather than merely weak.
    """
    values = list(facts.values())
    if len(values) < 3:
        return False
    keys: list[object] = []
    for value in values:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            keys.append(value)
        elif isinstance(value, (tuple, list)) and value:
            first = value[0]
            if isinstance(first, (int, float)) and not isinstance(first, bool):
                keys.append(first)
            else:
                return False
        else:
            return False
    ascending = all(a <= b for a, b in pairwise(keys))  # type: ignore[operator]
    descending = all(a >= b for a, b in pairwise(keys))  # type: ignore[operator]
    return ascending or descending


def admits_control[E: Hashable, V](
    render: Callable[[Mapping[E, V]], str],
    facts: Mapping[E, V],
    *,
    random_draws: int = _DEFAULT_RANDOM_DRAWS,
    seed: int = 0,
) -> AdmissibilityReport:
    """Check the necessary conditions C1-C3 for one renderer and one representative mapping.

    Args:
        render: your renderer. Called many times; must be pure and reasonably fast.
        facts: a representative entity -> value mapping. Representative matters more than
            large: values of *differing width* are what expose C2 violations, so a mapping
            whose values all happen to be the same length will pass a check that real data
            would fail.
        random_draws: random permutations sampled beyond the transpositions.
        seed: for reproducibility of the random draws.

    Returns:
        An `AdmissibilityReport`. `ok` means no violation was found - **not** that none
        exists. C2 is checked over a sample of a factorially large group, and the report
        states the coverage rather than implying a proof.

    Note:
        C3 is only partially checkable. Whether the information under test is recoverable
        from the presentation depends on what that information *is*, which this function
        cannot know. It detects the common mechanical case - values already in sorted
        order - and says so. A clean C3 result is weaker evidence than a clean C2 result.
    """
    entities = list(facts)
    n = len(entities)
    notes: list[str] = []
    failures: list[str] = []

    # C1: a permutation must exist at all.
    c1 = n >= 2 and len({repr(v) for v in facts.values()}) >= 2
    if n < 2:
        failures.append("C1: fewer than two entities, so every permutation is the identity")
    elif not c1:
        failures.append("C1: all values are equal, so no permutation displaces anything")
    if not c1:
        return AdmissibilityReport(
            ok=False,
            c1_permutable=False,
            c2_presentation_invariant=False,
            c3_assignment_carried=False,
            permutations_checked=0,
            permutations_total=_factorial_str(max(n, 1)),
            failures=tuple(failures),
        )

    baseline_text = render(facts)
    baseline = presentation_of(baseline_text)

    # Transpositions first: smallest non-identity permutations, and the ones most likely
    # to expose width-sensitivity. Capped so a large entity set does not become O(n^2)
    # renders without warning.
    pairs = list(combinations(range(n), 2))
    if len(pairs) > _MAX_TRANSPOSITIONS:
        rng_pairs = random.Random(seed ^ 0x5EED)
        pairs = rng_pairs.sample(pairs, _MAX_TRANSPOSITIONS)
        notes.append(f"n={n}: sampled {_MAX_TRANSPOSITIONS} of {n * (n - 1) // 2} transpositions")

    checked = 0
    counterexample: str | None = None
    c2 = True

    for i, j in pairs:
        order = entities[:]
        order[i], order[j] = order[j], order[i]
        candidate = presentation_of(render(_apply(facts, order)))
        checked += 1
        differences = baseline.differences(candidate)
        if differences:
            c2 = False
            if counterexample is None:
                counterexample = (
                    f"swapping {entities[i]!r} and {entities[j]!r} changes presentation:\n"
                    + "\n".join(f"  - {d}" for d in differences)
                )
            break

    if c2:
        rng = random.Random(seed)
        # Never draw more than the group holds. At n=4 there are 24 permutations and 64
        # draws would report "checked 68 of 24" - incoherent, and mostly re-checking
        # duplicates. Seen distinct orders are tracked so the count means what it says.
        seen: set[tuple[int, ...]] = set()
        budget = min(random_draws, _permutation_count(n) - 1 - checked)
        attempts = 0
        while len(seen) < max(budget, 0) and attempts < random_draws * 8:
            attempts += 1
            order = entities[:]
            rng.shuffle(order)
            signature = tuple(entities.index(e) for e in order)
            if signature in seen or order == entities:
                continue
            seen.add(signature)
            candidate = presentation_of(render(_apply(facts, order)))
            checked += 1
            differences = baseline.differences(candidate)
            if differences:
                c2 = False
                counterexample = "a random permutation changes presentation:\n" + "\n".join(
                    f"  - {d}" for d in differences
                )
                break

    if not c2:
        failures.append(
            "C2: presentation is assignment-dependent. Any measured difference between "
            "arms confounds information with presentation (SPEC Proposition 1), so the "
            "control is inert rather than merely weak"
        )

    # C3, mechanically detectable case only.
    c3 = not _looks_sorted_by_value(facts)
    if not c3:
        failures.append(
            "C3: values appear in sorted order, so rank is legible from row position. "
            "Permuting leaves that channel intact and the control is vacuous "
            "(SPEC Proposition 2)"
        )
    notes.append(
        "C3 is only partially checkable here: whether the information under test is "
        "recoverable from presentation depends on what that information is"
    )

    if all(len(repr(v)) == len(repr(next(iter(facts.values())))) for v in facts.values()):
        notes.append(
            "all values have equal repr width, so this mapping cannot expose a "
            "width-sensitivity violation - retry with values of differing width"
        )

    return AdmissibilityReport(
        ok=c1 and c2 and c3,
        c1_permutable=c1,
        c2_presentation_invariant=c2,
        c3_assignment_carried=c3,
        permutations_checked=checked,
        permutations_total=_factorial_str(n),
        failures=tuple(failures),
        counterexample=counterexample,
        notes=tuple(notes),
    )
