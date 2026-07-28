"""Cross-cutting checks that gate publication.

Leakage (positional attributes, token-length side channels, document-order
correlation), enhancement blindness, generation determinism, and design balance.
These run in CI because the failures they catch are silent: the experiment still
produces a number, it is just the wrong number.
"""
