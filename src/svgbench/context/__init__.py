"""ContextProvider implementations - one per experimental arm.

The provider signature is (svg, svg_id) -> ContextBlock. The instruction is
deliberately not a parameter, so instruction-blindness is enforced by the type
system rather than by reviewer discipline: a contributor cannot leak the
instruction into the context because it is not reachable from inside a provider.
"""
