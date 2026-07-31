"""`fmtcontrol` must remain copy-and-paste adoptable.

The realistic first act of adoption is not `pip install`. It is a researcher copying two
files into their evaluation harness. That works today because the package imports nothing
outside the standard library — but nothing prevents a future edit from adding `numpy` for
one convenience, at which point vendoring silently stops being possible and the barrier to
adoption goes up without anyone noticing.

These tests fix that property in place. They also guard the direction that matters more:
the package must not acquire a dependency on the benchmark it was extracted from, or the
domain-independence claim becomes false.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "fmtcontrol"

# Everything `fmtcontrol` is allowed to import. Standard library only. Adding to this list
# is a decision to make the package harder to vendor, and should be argued for rather than
# done in passing.
ALLOWED_TOP_LEVEL = {
    "__future__",
    "collections",
    "dataclasses",
    "hashlib",
    "random",
    "typing",
    "fmtcontrol",
}

pytestmark = pytest.mark.audit


def _python_sources() -> list[Path]:
    return sorted(PACKAGE.glob("*.py"))


def _imported_top_level(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_there_is_something_to_check() -> None:
    assert _python_sources(), "no sources found; the path is probably wrong"


@pytest.mark.parametrize("path", _python_sources(), ids=lambda p: p.name)
def test_imports_only_the_standard_library(path: Path) -> None:
    """Vendoring by copy must keep working."""
    disallowed = _imported_top_level(path) - ALLOWED_TOP_LEVEL
    assert not disallowed, (
        f"{path.name} imports {sorted(disallowed)}, which is outside the standard library. "
        "That makes the package impossible to vendor by copying, which is how it is most "
        "likely to be adopted. Either drop the dependency or argue for widening "
        "ALLOWED_TOP_LEVEL."
    )


@pytest.mark.parametrize("path", _python_sources(), ids=lambda p: p.name)
def test_never_imports_the_benchmark(path: Path) -> None:
    """The domain-independence claim, asserted rather than trusted."""
    assert "svgbench" not in _imported_top_level(path), (
        f"{path.name} imports svgbench. The package is the transferable part; a "
        "dependency on the case study would make that claim false."
    )


def test_every_allowed_import_is_actually_standard_library() -> None:
    """Guards the guard: a typo in ALLOWED_TOP_LEVEL would silently permit anything."""
    for name in ALLOWED_TOP_LEVEL - {"__future__", "fmtcontrol"}:
        assert name in sys.stdlib_module_names, f"{name!r} is not a stdlib module"


def test_the_example_runs_without_the_benchmark_installed() -> None:
    """The 30-second demonstration must not quietly depend on the benchmark's stack."""
    example = Path(__file__).resolve().parents[2] / "examples" / "rag_style_control.py"
    assert example.exists(), "the runnable example is missing"

    imported = _imported_top_level(example)
    assert "svgbench" not in imported
    outside = imported - ALLOWED_TOP_LEVEL - {"pathlib", "sys"}
    assert not outside, f"the example needs {sorted(outside)}, so it is not dependency-free"
