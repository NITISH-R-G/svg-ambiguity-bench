"""Corpus generation.

Supports claim C1: the corpus is genuinely under-determined. Every invariant enforced
here is one a reviewer would otherwise have to take on trust.

Seeding is hierarchical and *positional*: a sample's seed derives from its index, not
from a running counter. Regenerating sample 17 alone therefore reproduces it exactly,
and a change in early rejection sampling cannot cascade and reshuffle every later
sample. Without that property, one regeneration invalidates the whole corpus.
"""

from __future__ import annotations

import hashlib
import random

from svgbench.config import Config
from svgbench.generation.document import geometry_token, render_document
from svgbench.generation.records import ElementIntent, SVGSample
from svgbench.generation.shapes import (
    PlacementError,
    make_blob,
    place_without_overlap,
    target_areas,
)

# Fill palette. The ambiguity set takes one colour; distractors take others. Colours
# are written in a single notation so that fill strings never differ cosmetically
# between elements that are meant to be identical.
_AMBIGUITY_FILLS = ("#3b6ea5", "#4a7c59", "#8c5a3c", "#6b4c8a", "#a34a4a")
_DISTRACTOR_FILLS = ("#d9b310", "#2f2f2f", "#c0c0c0", "#e07b39", "#7a9e9f")

# Smallest ambiguity-set area, in square user units. Chosen so that the largest member
# of a K=7 set still leaves room for non-overlapping placement on the default canvas.
_BASE_AREA_RANGE = (1100.0, 1900.0)
_DISTRACTOR_AREA_RANGE = (900.0, 3200.0)


def _derive_seed(root_seed: int, *path: object) -> int:
    """Positional seed derivation.

    A hash of the path rather than a counter, so seeds depend on *where* a sample is
    rather than on how many samples preceded it.
    """
    key = f"{root_seed}:" + ":".join(str(part) for part in path)
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


def _digest(*parts: object) -> str:
    key = ":".join(str(part) for part in parts)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]


def generate_sample(config: Config, index: int) -> SVGSample:
    """Generate one sample, retrying placement failures with fresh attempt seeds.

    Retries are bounded and exhausting them raises. Silently relaxing the separation
    requirement would produce a corpus that quietly violates its own guarantees.
    """
    generation = config.generation
    svg_id = f"svg_{_digest(config.seed, 'id', index)}"
    last_failure: PlacementError | None = None

    for attempt in range(1, generation.max_regen_attempts + 1):
        sample_seed = _derive_seed(config.seed, "svg", index, "attempt", attempt)
        try:
            return _build_sample(config, index, svg_id, sample_seed, attempt)
        except PlacementError as exc:
            last_failure = exc

    raise RuntimeError(
        f"{svg_id}: placement failed after {generation.max_regen_attempts} attempts "
        f"({last_failure}). Loosen generation.min_area_ratio or enlarge the canvas "
        f"rather than reducing the separation requirement."
    )


def _build_sample(
    config: Config,
    index: int,
    svg_id: str,
    sample_seed: int,
    attempt: int,
) -> SVGSample:
    generation = config.generation
    rng = random.Random(sample_seed)

    k = rng.randint(generation.ambiguity_min, generation.ambiguity_max)
    n_distractors = rng.randint(generation.distractor_min, generation.distractor_max)

    shared_fill = rng.choice(_AMBIGUITY_FILLS)
    distractor_palette = [fill for fill in _DISTRACTOR_FILLS if fill != shared_fill]

    # Ambiguity areas are constructed to be separated, so the ordinal predicates have
    # an uncontested ordering. Distractor areas are unconstrained - they are never
    # ranking targets, and constraining them would needlessly crowd the canvas.
    ambiguity_areas = target_areas(
        rng,
        count=k,
        min_ratio=generation.min_area_ratio,
        base=rng.uniform(*_BASE_AREA_RANGE),
    )
    distractor_areas = [rng.uniform(*_DISTRACTOR_AREA_RANGE) for _ in range(n_distractors)]

    # Radius needed before a centre is known, so blobs are built twice: once at the
    # origin to learn their extent, then again at the chosen centre. Cheap, and it
    # keeps placement independent of shape synthesis.
    provisional = [
        make_blob(random.Random(_derive_seed(sample_seed, "shape", i)), area, (0.0, 0.0))
        for i, area in enumerate(ambiguity_areas + distractor_areas)
    ]
    centers = place_without_overlap(
        rng,
        radii=[blob.bounding_radius for blob in provisional],
        canvas_size=generation.canvas_size,
    )

    roles = ["ambiguity"] * k + ["distractor"] * n_distractors
    fills = [shared_fill] * k + [
        distractor_palette[i % len(distractor_palette)] for i in range(n_distractors)
    ]

    built = [
        make_blob(random.Random(_derive_seed(sample_seed, "shape", i)), area, centers[i])
        for i, area in enumerate(ambiguity_areas + distractor_areas)
    ]

    # Document order is shuffled independently of every geometric property, so that a
    # model which always edits the first candidate scores at the 1/K floor rather than
    # above it. Without this the baseline arm would not establish C1.
    order = list(range(len(built)))
    random.Random(_derive_seed(sample_seed, "order")).shuffle(order)

    elements: list[ElementIntent] = []
    shapes: list[tuple[str, str, str]] = []
    token_to_path: dict[str, str] = {}

    for document_index, source_index in enumerate(order):
        blob = built[source_index]
        # Identifiers derive from the shape's pre-shuffle index, so neither id nor
        # token can be sorted back into document, positional, or size order.
        element_id = f"e{_digest(sample_seed, 'element', source_index)}"
        token = geometry_token(_digest(sample_seed, "token", source_index))
        path_data = blob.to_path_data()
        token_to_path[token] = path_data

        elements.append(
            ElementIntent(
                element_id=element_id,
                geometry_token=token,
                role=roles[source_index],  # type: ignore[arg-type]
                fill=fills[source_index],
                document_index=document_index,
                placement_x=blob.placement_x,
                placement_y=blob.placement_y,
                area=blob.area,
                bounding_radius=blob.bounding_radius,
            )
        )
        shapes.append((element_id, path_data, fills[source_index]))

    resolved_svg = render_document(generation.canvas_size, shapes)

    if generation.redact_geometry:
        redacted = [
            (element_id, token_to_path_key(token_to_path, path_data), fill)
            for element_id, path_data, fill in shapes
        ]
        model_visible_svg = render_document(generation.canvas_size, redacted)
    else:
        # The `legible` control corpus: real geometry, everything else identical.
        model_visible_svg = resolved_svg

    return SVGSample(
        svg_id=svg_id,
        sample_index=index,
        sample_seed=sample_seed,
        attempts=attempt,
        shared_fill=shared_fill,
        canvas_size=generation.canvas_size,
        elements=tuple(elements),
        resolved_svg=resolved_svg,
        model_visible_svg=model_visible_svg,
        token_to_path=token_to_path,
    )


def token_to_path_key(token_to_path: dict[str, str], path_data: str) -> str:
    """Invert the token map. Raises if a path has no token, rather than emitting one."""
    for token, data in token_to_path.items():
        if data == path_data:
            return token
    raise KeyError("path data has no assigned geometry token")


def generate_corpus(config: Config) -> list[SVGSample]:
    """Generate the full corpus. Deterministic given `config.seed`."""
    return [generate_sample(config, index) for index in range(config.generation.n_svgs)]
