"""Configuration system tests.

These encode the two properties the experiment's validity rests on:

1. A parameter that can influence a result is in the config hash. Anything else is
   an untracked variable (Biderman et al., 2024 - "Lessons from the Trenches on
   Reproducible Evaluation of Language Models").
2. Corpus identity depends ONLY on seed + generation + instructions. If it depended
   on model or context settings, each arm would silently get its own corpus and the
   paired comparison in ADR-0007 would be invalid.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from svgbench.config import (
    Config,
    ConfigError,
    config_hash,
    corpus_config_hash,
    load_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGS = REPO_ROOT / "configs"
BASE = CONFIGS / "base.yaml"
EXPERIMENTS = CONFIGS / "experiments"


# ---------------------------------------------------------------------------
# Loading and layering
# ---------------------------------------------------------------------------


def test_base_config_is_complete_and_valid() -> None:
    """base.yaml alone must fully specify an experiment.

    Not a convenience property. If base.yaml were incomplete, the missing values
    would come from somewhere unrecorded, and the hash would not describe the run.
    """
    loaded = load_config(BASE)
    assert isinstance(loaded.config, Config)
    assert loaded.overrides == {}


@pytest.mark.parametrize(
    "experiment",
    sorted(p.name for p in EXPERIMENTS.glob("*.yaml")),
)
def test_every_shipped_experiment_loads(experiment: str) -> None:
    loaded = load_config(BASE, EXPERIMENTS / experiment)
    assert loaded.config.experiment_id


def test_experiment_layer_overrides_base() -> None:
    base_only = load_config(BASE).config
    enhanced = load_config(BASE, EXPERIMENTS / "main-enhanced.yaml").config
    assert base_only.context.provider != enhanced.context.provider
    assert enhanced.context.provider == "enhanced"


def test_explicit_override_wins_over_experiment(tmp_path: Path) -> None:
    loaded = load_config(
        BASE,
        EXPERIMENTS / "main-baseline.yaml",
        overrides={"generation.n_svgs": 3},
    )
    assert loaded.config.generation.n_svgs == 3
    assert loaded.overrides == {"generation.n_svgs": 3}


def test_overrides_are_recorded_in_provenance() -> None:
    """An unrecorded override is an untracked experimental variable."""
    loaded = load_config(BASE, overrides={"model.temperature": 0.7})
    assert loaded.overrides["model.temperature"] == 0.7
    assert loaded.config.model.temperature == 0.7


def test_sources_are_recorded_in_order() -> None:
    loaded = load_config(BASE, EXPERIMENTS / "main-enhanced.yaml")
    assert [Path(s).name for s in loaded.sources] == ["base.yaml", "main-enhanced.yaml"]


# ---------------------------------------------------------------------------
# Validation - the config must refuse to be wrong
# ---------------------------------------------------------------------------


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    """A typo'd key must fail loudly, not be silently ignored.

    Silent acceptance is how a parameter someone believed they set ends up not set.
    """
    bad = tmp_path / "bad.yaml"
    bad.write_text("generation:\n  n_svgz: 10\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="n_svgz"):
        load_config(BASE, bad)


def test_missing_required_section_is_rejected(tmp_path: Path) -> None:
    partial = tmp_path / "partial.yaml"
    partial.write_text(
        yaml.safe_dump({"schema_version": "1.0", "experiment_id": "x", "seed": 1}),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(partial)


def test_out_of_range_value_is_rejected() -> None:
    with pytest.raises(ConfigError):
        load_config(BASE, overrides={"generation.ambiguity_min": 1})


def test_inverted_ambiguity_range_is_rejected() -> None:
    with pytest.raises(ConfigError, match="ambiguity"):
        load_config(BASE, overrides={"generation.ambiguity_min": 7, "generation.ambiguity_max": 4})


def test_ordinal_predicates_must_fit_the_smallest_ambiguity_set() -> None:
    """`third_largest` is unanswerable if an ambiguity set can have fewer than 3 members.

    Caught at config load rather than at generation, because a corpus that cannot
    support its own instructions is a design error, not a runtime accident.
    """
    with pytest.raises(ConfigError, match="third_largest"):
        load_config(BASE, overrides={"generation.ambiguity_min": 2, "generation.ambiguity_max": 2})


def test_unknown_predicate_name_is_rejected() -> None:
    with pytest.raises(ConfigError):
        load_config(BASE, overrides={"instructions.spatial_predicates": ["middle_ish"]})


def test_config_is_immutable() -> None:
    """Frozen so nothing can mutate a value after it has been hashed."""
    cfg = load_config(BASE).config
    with pytest.raises(ValidationError, match="frozen"):
        cfg.generation.n_svgs = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Hashing - identity of an experiment
# ---------------------------------------------------------------------------


def test_hash_is_invariant_to_key_order(tmp_path: Path) -> None:
    """Two configs differing only in key order describe the same experiment."""
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("experiment_id: x\nseed: 7\n", encoding="utf-8")
    b.write_text("seed: 7\nexperiment_id: x\n", encoding="utf-8")
    assert config_hash(load_config(BASE, a).config) == config_hash(load_config(BASE, b).config)


def test_hash_excludes_experiment_id() -> None:
    """The label is not a parameter.

    Keeps the property that identical parameters produce an identical hash, which is
    what lets the arm-fairness audit detect drift.
    """
    base = load_config(BASE, overrides={"experiment_id": "alpha"}).config
    other = load_config(BASE, overrides={"experiment_id": "beta"}).config
    assert config_hash(base) == config_hash(other)


def test_hash_changes_when_any_result_affecting_value_changes() -> None:
    reference = config_hash(load_config(BASE).config)
    for key, value in [
        ("seed", 999),
        ("generation.n_svgs", 7),
        ("instructions.instructions_per_svg", 2),
        ("model.temperature", 0.9),
        ("model.name", "some-other-model"),
        ("prompt.template_version", "9.9"),
        ("context.provider", "enhanced"),
        ("evaluation.replicates", 5),
        ("metrics.bootstrap_seed", 4321),
    ]:
        changed = config_hash(load_config(BASE, overrides={key: value}).config)
        assert changed != reference, f"{key} does not affect the config hash"


def test_defaults_are_materialised_into_the_hash() -> None:
    """A default that is not in the dump is not in the hash, and the hash would lie."""
    dumped = load_config(BASE).config.model_dump(mode="json")
    assert dumped["metrics"]["cluster_unit"] == "svg"
    assert "numeric_tolerance" in dumped["evaluation"]


def test_hash_round_trips_through_serialisation() -> None:
    original = load_config(BASE).config
    revived = Config.model_validate(original.model_dump(mode="json"))
    assert config_hash(revived) == config_hash(original)


# ---------------------------------------------------------------------------
# Corpus identity - the property the paired comparison depends on
# ---------------------------------------------------------------------------


def test_corpus_hash_ignores_everything_downstream_of_the_dataset() -> None:
    """Every arm must load the same corpus.

    If model, prompt, context or metrics settings changed corpus identity, each arm
    would silently generate its own dataset and the paired test would be invalid.
    """
    reference = corpus_config_hash(load_config(BASE).config)
    for key, value in [
        ("model.name", "another-model"),
        ("model.temperature", 0.5),
        ("prompt.template_version", "2.0"),
        ("context.provider", "permuted"),
        ("evaluation.replicates", 9),
        ("metrics.bootstrap_iterations", 123),
        ("experiment_id", "unrelated"),
    ]:
        assert corpus_config_hash(load_config(BASE, overrides={key: value}).config) == reference, (
            f"{key} must not change corpus identity"
        )


def test_corpus_hash_changes_with_corpus_defining_values() -> None:
    reference = corpus_config_hash(load_config(BASE).config)
    for key, value in [
        ("seed", 424242),
        ("generation.n_svgs", 11),
        ("generation.ambiguity_max", 6),
        ("generation.redact_geometry", False),
        ("instructions.instructions_per_svg", 4),
        ("instructions.operations", ["recolor_fill"]),
    ]:
        assert corpus_config_hash(load_config(BASE, overrides={key: value}).config) != reference, (
            f"{key} must change corpus identity"
        )


def test_all_main_arms_share_one_corpus() -> None:
    """The central claim is a paired comparison. Pairing requires identical cases."""
    arms = sorted(EXPERIMENTS.glob("main-*.yaml"))
    assert len(arms) >= 3, "expected at least baseline, permuted and enhanced"
    hashes = {p.name: corpus_config_hash(load_config(BASE, p).config) for p in arms}
    assert len(set(hashes.values())) == 1, f"arms disagree on corpus: {hashes}"
