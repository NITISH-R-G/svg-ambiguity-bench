"""Loading and layering.

Three sources, resolved in order: base -> experiment -> explicit override. No
environment-variable layer and no implicit discovery, because a value that arrives
from an unrecorded source is an untracked experimental variable.

Every override is returned alongside the config so it can be written into the run
manifest. An override that is applied but not recorded is exactly the failure mode
Biderman et al. 2024 document as the leading cause of irreproducible LLM results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from svgbench.config.schema import Config


class ConfigError(ValueError):
    """Raised when a configuration cannot be resolved into a valid `Config`.

    Wraps pydantic and YAML failures so callers depend on this package's contract
    rather than on the validation library in use.
    """


class LoadedConfig(BaseModel):
    """A resolved config plus the provenance needed to reproduce it."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    config: Config
    sources: tuple[str, ...]
    overrides: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config file {path}: {exc}") from exc
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    return loaded


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge nested mappings; replace anything else wholesale.

    Lists are replaced rather than concatenated. Concatenation would make a config's
    effective value depend on the layer beneath it in a way that is invisible when
    reading the file.
    """
    merged = dict(base)
    for key, value in overlay.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def _expand_dotted(key: str, value: Any) -> dict[str, Any]:
    """Turn `generation.n_svgs` into `{"generation": {"n_svgs": ...}}`."""
    parts = [part for part in key.split(".") if part]
    if not parts:
        raise ConfigError(f"invalid override key: {key!r}")
    nested: dict[str, Any] = {parts[-1]: value}
    for part in reversed(parts[:-1]):
        nested = {part: nested}
    return nested


def load_config(
    base_path: Path,
    experiment_path: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> LoadedConfig:
    """Resolve a configuration from its layers.

    Args:
        base_path: `configs/base.yaml`, which must fully specify an experiment on its
            own. If it did not, the missing values would come from somewhere
            unrecorded and the hash would not describe the run.
        experiment_path: an optional overlay naming one experiment, conventionally
            differing from base only in the manipulated variable.
        overrides: explicit dotted-key overrides, recorded in the result.

    Raises:
        ConfigError: if any layer is unreadable, contains an unknown key, or the
            resolved result fails validation.
    """
    merged = _read_yaml(base_path)
    sources = [str(base_path)]

    if experiment_path is not None:
        merged = _deep_merge(merged, _read_yaml(experiment_path))
        sources.append(str(experiment_path))

    applied = dict(overrides or {})
    for key, value in applied.items():
        merged = _deep_merge(merged, _expand_dotted(key, value))

    try:
        config = Config.model_validate(merged)
    except ValidationError as exc:
        raise ConfigError(f"invalid configuration from {' + '.join(sources)}:\n{exc}") from exc

    return LoadedConfig(config=config, sources=tuple(sources), overrides=applied)
