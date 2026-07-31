"""Tests for the extracted, domain-independent control.

`fmtcontrol` must not know anything about SVG. These tests use retrieval-shaped and
tool-shaped data on purpose - if a change makes the package depend on this repository's
domain, something here should fail.
"""

from __future__ import annotations

import pytest

from fmtcontrol import check_control, permute


def test_preserves_entities_order_and_value_multiset() -> None:
    facts = {"doc_1": ("Paris", 2.1), "doc_2": ("Berlin", 3.4), "doc_3": ("Rome", 0.7)}
    out = permute(facts, key="q1", seed=991)

    assert list(out) == list(facts), "row order must be held fixed"
    assert sorted(out.values()) == sorted(facts.values()), "information content changed"
    assert out != facts, "mapping was not destroyed"


def test_input_is_not_mutated() -> None:
    facts = {"a": 1, "b": 2, "c": 3}
    before = dict(facts)
    permute(facts, key="k", seed=1)
    assert facts == before


def test_deterministic_per_key_and_independent_across_keys() -> None:
    facts = {f"e{i}": i for i in range(8)}
    assert permute(facts, key="x", seed=7) == permute(facts, key="x", seed=7)
    assert permute(facts, key="x", seed=7) != permute(facts, key="y", seed=7)
    assert permute(facts, key="x", seed=7) != permute(facts, key="x", seed=8)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 8, 16])
def test_never_returns_the_identity(n: int) -> None:
    """The failure this guards against is silent: an identity permutation makes the
    control arm a second treatment arm, and no downstream test would notice."""
    facts = {f"e{i}": (i * 1.5, i * 2.5) for i in range(n)}
    for trial in range(200):
        out = permute(facts, key=f"item-{trial}", seed=13)
        assert any(out[e] != facts[e] for e in facts), f"identity permutation at n={n}"


def test_single_entity_is_rejected_rather_than_silently_passed() -> None:
    """One row cannot be format-matched: permuting it changes nothing, so returning it
    unchanged would hand back an invalid control that looks valid."""
    with pytest.raises(ValueError, match="fewer than two entities"):
        permute({"only": 1}, key="k", seed=1)


def test_all_values_equal_is_rejected() -> None:
    """No permutation of identical values displaces anything, so no control exists."""
    with pytest.raises(ValueError, match="no displacing permutation"):
        permute({"a": 5, "b": 5, "c": 5}, key="k", seed=1)


def test_values_may_be_unhashable() -> None:
    """Facts are often records. Requiring hashability would exclude the common case."""
    facts = {"a": ["x", 1], "b": ["y", 2], "c": ["z", 3]}
    out = permute(facts, key="k", seed=1)
    assert sorted(map(str, out.values())) == sorted(map(str, facts.values()))


class TestCheckControl:
    def _render(self, mapping: dict[str, tuple[str, float]]) -> str:
        return "\n".join(f"{k:<8} {v[0]:<8} {v[1]:6.2f}" for k, v in mapping.items())

    def test_accepts_a_valid_control(self) -> None:
        facts = {"d1": ("Paris", 2.1), "d2": ("Berlin", 3.4), "d3": ("Rome", 0.7)}
        permuted = permute(facts, key="q", seed=991)
        report = check_control(facts, permuted, self._render(facts), self._render(permuted))
        assert report.ok, report.failures
        assert report.token_delta == 0

    def test_rejects_identity(self) -> None:
        facts = {"a": 1, "b": 2}
        report = check_control(facts, dict(facts))
        assert not report.ok
        assert any("identity" in f for f in report.failures)

    def test_rejects_altered_values(self) -> None:
        """The most damaging failure: values that were changed rather than only moved."""
        facts = {"a": 1, "b": 2, "c": 3}
        report = check_control(facts, {"a": 99, "b": 1, "c": 2})
        assert not report.ok
        assert any("multiset" in f for f in report.failures)

    def test_rejects_reordered_entities(self) -> None:
        facts = {"a": 1, "b": 2, "c": 3}
        report = check_control(facts, {"c": 1, "b": 3, "a": 2})
        assert not report.ok
        assert any("order" in f for f in report.failures)

    def test_rejects_differing_token_counts(self) -> None:
        facts = {"a": ("x", 1.0), "b": ("y", 2.0)}
        permuted = permute(facts, key="k", seed=1)
        report = check_control(facts, permuted, "a x 1", "a x 1 with several extra words here")
        assert not report.ok
        assert any("token" in f for f in report.failures)

    def test_reports_when_format_checks_were_skipped(self) -> None:
        """Silence about a check that did not run is how a control quietly degrades."""
        facts = {"a": 1, "b": 2, "c": 3}
        report = check_control(facts, permute(facts, key="k", seed=1))
        assert report.ok
        assert any("skipped" in n for n in report.notes)
        assert report.token_delta is None


def test_package_does_not_import_the_benchmark() -> None:
    """`fmtcontrol` is the transferable part. A dependency on svgbench would make the
    domain-independence claim false, and the import would be easy to add by accident."""
    import fmtcontrol.control

    source = __import__("pathlib").Path(fmtcontrol.control.__file__).read_text(encoding="utf-8")
    assert "svgbench" not in source
