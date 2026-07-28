"""The freeze point: content-addressed hashing, manifest generation, verification.

Everything upstream of this module is stochastic. Everything downstream loads by
dataset hash and refuses to run on a mismatch, so an arm can never be compared
against a corpus it did not see.
"""
