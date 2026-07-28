"""Ground-truth engine tests.

Supports C7 (ground truth is correct) and C8 (ground truth matches human judgement).

The question driving these is not "what would falsify the measurement" - Step 4 answered
that - but "what would make two reasonable humans disagree". Those are different
failures. A sample can be measured perfectly and still have no answer a person would
confidently give, and shipping such a sample measures the benchmark's arbitrariness
rather than the model's ability.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from svgbench.config import load_config
from svgbench.generation import generate_corpus
from svgbench.groundtruth import REGISTRY, build_corpus_ground_truth, build_ground_truth

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "configs" / "base.yaml"


@pytest.fixture(scope="module")
def config():  # type: ignore[no-untyped-def]
    return load_config(BASE, overrides={"generation.n_svgs": 10}).config


@pytest.fixture(scope="module")
def corpus(config):  # type: ignore[no-untyped-def]
    return generate_corpus(config)


@pytest.fixture(scope="module")
def truths(corpus, config):  # type: ignore[no-untyped-def]
    return build_corpus_ground_truth(corpus, config)


# ---------------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------------


def test_every_configured_predicate_is_registered(config) -> None:  # type: ignore[no-untyped-def]
    configured = set(config.instructions.spatial_predicates) | set(
        config.instructions.ordinal_predicates
    )
    assert configured <= set(REGISTRY), f"unregistered: {configured - set(REGISTRY)}"


def test_spatial_predicates_carry_alternative_definitions() -> None:
    """C8 rests on there being more than one reasonable reading to compare against.

    A spatial predicate with a single scorer cannot detect definition disagreement, so
    it would silently ship humanly-contested cases.
    """
    for name, spec in REGISTRY.items():
        if spec.family == "SPATIAL":
            assert len(spec.scorers) >= 2, f"{name} has no alternative reading to check"


def test_corner_predicates_require_a_quadrant() -> None:
    """Nearest-corner alone can crown a shape near the middle of the canvas."""
    for name in ("top_left", "top_right", "bottom_left", "bottom_right"):
        assert REGISTRY[name].required_quadrant is not None


# ---------------------------------------------------------------------------
# C8 - the construct-validity gate
# ---------------------------------------------------------------------------


def test_valid_predicates_agree_under_every_reasonable_definition(truths, config) -> None:  # type: ignore[no-untyped-def]
    """The core C8 property, re-derived independently of the engine's own bookkeeping."""
    corpus_truths, _ = truths
    for truth in corpus_truths:
        for name in truth.valid_predicates:
            spec = REGISTRY[name]
            if spec.family != "SPATIAL":
                continue
            winners = {
                min(truth.ambiguity_ids, key=lambda i: scorer(truth.geometry[i], 512))
                for scorer in spec.scorers
            }
            assert winners == {truth.predicates[name].winner}, (
                f"{truth.svg_id}/{name}: definitions disagree but predicate was accepted"
            )


def test_engine_actually_refuses_some_predicates(truths) -> None:  # type: ignore[no-untyped-def]
    """A gate that never fires is decoration.

    Definition disagreement was measured at roughly 1 sample in 8 before this engine
    existed, so a corpus where nothing is refused means the check is not running.
    """
    _, tally = truths
    refused = sum(count for reason, count in tally.items() if ":" not in reason) - tally["valid"]
    assert refused > 0, f"no predicate was refused, tally={dict(tally)}"


def test_refusals_are_all_for_declared_reasons(truths) -> None:  # type: ignore[no-untyped-def]
    corpus_truths, _ = truths
    for truth in corpus_truths:
        for result in truth.predicates.values():
            if result.is_valid:
                assert result.invalid_reason is None
            else:
                assert result.invalid_reason is not None


def test_target_lookup_refuses_invalid_predicates(truths) -> None:  # type: ignore[no-untyped-def]
    """The answer key must not hand out an answer it does not believe in."""
    corpus_truths, _ = truths
    for truth in corpus_truths:
        for name, result in truth.predicates.items():
            if result.is_valid:
                assert truth.target_of(name) == result.winner
            else:
                with pytest.raises(KeyError, match=name):
                    truth.target_of(name)


# ---------------------------------------------------------------------------
# Uniqueness and margins
# ---------------------------------------------------------------------------


def test_valid_spatial_targets_beat_every_distractor(truths, config) -> None:  # type: ignore[no-untyped-def]
    """Uniqueness is asserted over the FULL element set, not just the ambiguity set.

    A distractor winning the predicate would make the instruction ambiguous to a person,
    and a model picking the distractor would be marked wrong while arguably being right.
    """
    corpus_truths, _ = truths
    for truth in corpus_truths:
        outsiders = [i for i in truth.geometry if i not in truth.ambiguity_ids]
        for name in truth.valid_predicates:
            spec = REGISTRY[name]
            if spec.family != "SPATIAL":
                continue
            primary = spec.scorers[0]
            winner_score = primary(truth.geometry[truth.predicates[name].winner], 512)
            for other in outsiders:
                assert primary(truth.geometry[other], 512) >= winner_score, (
                    f"{truth.svg_id}/{name}: distractor {other} outranks the target"
                )


