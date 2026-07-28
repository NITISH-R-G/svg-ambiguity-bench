"""The configuration schema.

Every value that can influence a result lives here. That is the whole design rule:
a parameter held anywhere else - a default buried in a function body, an environment
variable, a constant - is not in the config hash, and the hash would then not describe
the run that produced the numbers.

Validation is deliberately strict. Unknown keys are rejected rather than ignored,
because silent acceptance is how a parameter someone believed they had set ends up
unset. Models are frozen so nothing can be mutated after it has been hashed.

This module also owns the controlled vocabularies (predicate and operation names).
The predicate registry in `svgbench.instructions` imports them from here rather than
the reverse, which keeps `config` a dependency-free leaf and still catches a typo'd
predicate name at load time instead of at generation time.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0"

# Controlled vocabularies. Operational definitions live in docs/01-architecture.md §3.
SpatialPredicate = Literal[
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "leftmost",
    "rightmost",
    "topmost",
    "bottommost",
]
OrdinalPredicate = Literal["largest", "second_largest", "third_largest", "smallest"]
Operation = Literal["recolor_fill", "add_stroke", "delete", "rotate"]
ContextProvider = Literal["null", "permuted", "enhanced", "ceiling"]
Backend = Literal["ollama", "stub"]

# How many ambiguity-set members a predicate needs before it is answerable at all.
_MIN_MEMBERS_FOR_PREDICATE: dict[str, int] = {
    "second_largest": 2,
    "third_largest": 3,
}

_STRICT = ConfigDict(extra="forbid", frozen=True)


class GenerationConfig(BaseModel):
    """Corpus construction. Together with `seed` and `instructions`, defines the dataset."""

    model_config = _STRICT

    n_svgs: int = Field(ge=1, le=200)
    ambiguity_min: int = Field(ge=2, le=32)
    ambiguity_max: int = Field(ge=2, le=32)
    distractor_min: int = Field(ge=0, le=32)
    distractor_max: int = Field(ge=0, le=32)

    canvas_size: int = Field(ge=32, le=4096)
    raster_scale: int = Field(ge=1, le=8)

    # Separability guarantees (FR-2). These make the corpus easier than arbitrary
    # layouts by rejection sampling; the size of that bias is published via the
    # rejection log rather than hidden.
    min_area_ratio: float = Field(gt=1.0, le=10.0)
    min_spatial_margin: float = Field(gt=0.0, le=1.0)
    max_overlap_ratio: float = Field(ge=0.0, le=1.0)
    max_regen_attempts: int = Field(ge=1, le=10_000)

    # False produces the `legible` control corpus with real path data, isolating the
    # ambiguity effect from the out-of-distribution-markup effect (ADR-0002, ADR-0009).
    redact_geometry: bool

    @model_validator(mode="after")
    def _check_ranges(self) -> GenerationConfig:
        if self.ambiguity_min > self.ambiguity_max:
            raise ValueError(
                f"ambiguity_min ({self.ambiguity_min}) exceeds ambiguity_max ({self.ambiguity_max})"
            )
        if self.distractor_min > self.distractor_max:
            raise ValueError(
                f"distractor_min ({self.distractor_min}) exceeds "
                f"distractor_max ({self.distractor_max})"
            )
        return self


class InstructionConfig(BaseModel):
    """Instruction synthesis. Part of corpus identity."""

    model_config = _STRICT

    spatial_predicates: list[SpatialPredicate] = Field(min_length=1)
    ordinal_predicates: list[OrdinalPredicate] = Field(min_length=1)
    operations: list[Operation] = Field(min_length=1)
    instructions_per_svg: int = Field(ge=2, le=64)

    @model_validator(mode="after")
    def _no_duplicates(self) -> InstructionConfig:
        for field, values in (
            ("spatial_predicates", self.spatial_predicates),
            ("ordinal_predicates", self.ordinal_predicates),
            ("operations", self.operations),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{field} contains duplicates: {values}")
        return self


class PromptConfig(BaseModel):
    """The prompt is an experimental variable, so it is versioned and hashed.

    Biderman et al. 2024 identify undocumented prompt format as a leading cause of
    irreproducible evaluation results.
    """

    model_config = _STRICT

    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)


class ContextConfig(BaseModel):
    """The manipulated variable. This section is the only difference between arms."""

    model_config = _STRICT

    provider: ContextProvider
    # Permutation must be reproducible, and must not be derived from the corpus seed,
    # or the shuffle would correlate with the layout it is meant to be independent of.
    permutation_seed: int = Field(ge=0)


class ModelConfig(BaseModel):
    """Model identity and decoding. Recorded in full because quantisation and backend
    change outputs, so a model name alone is insufficient provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())

    name: str = Field(min_length=1)
    backend: Backend
    base_url: str = Field(min_length=1)
    temperature: float = Field(ge=0.0, le=2.0)
    top_p: float = Field(gt=0.0, le=1.0)
    seed: int | None
    max_output_tokens: int = Field(ge=1, le=1_000_000)
    context_limit: int = Field(ge=1, le=10_000_000)
    timeout_s: int = Field(ge=1, le=3600)


class EvaluationConfig(BaseModel):
    """Scoring rules. Frozen before the first model output is observed."""

    model_config = _STRICT

    replicates: int = Field(ge=1, le=32)
    numeric_tolerance: float = Field(gt=0.0, le=1.0)
    # Versioned so that any post-registration change to abstention detection is a
    # visible amendment rather than a silent edit (ADR-0008).
    abstention_rule_version: str = Field(min_length=1)


class MetricsConfig(BaseModel):
    """Inference settings.

    `cluster_unit` admits exactly one value on purpose: it is a declaration of a
    statistical claim - that instructions sharing an SVG are not independent - and it
    belongs somewhere a reviewer will see it rather than buried in an analysis script
    (ADR-0007).
    """

    model_config = _STRICT

    cluster_unit: Literal["svg"]
    bootstrap_iterations: int = Field(ge=100, le=1_000_000)
    bootstrap_seed: int = Field(ge=0)
    permutation_iterations: int = Field(ge=100, le=1_000_000)
    permutation_seed: int = Field(ge=0)
    ci_level: float = Field(gt=0.5, lt=1.0)


class Config(BaseModel):
    """A fully resolved experiment specification."""

    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())

    schema_version: str
    experiment_id: str = Field(min_length=1)
    seed: int = Field(ge=0)

    generation: GenerationConfig
    instructions: InstructionConfig
    prompt: PromptConfig
    context: ContextConfig
    model: ModelConfig
    evaluation: EvaluationConfig
    metrics: MetricsConfig

    @model_validator(mode="after")
    def _predicates_are_answerable(self) -> Config:
        """A corpus that cannot support its own instructions is a design error.

        `third_largest` is unanswerable if an ambiguity set may contain fewer than
        three members. Caught here rather than at generation time, where it would
        surface as an inexplicable rejection loop.
        """
        smallest_set = self.generation.ambiguity_min
        for predicate in self.instructions.ordinal_predicates:
            required = _MIN_MEMBERS_FOR_PREDICATE.get(predicate, 1)
            if required > smallest_set:
                raise ValueError(
                    f"predicate {predicate!r} needs at least {required} ambiguity-set "
                    f"members but ambiguity_min is {smallest_set}"
                )
        return self

    @model_validator(mode="after")
    def _schema_version_is_supported(self) -> Config:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {self.schema_version!r}; "
                f"this build understands {SCHEMA_VERSION!r}"
            )
        return self
