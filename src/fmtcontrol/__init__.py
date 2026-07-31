"""Format-matched controls for context-augmentation experiments.

Adding context to a prompt changes two things at once: the **information** it carries and
the **format** it arrives in. Comparing augmented against unaugmented cannot separate
them, so a measured improvement is equally consistent with "the facts helped" and "a
table helped".

The control is a third arm that is format-identical and information-destroyed: the same
rows, fields, widths and token count, with the values permuted between entities so the
entity-to-fact mapping is broken and nothing else is.

    enhanced - baseline    total effect
    permuted - baseline    format component
    enhanced - permuted    information component   <- the claim people actually make

This package is domain-independent. It knows nothing about SVG, retrieval, tools or
memory. It permutes a mapping and checks that the result is a valid control.

Usage::

    from fmtcontrol import permute, check_control

    facts = {"doc_1": ("Paris", 2.1), "doc_2": ("Berlin", 3.4)}

    permuted = permute(facts, key="query_42", seed=991)

    enhanced_text = my_renderer(facts)      # the SAME renderer for both arms -
    permuted_text = my_renderer(permuted)   # otherwise format is not held fixed

    report = check_control(facts, permuted, enhanced_text, permuted_text)
    assert report.ok, report.failures

Why the caller renders rather than the package: a renderer that lives here would have to
guess your format, and an arm rendered by different code from its treatment is not a
format-matched control. Passing the mapping back keeps the single-renderer requirement
where the caller can see it.
"""

from fmtcontrol.control import ControlReport, check_control, permute

__all__ = ["ControlReport", "check_control", "permute"]
__version__ = "0.1.0"
