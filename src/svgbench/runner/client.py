"""Model clients.

Two backends: `ollama` for real runs, and `stub` for tests and CI, which needs no model
and no network.

Every call records the full resolved prompt and the raw response verbatim. That is what
makes Tier-1 and Tier-2 reproduction possible: a reviewer with no model can re-derive
every published number from the stored responses, and a sceptical one can write their own
scorer and check it against ours.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

from svgbench.config import ModelConfig


class ModelResponse:
    """One call's result, including its failures."""

    def __init__(
        self,
        text: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        latency_ms: int,
        truncated: bool,
        error: str | None = None,
    ) -> None:
        self.text = text
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.latency_ms = latency_ms
        # Recorded separately from `error` so a format failure caused by hitting the
        # token limit is never silently counted as an identification failure.
        self.truncated = truncated
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_ms": self.latency_ms,
            "truncated": self.truncated,
            "error": self.error,
        }


class ModelClient(Protocol):
    def generate(self, prompt: str) -> ModelResponse: ...


class StubClient:
    """Deterministic fake for tests and CI.

    Echoes the SVG it was given, unchanged. That makes every case score `NO_EDIT`, which
    is a known, checkable outcome - useful for exercising the pipeline end to end without
    pretending to measure anything.
    """

    def __init__(self, config: ModelConfig) -> None:
        self._config = config

    def generate(self, prompt: str) -> ModelResponse:
        start = prompt.find("<svg")
        end = prompt.find("</svg>", start)
        echoed = prompt[start : end + 6] if start != -1 and end != -1 else ""
        return ModelResponse(
            text=echoed,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(echoed) // 4,
            latency_ms=0,
            truncated=False,
        )


class OllamaClient:
    """Local Ollama backend.

    Decoding parameters come from the config and are recorded in the run manifest.
    `num_predict` is passed explicitly so truncation is detectable rather than silent.
    """

    def __init__(self, config: ModelConfig) -> None:
        self._config = config
        self._client = httpx.Client(base_url=config.base_url, timeout=config.timeout_s)

    def generate(self, prompt: str) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self._config.name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self._config.temperature,
                "top_p": self._config.top_p,
                "num_predict": self._config.max_output_tokens,
            },
        }
        if self._config.seed is not None:
            payload["options"]["seed"] = self._config.seed

        started = time.monotonic()
        try:
            response = self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # An error is an outcome, not a reason to drop the case. Denominators are
            # fixed at freeze time.
            return ModelResponse(
                text="",
                prompt_tokens=None,
                completion_tokens=None,
                latency_ms=int((time.monotonic() - started) * 1000),
                truncated=False,
                error=f"{type(exc).__name__}: {exc}",
            )

        completion = int(body.get("eval_count") or 0)
        return ModelResponse(
            text=body.get("response", ""),
            prompt_tokens=int(body.get("prompt_eval_count") or 0),
            completion_tokens=completion,
            latency_ms=int((time.monotonic() - started) * 1000),
            truncated=completion >= self._config.max_output_tokens,
        )

    def close(self) -> None:
        self._client.close()


def build_client(config: ModelConfig) -> ModelClient:
    if config.backend == "stub":
        return StubClient(config)
    if config.backend == "ollama":
        return OllamaClient(config)
    raise ValueError(f"unknown backend {config.backend!r}")
