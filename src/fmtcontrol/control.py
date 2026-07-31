"""The permutation and its invariant checks.

Deliberately small. The whole idea is roughly forty lines; the rest is the checking that
makes it trustworthy, which is the part people skip.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Hashable, Mapping
from dataclasses import dataclass, field

# An identity permutation silently turns the control arm into a second treatment arm,
# with no test failing anywhere. With few entities it happens often enough to matter:
# at 4 entities a uniform shuffle is the identity 1 time in 24.
_MAX_RESHUFFLE = 64


def permute[E: Hashable, V](
    facts: Mapping[E, V],
    key: str,
    seed: int,
    *,
    require_displacement: bool = True,
) -> dict[E, V]:
    """Return the same entities with the values redistributed between them.

    Preserves, exactly: the entity set, the iteration order, and the multiset of values.
    Destroys: which entity each value belongs to. That is the whole manipulation.

    Args:
        facts: entity -> fact. Values are moved wholesale, never modified, so a value can
            be any object at all - a tuple, a row, a passage.
        key: identifies this item. The permutation is derived from it, so it is
            deterministic per item but uncorrelated across items.
        seed: an experiment-level seed, combined with `key`. Keep it **independent of
            whatever seed generated your data**, or the permutation can correlate with
            the structure it is meant to be independent of.
        require_displacement: reject the identity permutation. Leave this on unless you
            have a specific reason; see `_MAX_RESHUFFLE`.

    Returns:
        A new mapping. The input is not modified.

    Raises:
        ValueError: if a non-identity permutation could not be found. With fewer than two
            distinct values none exists, and that is a property of the data rather than a
            transient failure - a single-row context cannot be format-matched, because
            permuting it changes nothing.
    """
    entities = list(facts)
    values = [facts[e] for e in entities]

    if len(entities) < 2:
        if require_displacement:
            raise ValueError(
                f"cannot build a control for {len(entities)} entities: a permutation of "
                "fewer than two entities is necessarily the identity, so this item has "
                "no format-matched control. Exclude it, or report it separately."
            )
        return dict(facts)

    # Derived from the item, not drawn from a stream, so the same item always gets the
    # same permutation regardless of evaluation order or parallelism.
    digest = hashlib.sha256(f"{seed}:{key}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))

    shuffled = values[:]
    for _ in range(_MAX_RESHUFFLE):
        rng.shuffle(shuffled)
        if not require_displacement or _displaced(values, shuffled):
            return dict(zip(entities, shuffled, strict=True))

    # Reached only when every value is equal, so no permutation displaces anything.
    raise ValueError(
        f"no displacing permutation after {_MAX_RESHUFFLE} attempts for key {key!r}: "
        "all values appear to be identical, so a permuted arm would be byte-identical "
        "to the enhanced arm and would not be a control."
    )


def _displaced[V](original: list[V], shuffled: list[V]) -> bool:
    """Whether at least one position changed value.

    Compared by value, not identity: two equal values swapping places is not a
    displacement, because the rendered context is unchanged.
    """
    return any(a != b for a, b in zip(original, shuffled, strict=True))


@dataclass(frozen=True)
class ControlReport:
    """The result of checking that a permuted arm is a valid control."""

    ok: bool
    failures: tuple[str, ...] = ()
    checks_run: tuple[str, ...] = ()
    token_delta: int | None = None
    notes: tuple[str, ...] = field(default=())

    def __str__(self) -> str:
        if self.ok:
            return f"control OK ({len(self.checks_run)} checks)"
        return "control INVALID:\n" + "\n".join(f"  - {f}" for f in self.failures)


def check_control[E: Hashable, V](
    enhanced: Mapping[E, V],
    permuted: Mapping[E, V],
    enhanced_text: str | None = None,
    permuted_text: str | None = None,
    *,
    token_tolerance: int = 4,
) -> ControlReport:
    """Check that `permuted` is a format-matched, information-destroyed version.

    Each check corresponds to a way the control can quietly stop being one. Passing the
    rendered strings enables the format checks; without them only the structural checks
    run, and the report says so.

    Args:
        enhanced: the treatment mapping.
        permuted: the candidate control mapping.
        enhanced_text: the rendered treatment context, if available.
        permuted_text: the rendered control context, rendered by the **same** code.
        token_tolerance: permitted difference in whitespace-delimited token count.
            Non-zero because values of differing width can shift alignment padding.

    Returns:
        A `ControlReport`. Check `.ok`; `.failures` explains each problem.
    """
    failures: list[str] = []
    checks: list[str] = []
    notes: list[str] = []

    checks.append("same entity set")
    if set(enhanced) != set(permuted):
        missing = set(enhanced) ^ set(permuted)
        failures.append(f"entity sets differ; symmetric difference {sorted(map(str, missing))!r}")

    checks.append("same entity order")
    if list(enhanced) != list(permuted):
        failures.append("entity iteration order differs, so row order is not held fixed")

    checks.append("identical value multiset")
    if not _same_multiset(list(enhanced.values()), list(permuted.values())):
        failures.append(
            "value multisets differ: the permutation altered the information content "
            "rather than only its assignment"
        )

    checks.append("mapping actually destroyed")
    if set(enhanced) == set(permuted) and all(enhanced[e] == permuted[e] for e in enhanced):
        failures.append(
            "permutation is the identity: this arm is a second copy of the treatment, not a control"
        )

    token_delta: int | None = None
    if enhanced_text is not None and permuted_text is not None:
        checks.append("token count within tolerance")
        token_delta = abs(len(enhanced_text.split()) - len(permuted_text.split()))
        if token_delta > token_tolerance:
            failures.append(
                f"token counts differ by {token_delta} (> {token_tolerance}): prompt "
                "length has become a confound between arms"
            )

        checks.append("line count identical")
        if enhanced_text.count("\n") != permuted_text.count("\n"):
            failures.append("line counts differ, so the arms are not format-matched")

        checks.append("rendered text actually differs")
        if enhanced_text == permuted_text:
            failures.append("rendered contexts are byte-identical: no manipulation occurred")
    else:
        notes.append("rendered text not supplied; format checks skipped")

    return ControlReport(
        ok=not failures,
        failures=tuple(failures),
        checks_run=tuple(checks),
        token_delta=token_delta,
        notes=tuple(notes),
    )


def _same_multiset[V](left: list[V], right: list[V]) -> bool:
    """Multiset equality without requiring values to be hashable or orderable.

    Facts are often tuples or small records; some are hashable, some are not. Try the
    cheap path, then a sortable path, then fall back to quadratic matching so that an
    unhashable value degrades performance rather than raising.
    """
    if len(left) != len(right):
        return False
    try:
        return sorted(left) == sorted(right)  # type: ignore[type-var]
    except TypeError:
        pass
    try:
        from collections import Counter

        return Counter(left) == Counter(right)
    except TypeError:
        pass

    remaining = list(right)
    for item in left:
        for index, candidate in enumerate(remaining):
            if item == candidate:
                del remaining[index]
                break
        else:
            return False
    return True
