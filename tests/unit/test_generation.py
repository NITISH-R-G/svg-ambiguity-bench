"""Generator tests.

These support claim C1: the corpus is genuinely under-determined - the markup cannot
distinguish the candidate elements.

C1 is what makes the baseline arm a valid manipulation check. If any of these fail,
baseline failure could be caused by something other than the missing information, and
the central comparison loses its reference point.
"""

from __future__ import annotations

import itertools
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.generation import generate_corpus, generate_sample

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"

SVG_NS = "{http://www.w3.org/2000/svg}"

# Any of these on a shape would put position back into readable markup and destroy C1.
POSITIONAL_ATTRIBUTES = frozenset(
    {
        "transform",
        "x",
        "y",
        "cx",
        "cy",
        "r",
        "rx",
        "ry",
        "x1",
        "y1",
        "x2",
        "y2",
        "points",
        "width",
        "height",
        "offset",
    }
)

TOKEN_PATTERN = re.compile(r"^\{\{GEOM_[0-9a-f]{8}\}\}$")


@pytest.fixture(scope="module")
def config():  # type: ignore[no-untyped-def]
    # Small corpus keeps the suite fast; invariants are size-independent.
    return load_config(BASE, overrides={"generation.n_svgs": 6}).config


@pytest.fixture(scope="module")
def corpus(config):  # type: ignore[no-untyped-def]
    return generate_corpus(config)


def _shapes(svg_text: str) -> list[ET.Element]:
    root = ET.fromstring(svg_text)
    return [el for el in root.iter() if el.tag == f"{SVG_NS}path"]


# ---------------------------------------------------------------------------
# Determinism - the precondition for every reproducibility claim (C6)
# ---------------------------------------------------------------------------


def test_same_seed_produces_byte_identical_corpus(config) -> None:  # type: ignore[no-untyped-def]
    first = generate_corpus(config)
    second = generate_corpus(config)
    assert [s.model_visible_svg for s in first] == [s.model_visible_svg for s in second]
    assert [s.resolved_svg for s in first] == [s.resolved_svg for s in second]


def test_different_seed_produces_a_different_corpus(config) -> None:  # type: ignore[no-untyped-def]
    other = load_config(BASE, overrides={"generation.n_svgs": 6, "seed": 999}).config
    assert generate_corpus(config)[0].resolved_svg != generate_corpus(other)[0].resolved_svg


def test_sample_seeds_are_positional_not_sequential(config, corpus) -> None:  # type: ignore[no-untyped-def]
    """Regenerating one sample alone must reproduce it exactly.

    Seeds derive from the sample's index rather than from a running counter, so a
    change in early rejection sampling cannot cascade and reshuffle every later
    sample. Without this, one regeneration invalidates the whole corpus.
    """
    for index in (0, 3, 5):
        assert generate_sample(config, index).resolved_svg == corpus[index].resolved_svg


# ---------------------------------------------------------------------------
# C1: the ambiguity set is genuinely indistinguishable in markup
# ---------------------------------------------------------------------------


def test_ambiguity_set_size_is_within_configured_range(config, corpus) -> None:  # type: ignore[no-untyped-def]
    for sample in corpus:
        assert config.generation.ambiguity_min <= sample.k <= config.generation.ambiguity_max


def test_distractor_count_is_within_configured_range(config, corpus) -> None:  # type: ignore[no-untyped-def]
    for sample in corpus:
        n = len(sample.distractor_elements)
        assert config.generation.distractor_min <= n <= config.generation.distractor_max


def test_ambiguity_members_share_tag_and_fill(corpus) -> None:  # type: ignore[no-untyped-def]
    """The defining property. If they differed, the markup would distinguish them."""
    for sample in corpus:
        fills = {e.fill for e in sample.ambiguity_elements}
        assert fills == {sample.shared_fill}, f"{sample.svg_id}: fills differ {fills}"

        by_id = {e.element_id: e for e in sample.ambiguity_elements}
        tags = {el.tag for el in _shapes(sample.model_visible_svg) if el.get("id") in by_id}
        assert tags == {f"{SVG_NS}path"}, f"{sample.svg_id}: tags differ {tags}"


