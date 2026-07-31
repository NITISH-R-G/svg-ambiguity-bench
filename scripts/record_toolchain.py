"""Record the resolved toolchain the published results were produced under.

`pyproject.toml` holds the *constraints*. This records what those constraints actually
resolved to, so someone rerunning this in 2029 does not have to guess which `ruff`
reformatted the source or which `numpy` did the arithmetic. A range is a promise about
the future; this is a statement about the past.

Prompted by a concrete failure: `ruff>=0.6,<1` silently permitted a version whose
formatter reaches into Python blocks inside markdown, and CI went red on every push for
a week. The constraint was satisfied the whole time.

Usage:
    python scripts/record_toolchain.py
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "scripts" / "toolchain.txt"

# Distribution names as pip reports them. `resvg-py` installs as `resvg_py`; looking it
# up under the hyphenated name silently reported "not installed" while the module
# imported fine - a reminder that an absent record and an absent package look identical.
PACKAGES = (
    "ruff",
    "mypy",
    "pytest",
    "pytest-cov",
    "matplotlib",
    "types-PyYAML",
    "pydantic",
    "PyYAML",
    "numpy",
    "svgelements",
    "resvg_py",
    "pillow",
    "httpx",
)


def _installed() -> dict[str, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        line.split("==")[0].lower().replace("-", "_"): line
        for line in result.stdout.splitlines()
        if "==" in line
    }


def main() -> int:
    have = _installed()
    missing = [name for name in PACKAGES if name.lower().replace("-", "_") not in have]

    lines = [
        "# Resolved toolchain for the environment the published results were produced in,",
        "# and which CI is verified green against.",
        "#",
        "# Regenerate: python scripts/record_toolchain.py",
        "#",
        "# This is a RECORD, not a constraint. pyproject.toml holds the constraints.",
        "",
        f"python {platform.python_version()}  ({platform.python_implementation()})",
        f"platform {platform.system()} {platform.release()} {platform.machine()}",
        "",
        "# CI additionally runs ubuntu-latest and windows-latest on python 3.12.",
        "",
    ]
    for name in PACKAGES:
        lines.append(have.get(name.lower().replace("-", "_"), f"# {name}: NOT INSTALLED"))

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO_ROOT)}")
    if missing:
        print(f"  note: not installed in this environment: {missing}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
