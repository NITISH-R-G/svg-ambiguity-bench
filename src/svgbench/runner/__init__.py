"""The single shared execution path used by every arm.

Prompt assembly, model client, and the append-only response store. There is one
runner and one prompt template; arms differ only in which ContextProvider fills the
context slot. Two separately-authored pipelines would drift, and no care downstream
would recover the comparison.

Supports C2 (arms comparable) and C6 (every number independently verifiable - the
store is what makes Tier-1 and Tier-2 reproduction possible without a model).
"""

from svgbench.runner.client import (
    ModelClient,
    ModelResponse,
    OllamaClient,
    StubClient,
    build_client,
)
from svgbench.runner.prompt import TEMPLATE_ID, TEMPLATE_VERSION, build_prompt
from svgbench.runner.run import run_arm
from svgbench.runner.store import ResponseStore

__all__ = [
    "TEMPLATE_ID",
    "TEMPLATE_VERSION",
    "ModelClient",
    "ModelResponse",
    "OllamaClient",
    "ResponseStore",
    "StubClient",
    "build_client",
    "build_prompt",
    "run_arm",
]