def test_distractors_are_distinguishable_by_fill(corpus) -> None:  # type: ignore[no-untyped-def]
    """Distractors exist so the scene is not uniformly one kind of thing."""
    for sample in corpus:
        for element in sample.distractor_elements:
            assert element.fill != sample.shared_fill


def test_ambiguity_members_carry_no_semantic_hints(corpus) -> None:  # type: ignore[no-untyped-def]
    """No class, label, title or aria text that could name an element."""
    forbidden = {"class", "aria-label", "data-name", "label", "title", "name"}
    for sample in corpus:
        for el in _shapes(sample.model_visible_svg):
            assert not (forbidden & set(el.attrib)), f"{sample.svg_id}: {el.attrib}"


# ---------------------------------------------------------------------------
# Redaction integrity
# ---------------------------------------------------------------------------


def test_every_geometry_token_is_well_formed_and_fixed_length(corpus) -> None:  # type: ignore[no-untyped-def]
    lengths = set()
    for sample in corpus:
        for el in _shapes(sample.model_visible_svg):
            d = el.get("d", "")
            assert TOKEN_PATTERN.match(d), f"{sample.svg_id}: unexpected d={d!r}"
            lengths.add(len(d))
    assert len(lengths) == 1, f"token lengths vary: {lengths}"


def test_tokens_are_unique_within_a_document(corpus) -> None:  # type: ignore[no-untyped-def]
    """The token is the primary scoring identity anchor, so collisions would break
    alignment as well as leak that two elements are related."""
    for sample in corpus:
        tokens = [el.get("d") for el in _shapes(sample.model_visible_svg)]
        assert len(set(tokens)) == len(tokens)


def test_element_ids_are_opaque_and_fixed_length(corpus) -> None:  # type: ignore[no-untyped-def]
    lengths = set()
    for sample in corpus:
        ids = [el.get("id", "") for el in _shapes(sample.model_visible_svg)]
        assert len(set(ids)) == len(ids)
        for element_id in ids:
            assert re.match(r"^e[0-9a-f]{8}$", element_id), element_id
            lengths.add(len(element_id))
    assert len(lengths) == 1


def test_model_visible_svg_contains_no_coordinates(corpus) -> None:  # type: ignore[no-untyped-def]
    """The strongest form of C1: no numeric geometry survives anywhere in the document
    the model sees, apart from the canvas dimensions."""
    for sample in corpus:
        root = ET.fromstring(sample.model_visible_svg)
        for el in root.iter():
            if el.tag == f"{SVG_NS}svg":
                continue
            for name, value in el.attrib.items():
                assert name not in POSITIONAL_ATTRIBUTES, f"{sample.svg_id}: {name}"
                if name != "d":
                    assert not re.search(r"\d+\.\d+", value), f"{sample.svg_id}: {name}={value}"


def test_token_to_path_map_is_absent_from_model_visible_svg(corpus) -> None:  # type: ignore[no-untyped-def]
    for sample in corpus:
        for path_data in sample.token_to_path.values():
            assert path_data not in sample.model_visible_svg


def test_redaction_is_structure_preserving(corpus) -> None:  # type: ignore[no-untyped-def]
    """Redaction must remove geometry and change nothing else.

    Compared with `d` masked on both sides: same elements, same order, same attributes.
    Anything else differing would mean redaction introduced a second, unmeasured change.
    """
    for sample in corpus:

        def skeleton(svg_text: str) -> list[tuple[str, tuple[tuple[str, str], ...]]]:
            root = ET.fromstring(svg_text)
            return [
                (
                    el.tag,
                    tuple(sorted((k, "<masked>" if k == "d" else v) for k, v in el.attrib.items())),
                )
                for el in root.iter()
            ]

        assert skeleton(sample.resolved_svg) == skeleton(sample.model_visible_svg)


def test_legible_mode_keeps_real_geometry(config) -> None:  # type: ignore[no-untyped-def]
    """The `legible` control corpus isolates ambiguity from unfamiliar markup."""
    legible = load_config(
        BASE,
        overrides={"generation.n_svgs": 2, "generation.redact_geometry": False},
    ).config
    for sample in generate_corpus(legible):
        assert sample.model_visible_svg == sample.resolved_svg
        assert not TOKEN_PATTERN.match(_shapes(sample.model_visible_svg)[0].get("d", ""))


