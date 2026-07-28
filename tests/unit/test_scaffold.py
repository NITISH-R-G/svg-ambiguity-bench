"""Scaffold tests.

These are deliberately structural rather than behavioural - there is no behaviour yet.
Their job is to make the architecture enforceable from the first commit, so that the
layering documented in `docs/01-architecture.md` cannot quietly rot as modules land.
"""

from __future__ import annotations

import ast
import importlib
import tomllib
from pathlib import Path

import pytest

import svgbench
from svgbench.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_ROOT = REPO_ROOT / "src" / "svgbench"

# Dependency order, which is NOT the same as data-flow order. `geometry` is a leaf
# measurement utility with no internal dependencies, so it sits first even though data
# flows generation -> geometry. A module may import from its own layer or any earlier
# one, never a later one.
LAYERS: tuple[str, ...] = (
    "geometry",
    "generation",
    "groundtruth",
    "instructions",
    "dataset",
    "context",
    "runner",
    "evaluation",
    "metrics",
    "reporting",
)

# `config` is depended on by everything and depends on nothing in the pipeline.
# `audit` deliberately inspects every stage. `cli` wires everything together.
EXEMPT: frozenset[str] = frozenset({"config", "audit", "cli"})


def test_version_is_single_sourced() -> None:
    """The package version and the packaging metadata must not drift apart."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == svgbench.__version__


@pytest.mark.parametrize("name", [*LAYERS, *sorted(EXEMPT - {"cli"})])
def test_subpackage_is_importable(name: str) -> None:
    """Every architectural component exists as a real, importable package."""
    module = importlib.import_module(f"svgbench.{name}")
    assert module.__doc__, f"svgbench.{name} must document what it is responsible for"


def test_status_command_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "No experiments have been run" in out


def test_unimplemented_command_fails_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    """A step that is not built yet must say so, not raise."""
    assert main(["generate"]) == 2
    assert "not implemented yet" in capsys.readouterr().err


def test_bare_invocation_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def _layer_of(path: Path) -> str | None:
    rel = path.relative_to(PKG_ROOT)
    return rel.parts[0] if len(rel.parts) > 1 else None


def _imported_layers(source: str) -> set[str]:
    """Return the svgbench subpackages a source file imports from."""
    found: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] == "svgbench" and len(parts) > 1:
                found.add(parts[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "svgbench" and len(parts) > 1:
                    found.add(parts[1])
    return found


def test_pipeline_layering_is_one_directional() -> None:
    """No module may import from a stage that comes after it.

    This is the architectural invariant that keeps the pipeline honest: if evaluation
    could reach back into generation, a scoring rule could come to depend on how a
    sample was made, and arm-blind scoring would no longer be structurally guaranteed.
    """
    violations: list[str] = []
    for py_file in PKG_ROOT.rglob("*.py"):
        layer = _layer_of(py_file)
        if layer is None or layer in EXEMPT:
            continue
        if layer not in LAYERS:
            violations.append(f"{py_file.name}: unknown layer {layer!r}")
            continue
        own_index = LAYERS.index(layer)
        for imported in _imported_layers(py_file.read_text(encoding="utf-8")):
            if imported in EXEMPT or imported == layer:
                continue
            if imported not in LAYERS:
                violations.append(f"{layer}: imports unknown layer {imported!r}")
            elif LAYERS.index(imported) > own_index:
                violations.append(
                    f"{layer} imports downstream layer {imported!r} "
                    f"({py_file.relative_to(REPO_ROOT)})"
                )
    assert not violations, "Layering violations:\n  " + "\n  ".join(violations)


def test_evaluation_never_imports_a_renderer() -> None:
    """Scoring must be reproducible without an SVG toolchain.

    Tier-1 and Tier-2 reproduction promise that a reviewer with no renderer and no model
    can re-derive every published number. That promise is only credible if the scoring
    path cannot rasterise.
    """
    forbidden = {"resvg_py", "PIL", "svgelements"}
    offenders: list[str] = []
    for stage in ("evaluation", "metrics", "reporting"):
        for py_file in (PKG_ROOT / stage).rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if name in forbidden:
                        offenders.append(f"{py_file.relative_to(REPO_ROOT)} imports {name}")
    assert not offenders, "Renderer reached scoring path:\n  " + "\n  ".join(offenders)
