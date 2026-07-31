"""The local check targets must run everything CI runs.

For a week, `make check` and `.\\tasks.ps1 check` ran lint, typecheck and test - but not
`ruff format --check`, which CI does run. Every push failed CI while the local signal was
green, and the README carried a red badge that nobody looked at because the local checks
said fine.

That is the FA-012 shape again: a verification surface that is silently narrower than the
one that actually gates. A convenience target which is a *subset* of CI is worse than no
target, because it manufactures false confidence.

These tests keep the three in sync by construction rather than by memory.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
MAKEFILE = REPO_ROOT / "Makefile"
TASKS_PS1 = REPO_ROOT / "tasks.ps1"

pytestmark = pytest.mark.audit

# The commands CI gates on. Keyed by a short name, valued by the distinguishing fragment
# that must appear in a local runner for that step to count as present.
CI_STEPS: dict[str, str] = {
    "lint": "ruff check .",
    "format-check": "ruff format --check .",
    "typecheck": "mypy",
    "test": "pytest",
    "audit": "pytest -m audit",
}


def test_workflow_exists_and_targets_the_default_branch() -> None:
    """A workflow that never triggers is indistinguishable from a passing one (FA-012)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "branches: [master]" in text, (
        "CI must trigger on the default branch. It once targeted `main` while the branch "
        "was `master`, so it never ran at all."
    )


@pytest.mark.parametrize("name", sorted(CI_STEPS))
def test_ci_still_runs_every_step_we_think_it_does(name: str) -> None:
    """Guards the guard: if CI drops a step, the local runners should not keep claiming it."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert CI_STEPS[name] in text, (
        f"CI no longer runs {name!r} ({CI_STEPS[name]!r}). Either restore it, or remove it "
        "from CI_STEPS and from the local check targets deliberately."
    )


def _makefile_check_body() -> str:
    """The recipe lines of the Makefile's `check` target, plus the targets it depends on."""
    text = MAKEFILE.read_text(encoding="utf-8")
    match = re.search(r"^check:([^\n]*)\n", text, re.MULTILINE)
    assert match, "no `check` target in the Makefile"
    dependencies = match.group(1).split("##")[0].split()

    body = []
    for dependency in dependencies:
        recipe = re.search(
            rf"^{re.escape(dependency)}:[^\n]*\n((?:\t[^\n]*\n)+)", text, re.MULTILINE
        )
        if recipe:
            body.append(recipe.group(1))
    return "\n".join(body)


@pytest.mark.parametrize("name", sorted(CI_STEPS))
def test_makefile_check_runs_every_ci_step(name: str) -> None:
    body = _makefile_check_body()
    assert CI_STEPS[name] in body, (
        f"`make check` does not run {name!r} ({CI_STEPS[name]!r}), but CI does. A local "
        "check that is a subset of CI produces false confidence - this exact gap let a "
        "week of red builds go unnoticed."
    )


def _tasks_check_body() -> str:
    text = TASKS_PS1.read_text(encoding="utf-8")
    match = re.search(r"'check'\s*\{(.*?)\n    \}", text, re.DOTALL)
    assert match, "no 'check' branch in tasks.ps1"
    return match.group(1)


@pytest.mark.parametrize("name", sorted(CI_STEPS))
def test_tasks_ps1_check_runs_every_ci_step(name: str) -> None:
    """Windows is the primary development platform here, so this is the one that matters."""
    body = _tasks_check_body()
    normalised = (
        body.replace("-m ruff", "ruff").replace("-m mypy", "mypy").replace("-m pytest", "pytest")
    )
    assert CI_STEPS[name] in normalised, (
        f"`.\\tasks.ps1 check` does not run {name!r} ({CI_STEPS[name]!r}), but CI does."
    )