# ---------------------------------------------------------------------------
# Document order must carry no signal
# ---------------------------------------------------------------------------


def _spearman(xs: list[float], ys: list[float]) -> float:
    def rank(values: list[float]) -> list[float]:
        """Midranks: tied values share their average rank.

        Ordinal ranks with stable tie-breaking would be wrong here and not merely
        imprecise. The pooled data is almost entirely ties - positions run 0..K-1 once
        per SVG, and so do the ranked attributes - so a stable sort resolves every tie
        by append order. Both vectors are appended in the same SVG order, which
        manufactures correlation out of nothing. Using ordinal ranks produced a mean
        z of +1.6 across 25 seeds against a true value of 0.
        """
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        start = 0
        while start < len(order):
            end = start
            while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
                end += 1
            shared = (start + end) / 2.0
            for position in range(start, end + 1):
                ranks[order[position]] = shared
            start = end + 1
        return ranks

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mean_x, mean_y = sum(rx) / n, sum(ry) / n
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry, strict=True))
    var_x = sum((a - mean_x) ** 2 for a in rx) ** 0.5
    var_y = sum((b - mean_y) ** 2 for b in ry) ** 0.5
    return 0.0 if var_x == 0 or var_y == 0 else cov / (var_x * var_y)


# The null distribution is built by permutation rather than from a formula.
#
# The obvious analytic route - rho * sqrt(n - 1), compared against a normal - is wrong
# here, and measurably so. Under a shuffle that is uniform BY CONSTRUCTION, that
# statistic has mean +0.88 rather than 0. The cause is structural: positions and
# attribute ranks both run 0..K-1 within an SVG, so pooling across SVGs with different
# K induces an association from group size alone, and the formula cannot see it.
# Trusting it would have meant reporting a generator leak that does not exist.
#
# Permuting the within-SVG assignment handles ties, unequal group sizes and pooling
# exactly, with no distributional assumption. It is also the same instrument the main
# analysis commits to for the same reason (ADR-0007).
_PERMUTATIONS = 2000
_MIN_P_VALUE = 0.005
_PERMUTATION_SEED = 20260728


def _pooled_rho(groups: list[list[float]]) -> float:
    """Spearman over positions vs attribute ranks, pooled across SVGs."""
    positions: list[float] = []
    values: list[float] = []
    for group in groups:
        positions.extend(float(i) for i in range(len(group)))
        values.extend(group)
    return _spearman(positions, values)


def _assert_no_association(groups: list[list[float]], label: str) -> None:
    """Fail if the observed association is extreme against its own permutation null.

    `groups[i][p]` is the attribute rank of the element at position `p` within SVG `i`.
    """
    observed = abs(_pooled_rho(groups))
    rng = random.Random(_PERMUTATION_SEED)

    extreme = 0
    for _ in range(_PERMUTATIONS):
        shuffled = []
        for group in groups:
            copy = list(group)
            rng.shuffle(copy)
            shuffled.append(copy)
        if abs(_pooled_rho(shuffled)) >= observed:
            extreme += 1

    p_value = (extreme + 1) / (_PERMUTATIONS + 1)
    assert p_value >= _MIN_P_VALUE, (
        f"{label}: rho={_pooled_rho(groups):+.3f}, permutation p={p_value:.4f} "
        f"(< {_MIN_P_VALUE}) over {len(groups)} SVGs"
    )


def _rank_groups(corpus, sort_key: str, attribute: str) -> list[list[float]]:  # type: ignore[no-untyped-def]
    """For each SVG, the `attribute` rank of the element at each `sort_key` position.

    Both variables are ranked WITHIN an SVG. Pooling raw areas would let between-SVG
    scale differences (areas span roughly 1e3 to 3e4 across the corpus) dominate the
    ranking, while positions only ever range over one ambiguity set.
    """
    groups: list[list[float]] = []
    for sample in corpus:
        members = sample.ambiguity_elements
        by_attribute = sorted(members, key=lambda e: getattr(e, attribute))
        attribute_rank = {e.element_id: i for i, e in enumerate(by_attribute)}
        ordered = sorted(members, key=lambda e: getattr(e, sort_key))
        groups.append([float(attribute_rank[e.element_id]) for e in ordered])
    return groups


