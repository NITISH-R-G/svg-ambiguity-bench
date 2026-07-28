"""Scene synthesis and geometry redaction.

Owns the invariant that every piece of positional information lives inside the
path `d` attribute. A `transform`, `x` or `cx` on an ambiguity-set member would
silently reintroduce readable position and destroy the premise of the benchmark.
"""
