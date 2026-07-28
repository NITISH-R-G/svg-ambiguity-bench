"""Instruction phrasing.

Two independent banks - one naming the target, one naming the edit - composed into an
instruction. Two phrasings each gives four wordings per (predicate, operation) pair from
sixteen short strings rather than forty-eight.

Multiple phrasings are not decoration. CanItEdit (arXiv 2312.12450) demonstrated that
instruction register alone changes measured edit accuracy, so a single wording per
predicate would confound phrasing with capability and leave the result conditional on a
choice nobody swept.

Phrasing must never identify an element by anything a model could match against the
markup. No ids, no geometry tokens, no fill values, no document positions. The lint in
`svgbench.instructions.lint` enforces this rather than trusting the templates.
"""

from __future__ import annotations

# How to refer to the target. Index 0 is terse, index 1 more explicit - roughly the
# "lazy" and "descriptive" registers CanItEdit contrasts.
TARGET_PHRASES: dict[str, tuple[str, str]] = {
    "top_left": ("the top-left shape", "the shape nearest the top-left corner"),
    "top_right": ("the top-right shape", "the shape nearest the top-right corner"),
    "bottom_left": ("the bottom-left shape", "the shape nearest the bottom-left corner"),
    "bottom_right": ("the bottom-right shape", "the shape nearest the bottom-right corner"),
    "leftmost": ("the leftmost shape", "the shape furthest to the left"),
    "rightmost": ("the rightmost shape", "the shape furthest to the right"),
    "topmost": ("the topmost shape", "the shape furthest towards the top"),
    "bottommost": ("the bottommost shape", "the shape furthest towards the bottom"),
    # Ordinal descriptive variants avoid a trailing prepositional phrase. "the biggest
    # shape by area" composes into "Rotate the biggest shape by area by 90 degrees",
    # where the stacked "by" clauses read as a parsing puzzle. Awkward phrasing adds
    # variance that has nothing to do with reference resolution.
    "largest": ("the largest shape", "the biggest of the shapes"),
    "second_largest": ("the second largest shape", "the second biggest of the shapes"),
    "third_largest": ("the third largest shape", "the third biggest of the shapes"),
    "smallest": ("the smallest shape", "the tiniest of the shapes"),
}

# How to state the edit. `{target}` is filled from TARGET_PHRASES.
OPERATION_PHRASES: dict[str, tuple[str, str]] = {
    "recolor_fill": ("Change the fill of {target} to {fill}.", "Recolour {target} to {fill}."),
    "add_stroke": (
        "Add a {stroke_width}px {stroke} outline to {target}.",
        "Give {target} a {stroke_width}px {stroke} border.",
    ),
    "delete": ("Delete {target}.", "Remove {target} from the document."),
    "rotate": (
        "Rotate {target} by {degrees} degrees.",
        "Turn {target} {degrees} degrees clockwise.",
    ),
}

# Edit colours, deliberately far from every generator palette entry so a requested
# colour can never coincide with a fill already in the document. Verified per instruction
# rather than assumed.
EDIT_COLOURS: tuple[str, ...] = ("#ff0000", "#00ff00", "#0000ff", "#ff00ff")
STROKE_COLOURS: tuple[str, ...] = ("#000000", "#ffffff")
STROKE_WIDTHS: tuple[int, ...] = (3, 5)
ROTATION_DEGREES: tuple[int, ...] = (45, 90)


def template_id(predicate: str, operation: str, target_variant: int, operation_variant: int) -> str:
    """Stable identifier for one wording, so per-template variance is reportable."""
    return f"{predicate}.{operation}.t{target_variant}o{operation_variant}"


def render(
    predicate: str,
    operation: str,
    target_variant: int,
    operation_variant: int,
    params: dict[str, object],
) -> str:
    target = TARGET_PHRASES[predicate][target_variant]
    return OPERATION_PHRASES[operation][operation_variant].format(target=target, **params)