@pytest.mark.parametrize("attribute", ["area", "placement_x", "placement_y"])
def test_document_order_does_not_predict_geometry(corpus, attribute: str) -> None:  # type: ignore[no-untyped-def]
    """A model that always edits the first candidate must score at chance, not above it.

    If document order correlated with position or size, such a policy would beat the
    1/K floor for a reason unrelated to reference resolution, and the baseline arm
    would no longer establish C1.
    """
    _assert_no_association(
        _rank_groups(corpus, "document_index", attribute),
        f"document order predicts {attribute}",
    )


@pytest.mark.parametrize("sort_key", ["element_id", "geometry_token"])
@pytest.mark.parametrize("attribute", ["area", "placement_x", "placement_y"])
def test_identifiers_do_not_sort_into_geometric_order(
    corpus, sort_key: str, attribute: str
) -> None:  # type: ignore[no-untyped-def]
    """Ids and tokens are visible in the markup and therefore sortable by a model.

    Both are hashes of a pre-shuffle index that *does* correlate with area by
    construction, so the hash is load-bearing here rather than incidental. Verified
    rather than assumed.
    """
    _assert_no_association(
        _rank_groups(corpus, sort_key, attribute),
        f"{sort_key} order predicts {attribute}",
    )


def test_the_leak_detector_actually_detects_a_leak(corpus) -> None:  # type: ignore[no-untyped-def]
    """A test that cannot fail is decoration.

    Plants perfect document-order-equals-area-order and requires the permutation test
    to reject it.
    """
    planted = [sorted(group) for group in _rank_groups(corpus, "document_index", "area")]
    with pytest.raises(AssertionError, match="permutation p"):
        _assert_no_association(planted, "planted leak")


# ---------------------------------------------------------------------------
# Geometric properties the instruction families depend on
# ---------------------------------------------------------------------------


def test_ambiguity_areas_are_separated_enough_to_rank(config, corpus) -> None:  # type: ignore[no-untyped-def]
    """Ordinal predicates need an uncontested ordering.

    Checked against generator intent here; verified independently against rendered
    geometry at step 5, which is what makes it ground truth rather than a belief.
    """
    for sample in corpus:
        areas = sorted((e.area for e in sample.ambiguity_elements), reverse=True)
        for larger, smaller in itertools.pairwise(areas):
            assert larger / smaller >= config.generation.min_area_ratio, (
                f"{sample.svg_id}: adjacent areas {larger:.1f}/{smaller:.1f} too close"
            )


def test_shapes_do_not_overlap(corpus) -> None:  # type: ignore[no-untyped-def]
    """Occlusion would corrupt rendered area and make ordinal ground truth wrong."""
    for sample in corpus:
        elements = sample.ambiguity_elements + sample.distractor_elements
        for i, a in enumerate(elements):
            for b in elements[i + 1 :]:
                distance = (
                    (a.placement_x - b.placement_x) ** 2 + (a.placement_y - b.placement_y) ** 2
                ) ** 0.5
                assert distance > a.bounding_radius + b.bounding_radius, (
                    f"{sample.svg_id}: {a.element_id} overlaps {b.element_id}"
                )


def test_shapes_stay_inside_the_canvas(config, corpus) -> None:  # type: ignore[no-untyped-def]
    """A clipped shape would render with a smaller area than its geometry implies."""
    size = config.generation.canvas_size
    for sample in corpus:
        for element in sample.ambiguity_elements + sample.distractor_elements:
            assert element.placement_x - element.bounding_radius >= 0
            assert element.placement_y - element.bounding_radius >= 0
            assert element.placement_x + element.bounding_radius <= size
            assert element.placement_y + element.bounding_radius <= size


# ---------------------------------------------------------------------------
# The documents must actually be documents
# ---------------------------------------------------------------------------


def test_both_variants_parse_as_xml(corpus) -> None:  # type: ignore[no-untyped-def]
    for sample in corpus:
        ET.fromstring(sample.resolved_svg)
        ET.fromstring(sample.model_visible_svg)


def test_resolved_svg_renders(corpus) -> None:  # type: ignore[no-untyped-def]
    """Ground truth is measured from the render, so an unrenderable corpus has none."""
    import resvg_py

    png = resvg_py.svg_to_bytes(svg_string=corpus[0].resolved_svg)
    assert len(bytes(png)) > 0