def test_valid_ordinal_targets_clear_the_area_margin(truths, config) -> None:  # type: ignore[no-untyped-def]
    corpus_truths, _ = truths
    for truth in corpus_truths:
        for name in truth.valid_predicates:
            result = truth.predicates[name]
            if result.family == "ORDINAL_SIZE":
                assert result.margin >= config.generation.min_area_ratio


def test_valid_spatial_targets_clear_the_spatial_margin(truths, config) -> None:  # type: ignore[no-untyped-def]
    corpus_truths, _ = truths
    for truth in corpus_truths:
        for name in truth.valid_predicates:
            result = truth.predicates[name]
            if result.family == "SPATIAL":
                assert result.margin >= config.generation.min_spatial_margin


def test_ordinal_ranks_pick_the_right_element(truths) -> None:  # type: ignore[no-untyped-def]
    """`second_largest` must genuinely be second by canonical area."""
    corpus_truths, _ = truths
    for truth in corpus_truths:
        by_area = sorted(truth.ambiguity_ids, key=lambda i: truth.geometry[i].area, reverse=True)
        for name, expected_index in (
            ("largest", 0),
            ("second_largest", 1),
            ("third_largest", 2),
            ("smallest", len(by_area) - 1),
        ):
            if name in truth.valid_predicates:
                assert truth.predicates[name].winner == by_area[expected_index]


# ---------------------------------------------------------------------------
# Every sample must still be usable
# ---------------------------------------------------------------------------


def test_every_sample_can_host_both_families(truths) -> None:  # type: ignore[no-untyped-def]
    """Each cluster must contribute to both family estimates.

    The SVG is the unit of statistical resampling (ADR-0007), so a sample supplying only
    one family would contribute to one arm of the family comparison and not the other.
    """
    corpus_truths, _ = truths
    for truth in corpus_truths:
        families = {truth.predicates[n].family for n in truth.valid_predicates}
        assert "SPATIAL" in families, f"{truth.svg_id}: no valid spatial predicate"
        assert "ORDINAL_SIZE" in families, f"{truth.svg_id}: no valid ordinal predicate"


def test_corpus_supplies_enough_predicates_for_the_instruction_budget(truths, config) -> None:  # type: ignore[no-untyped-def]
    """The check that a per-SVG-minimum test would miss.

    An earlier `min_spatial_margin` of 0.15 left 13 of 30 SVGs unable to supply three
    spatial predicates, while every sample still had at least one - so a
    "both families present" test passed while the corpus could not actually be built.
    Availability is a CORPUS-level property and has to be asserted as one.
    """
    corpus_truths, _ = truths
    needed_per_family = config.instructions.instructions_per_svg // 2
    demand = needed_per_family * len(corpus_truths)

    for family in ("SPATIAL", "ORDINAL_SIZE"):
        supply = sum(
            1
            for truth in corpus_truths
            for name in truth.valid_predicates
            if truth.predicates[name].family == family
        )
        assert supply >= demand, (
            f"{family}: corpus supplies {supply} valid predicate slots but the "
            f"instruction budget needs {demand}"
        )


def test_predicate_availability_is_uneven_across_samples(truths) -> None:  # type: ignore[no-untyped-def]
    """Documents a constraint that Step 7 inherits rather than one this step fixes.

    Spatial availability varies per SVG because `definition_disagreement` and
    `distractor_outranks_target` are validity requirements, not tunable thresholds - no
    margin setting makes them go away. Instruction allocation must therefore adapt to
    what each sample can host, balancing at the corpus level rather than assuming a
    fixed split within every SVG.

    Asserted so the constraint is discovered here, in a test, rather than as a puzzling
    failure inside the instruction generator.
    """
    corpus_truths, _ = truths
    spatial_counts = {
        truth.svg_id: sum(
            1 for n in truth.valid_predicates if truth.predicates[n].family == "SPATIAL"
        )
        for truth in corpus_truths
    }
    assert len(set(spatial_counts.values())) > 1, (
        "spatial availability is uniform, so Step 7 could assume a fixed split - "
        "verify this is really true before relying on it"
    )


def test_ground_truth_is_deterministic(corpus, config) -> None:  # type: ignore[no-untyped-def]
    first = build_ground_truth(corpus[0], config)
    second = build_ground_truth(corpus[0], config)
    assert first.valid_predicates == second.valid_predicates
    assert {n: r.winner for n, r in first.predicates.items()} == {
        n: r.winner for n, r in second.predicates.items()
    }
