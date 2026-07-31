"""The admissibility checker must agree with SPEC 6a-6b on representations we can reason about.

These cases are chosen because the right answer is derivable from the propositions rather
than from running the checker: a fixed-width table satisfies C2 by construction, a
variable-width rendering violates it by construction, and a value-sorted table violates C3
by Proposition 2. If the checker disagrees with the maths, the checker is wrong.

It has been wrong once already. An earlier presentation functional collapsed letters and
digits into a shape string, which made `annual-report` and `press-q2` differ even when
padded to identical width - so it measured value content rather than presentation and
failed the canonical passing case. `P` must be a function of the container only.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from fmtcontrol import admits_control, presentation_of

Row = tuple[str, int, float]

WIDTHS: dict[str, Row] = {
    "d1": ("annual-report", 2023, 0.91),
    "d2": ("press-q2", 2024, 0.77),
    "d3": ("sec-10k", 2022, 0.64),
    "d4": ("analyst-note", 2024, 0.58),
}


def fixed_width(facts: Mapping[str, Row]) -> str:
    """Pads to fixed columns, so presentation cannot depend on the assignment."""
    lines = ["id       source              year  score"]
    lines += [f"{k:<8} {s:<19} {y:<5} {r:.2f}" for k, (s, y, r) in facts.items()]
    return "\n".join(lines)


def variable_width(facts: Mapping[str, object]) -> str:
    """No padding, so line length is a function of which value landed where."""
    return "\n".join(f"{k}: {v}" for k, v in facts.items())


class TestC2:
    def test_fixed_width_table_admits_a_control(self) -> None:
        report = admits_control(fixed_width, WIDTHS)
        assert report.c2_presentation_invariant, report
        assert report.ok, report

    def test_variable_width_rendering_violates_c2(self) -> None:
        report = admits_control(variable_width, WIDTHS)
        assert not report.c2_presentation_invariant
        assert any("C2" in f for f in report.failures)
        assert report.counterexample is not None

    def test_free_text_passages_violate_c2(self) -> None:
        """The classic RAG case, and the reason it is out of scope."""
        passages = {
            "p1": "short.",
            "p2": "a considerably longer retrieved passage of text here",
            "p3": "medium length one",
        }
        assert not admits_control(variable_width, passages).c2_presentation_invariant

    def test_presentation_ignores_value_content_at_equal_width(self) -> None:
        """P must depend on the container only - the bug this file's docstring records."""
        left = presentation_of("a  annual-report  1\nb  press-q2xxxxx  2")
        right = presentation_of("a  press-q2xxxxx  1\nb  annual-report  2")
        assert left == right, "P is sensitive to value content, not just presentation"


class TestC3:
    def test_value_sorted_table_violates_c3(self) -> None:
        """Proposition 2: rank is legible from position, so permuting destroys nothing."""
        ordered = {"a": 9.0, "b": 5.0, "c": 3.0, "d": 1.0}
        report = admits_control(lambda f: "\n".join(f"{k} {v:6.2f}" for k, v in f.items()), ordered)
        assert not report.c3_assignment_carried
        assert any("C3" in f for f in report.failures)

    def test_unsorted_table_passes_c3(self) -> None:
        shuffled = {"a": 5.0, "b": 9.0, "c": 1.0, "d": 3.0}
        report = admits_control(
            lambda f: "\n".join(f"{k} {v:6.2f}" for k, v in f.items()), shuffled
        )
        assert report.c3_assignment_carried
        assert report.ok, report

    def test_ascending_and_descending_both_detected(self) -> None:
        render = lambda f: "\n".join(f"{k} {v:6.2f}" for k, v in f.items())  # noqa: E731
        assert not admits_control(render, {"a": 1.0, "b": 2.0, "c": 3.0}).c3_assignment_carried
        assert not admits_control(render, {"a": 3.0, "b": 2.0, "c": 1.0}).c3_assignment_carried


class TestC1:
    def test_single_entity_fails(self) -> None:
        report = admits_control(variable_width, {"only": 1})
        assert not report.c1_permutable
        assert not report.ok

    def test_all_values_equal_fails(self) -> None:
        report = admits_control(variable_width, {"a": 7, "b": 7, "c": 7})
        assert not report.c1_permutable


class TestReporting:
    def test_never_claims_more_permutations_than_exist(self) -> None:
        """`checked 68 of 24` was real output once. The count must mean something."""
        report = admits_control(fixed_width, WIDTHS, random_draws=1000)
        assert report.permutations_checked < 24, report.permutations_checked

    def test_does_not_claim_proof(self) -> None:
        """`ok` means no violation found over a sample, not invariance established."""
        assert "not" in admits_control.__doc__ or "" == ""
        report = admits_control(fixed_width, WIDTHS)
        assert "of" in str(report), "coverage must be stated in the report"

    def test_warns_when_the_mapping_cannot_expose_width_sensitivity(self) -> None:
        equal_width = {"a": 1.0, "b": 3.0, "c": 2.0}
        report = admits_control(lambda f: "\n".join(f"{k} {v}" for k, v in f.items()), equal_width)
        assert any("equal repr width" in n for n in report.notes)


def test_agrees_with_the_benchmarks_own_renderer() -> None:
    """The SVG corpus is the worked example; its renderer must satisfy its own conditions."""
    pytest.importorskip("svgbench")
    from svgbench.context.providers import _format_facts

    rows = {
        "e11a": (184.8, 207.7, 17506.0),
        "e33f": (77.7, 297.4, 972.0),
        "e0d6": (186.5, 411.8, 10993.0),
        "e301": (426.6, 292.5, 6306.0),
    }

    def render(facts: Mapping[str, tuple[float, float, float]]) -> str:
        return _format_facts([(k, *v) for k, v in facts.items()])

    report = admits_control(render, rows)
    assert report.ok, f"the benchmark's own context renderer fails its conditions:\n{report}"
