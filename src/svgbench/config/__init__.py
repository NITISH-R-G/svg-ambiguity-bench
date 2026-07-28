"""Configuration schema, layering (base -> experiment -> CLI override), validation
and canonical hashing.

The resolved config's hash is the identity of an experiment. Anything that can
influence a result must be represented here: a value that lives as an implicit
default inside code is not in the hash, and the hash would then be a lie.
"""
