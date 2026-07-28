"""Configuration schema, layering (base -> experiment -> CLI override), validation
and canonical hashing.

The resolved config's hash is the identity of an experiment. Anything that can
influence a result must be represented here: a value that lives as an implicit
default inside code is not in the hash, and the hash would then be a lie.
"""

from svgbench.config.hashing import canonical_json, config_hash, corpus_config_hash
from svgbench.config.loader import ConfigError, LoadedConfig, load_config
from svgbench.config.schema import (
    SCHEMA_VERSION,
    Config,
    ContextConfig,
    EvaluationConfig,
    GenerationConfig,
    InstructionConfig,
    MetricsConfig,
    ModelConfig,
    Operation,
    OrdinalPredicate,
    PromptConfig,
    SpatialPredicate,
)

__all__ = [
    "SCHEMA_VERSION",
    "Config",
    "ConfigError",
    "ContextConfig",
    "EvaluationConfig",
    "GenerationConfig",
    "InstructionConfig",
    "LoadedConfig",
    "MetricsConfig",
    "ModelConfig",
    "Operation",
    "OrdinalPredicate",
    "PromptConfig",
    "SpatialPredicate",
    "canonical_json",
    "config_hash",
    "corpus_config_hash",
    "load_config",
]
