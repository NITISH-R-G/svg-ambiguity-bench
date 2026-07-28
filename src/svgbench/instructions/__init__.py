"""Instruction synthesis, ground-truth resolution, and the leakage lint.

Resolution is performed by code against ground truth - never by a model and never
by hand. An instruction that does not resolve to exactly one element with
sufficient margin is not emitted.
"""
