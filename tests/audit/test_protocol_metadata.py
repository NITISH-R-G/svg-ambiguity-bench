"""`protocol.json` must describe the repository it ships with.

It exists so a machine - a results file, a downstream harness, a reviewer's script - can
read the protocol identity without parsing prose. That is only worth having if it cannot
quietly go stale, and this repository has already shipped three stale duplicates of facts
that lived in more than one place.

So every field here is checked against the artefact it claims to describe rather than
against a second copy of itself.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = REPO_ROOT / "protocol.json"

pytestmark = pytest.mark.audit


def _protocol() -> dict:  # type: ignore[type-arg]
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def _frozen_manifest() -> dict:  # type: ignore[type-arg]
    roots = [p for p in (REPO_ROOT / "data" / "frozen").iterdir() if p.is_dir()]
    assert roots, "no frozen dataset"
    return json.loads((roots[0] / "manifest.json").read_text(encoding="utf-8"))


def test_protocol_is_valid_json_with_required_sections() -> None:
    protocol = _protocol()
    for section in (
        "protocol_version",
        "instrument",
        "prompt",
        "scoring",
        "fmtcontrol",
        "studies",
        "open",
    ):
        assert section in protocol, f"protocol.json is missing {section!r}"


@pytest.mark.parametrize("field", ["dataset_hash", "config_hash", "corpus_config_hash", "seed"])
def test_instrument_fields_match_the_frozen_manifest(field: str) -> None:
    """The manifest is the artefact; protocol.json only reports it."""
    assert _protocol()["instrument"][field] == _frozen_manifest()[field], (
        f"protocol.json {field!r} disagrees with the frozen manifest. One of them is stale."
    )


def test_dataset_hash_matches_the_directory_it_names() -> None:
    """The frozen directory is named for its own content hash, so this is a real check."""
    roots = [p.name for p in (REPO_ROOT / "data" / "frozen").iterdir() if p.is_dir()]
    assert _protocol()["instrument"]["dataset_hash"] in roots


def test_prompt_version_matches_the_code() -> None:
    from svgbench.runner.prompt import TEMPLATE_ID, TEMPLATE_VERSION

    prompt = _protocol()["prompt"]
    assert prompt["template_id"] == TEMPLATE_ID
    assert prompt["template_version"] == TEMPLATE_VERSION


def test_fmtcontrol_versions_match_the_package_and_vectors() -> None:
    import fmtcontrol

    declared = _protocol()["fmtcontrol"]
    assert declared["version"] == fmtcontrol.__version__

    vectors = json.loads(
        (REPO_ROOT / "src" / "fmtcontrol" / "conformance_vectors.json").read_text(encoding="utf-8")
    )
    assert declared["spec_version"] == vectors["spec_version"]


def test_abstention_rule_version_matches_the_config() -> None:
    from svgbench.config import load_config

    config = load_config(REPO_ROOT / "configs" / "base.yaml").config
    assert (
        _protocol()["scoring"]["abstention_rule_version"]
        == config.evaluation.abstention_rule_version
    )


def test_known_defects_are_declared_while_unresolved() -> None:
    """FA-013 is live. A protocol advertising a scoring version without its known defect
    would be the most misleading field in the file."""
    defects = _protocol()["scoring"].get("known_defects", [])
    assert any(d["id"] == "FA-013" for d in defects), (
        "FA-013 is unresolved and must stay declared until a revised abstention rule ships"
    )


def test_every_study_points_at_files_that_exist() -> None:
    for study in _protocol()["studies"]:
        for key in ("preregistration", "results"):
            assert (REPO_ROOT / study[key]).exists(), f"{study['id']}: missing {study[key]}"


def test_open_counters_are_honest() -> None:
    """These are the numbers a reader checks first. They must not be aspirational."""
    open_items = _protocol()["open"]
    assert open_items["central_claim_exercised"] is False, (
        "If the control has now fired, this flag, TRUST.md and LIMITATIONS 14 all change "
        "together - and only after a study whose pre-registration says so."
    )
    assert open_items["independent_implementations"] == 0
    assert open_items["independent_replications"] == 0


def test_toolchain_record_exists_and_pins_python() -> None:
    record = (REPO_ROOT / "scripts" / "toolchain.txt").read_text(encoding="utf-8")
    assert record.startswith("#")
    assert "python 3.12" in record, "the toolchain record must state the Python version"
    for tool in ("ruff==", "mypy==", "pytest=="):
        assert tool in record, f"toolchain record does not pin {tool}"
