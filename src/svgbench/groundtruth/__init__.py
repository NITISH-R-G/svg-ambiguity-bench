"""Derives per-element geometric facts and evaluates the predicate registry.

Enforces the separability guarantees. A case whose intended target does not beat
the runner-up by the configured margin is rejected and regenerated - never
shipped with a contested answer. Rejections are logged, because rejection
sampling biases the corpus and the size of that bias must be publishable.
"""
