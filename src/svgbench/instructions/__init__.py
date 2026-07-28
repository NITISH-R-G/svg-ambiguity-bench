"""Instruction synthesis, ground-truth resolution, and the leakage lint.

Resolution is performed by code against ground truth - never by a model and never
by hand. An instruction that does not resolve to exactly one element with
sufficient margin is not emitted.

Supports C1 (instruction text leaks nothing matchable against the markup) and C8 (only
predicates with a defensible answer become cases).

Balance is a corpus-level property, never a per-sample one. Per-SVG availability is
inherently uneven (FA-008), and forcing uniformity would make the generator serve the
allocation algorithm instead of the construct-validity rules.
"""

from svgbench.instructions.generator import build_instructions
from svgbench.instructions.lint import FORBIDDEN_PHRASES, LeakageError, lint_instruction_text
from svgbench.instructions.records import (
    Instruction,
    InstructionProvenance,
    RejectedCandidate,
)
from svgbench.instructions.templates import (
    OPERATION_PHRASES,
    TARGET_PHRASES,
    render,
    template_id,
)

__all__ = [
    "FORBIDDEN_PHRASES",
    "OPERATION_PHRASES",
    "TARGET_PHRASES",
    "Instruction",
    "InstructionProvenance",
    "LeakageError",
    "RejectedCandidate",
    "build_instructions",
    "lint_instruction_text",
    "render",
    "template_id",
]
