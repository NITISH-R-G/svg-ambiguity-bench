"""ContextProvider implementations - one per experimental arm.

The provider signature is (svg_id, geometry) -> str. The instruction is deliberately
not a parameter, so instruction-blindness is enforced by the type system rather than
by reviewer discipline: a contributor cannot leak the instruction into the context
because it is not reachable from inside a provider.

Supports C2 (arms differ in exactly one variable) and C3 (the `permuted` control that
separates information from format).
"""

from svgbench.context.providers import (
    CeilingProvider,
    ContextProvider,
    EnhancedProvider,
    NullProvider,
    PermutedProvider,
    build_provider,
)

__all__ = [
    "CeilingProvider",
    "ContextProvider",
    "EnhancedProvider",
    "NullProvider",
    "PermutedProvider",
    "build_provider",
]
