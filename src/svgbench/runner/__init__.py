"""The single shared execution path used by every arm.

Prompt assembly, model client, and the append-only response store. There is one
runner and one prompt template; arms differ only in which ContextProvider fills
the context slot. Two separately-authored pipelines would drift, and no care
downstream would recover the comparison.
"""
