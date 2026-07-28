"""Audit: the shipped corpus leaks nothing that identifies an element.

Supports claim C1. The unit tests run these invariants on a small corpus for speed;
this module runs them at the configured size, because the corpus that ships is the
one whose properties are claimed.

If any of these fail, the baseline arm stops being a valid manipulation check: a model
could beat the 1/K floor by exploiting the leak rather than by resolving a reference,
and the central comparison would lose its reference point.
"""

from __future__ import annotations

import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.generation import generate_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"
SVG_NS = "{http://www.w3.org/2000/svg}"

POSITIONAL_ATTRIBUTES = frozenset(
    {"transform", "x", "y", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2", "points"}
)

_PERMUTATIONS = 2000
_MIN_P_VALUE = 0.005
_PERMUTATION_SEED = 20260728


@pytest.fixture(scope="module")
def shipped_corpus():  # type: ignore[no-untyped-def]
    """The corpus at its configured size - 30 SVGs, exactly what will be frozen."""
    return generate_corpus(load_config(BASE).config)


def _midrank(values: list[float]) -> list[float]:
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


def _pooled_rho(groups: list[list[float]]) -> float:
    positions: list[float] = []
    values: list[float] = []
    for group in groups:
        positions.extend(float(i) for i in range(len(group)))
        values.extend(group)
    rx, ry = _midrank(positions), _midrank(values)
    n = len(positions)
    mean_x, mean_y = sum(rx) / n, sum(ry) / n
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry, strict=True))
    var_x = sum((a - mean_x) ** 2 for a in rx) ** 0.5
    var_y = sum((b - mean_y) ** 2 for b in ry) ** 0.5
    return 0.0 if var_x == 0 or var_y == 0 else cov / (var_x * var_y)


def _permutation_p(groups: list[list[float]]) -> float:
    """Empirical p-value. See tests/unit/test_generation.py for why not an analytic z:
    under a provably uniform shuffle the analytic statistic has mean +0.88, not 0."""
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
    return (extreme + 1) / (_PERMUTATIONS + 1)


def _rank_groups(corpus, sort_key: str, attribute: str) -> list[list[float]]:  # type: ignore[no-untyped-def]
    groups: list[list[float]] = []
    for sample in corpus:
        members = sample.ambiguity_elements
        by_attribute = sorted(members, key=lambda e: getattr(e, attribute))
        attribute_rank = {e.element_id: i for i, e in enumerate(by_attribute)}
        ordered = sorted(members, key=lambda e: getattr(e, sort_key))
        groups.append([float(attribute_rank[e.element_id]) for e in ordered])
    return groups


@pytest.mark.audit
@pytest.mark.parametrize("sort_key", ["document_index", "element_id", "geometry_token"])
@pytest.mark.parametrize("attribute", ["area", "center_x", "center_y"])
def test_no_visible_ordering_predicts_geometry(shipped_corpus, sort_key, attribute) -> None:  # type: ignore[no-untyped-def]
    """Every ordering a model can see must be uninformative about every property an
    instruction can refer to."""
    p_value = _permutation_p(_rank_groups(shipped_corpus, sort_key, attribute))
    assert p_value >= _MIN_P_VALUE, (
        f"{sort_key} predicts {attribute} in the shipped corpus (p={p_value:.4f})"
    )


@pytest.mark.audit
def test_no_positional_attributes_in_the_shipped_corpus(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """A single `transform` would put position back in plain sight.

    The easiest way to invalidate the whole benchmark, so it is checked rather than
    trusted to code review.
    """
    for sample in shipped_corpus:
        root = ET.fromstring(sample.model_visible_svg)
        for element in root.iter():
            if element.tag == f"{SVG_NS}svg":
                continue
            offending = POSITIONAL_ATTRIBUTES & set(element.attrib)
            assert not offending, f"{sample.svg_id}: {sorted(offending)}"


@pytest.mark.audit
def test_geometry_tokens_are_uniform_length_in_the_shipped_corpus(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """Variable-length tokens would leak path complexity - which correlates with size -
    through byte count alone."""
    lengths = {
        len(element.get("d", ""))
        for sample in shipped_corpus
        for element in ET.fromstring(sample.model_visible_svg).iter()
        if element.tag == f"{SVG_NS}path"
    }
    assert len(lengths) == 1, f"token lengths vary: {sorted(lengths)}"


@pytest.mark.audit
def test_ambiguity_sets_are_indistinguishable_in_markup(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """The defining property of C1: within an ambiguity set, every model-visible
    attribute except the opaque identifiers is identical."""
    for sample in shipped_corpus:
        member_ids = {e.element_id for e in sample.ambiguity_elements}
        signatures = set()
        for element in ET.fromstring(sample.model_visible_svg).iter():
            if element.get("id") in member_ids:
                signatures.add(
                    (element.tag, tuple(sorted(k for k in element.attrib)), element.get("fill"))
                )
        assert len(signatures) == 1, f"{sample.svg_id}: members differ in markup {signatures}"


@pytest.mark.audit
def test_no_real_coordinates_survive_redaction(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """No decimal number survives on any shape.

    Scoped to element attributes rather than raw text: the XML declaration carries
    `version="1.0"`, which is not a coordinate. Canvas dimensions on the root are
    integers, identical across every sample, and therefore carry no per-element
    information.
    """
    for sample in shipped_corpus:
        for element in ET.fromstring(sample.model_visible_svg).iter():
            if element.tag == f"{SVG_NS}svg":
                continue
            for name, value in element.attrib.items():
                if name == "d":
                    continue
                assert not re.search(r"\d+\.\d+", value), f"{sample.svg_id}: {name}={value}"


@pytest.mark.audit
def test_corpus_is_deterministic_at_shipped_size(shipped_corpus) -> None:  # type: ignore[no-untyped-def]
    """The precondition for content-addressing the dataset (C6)."""
    again = generate_corpus(load_config(BASE).config)
    assert [s.resolved_svg for s in again] == [s.resolved_svg for s in shipped_corpus]
