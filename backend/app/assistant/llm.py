"""Gemini calls for grounded answers (US10), free tier only.

Free limits are per model, so the configured models are tried in order and the
next one is asked when a model answers 429 (limit reached) or 503 (free models
are often overloaded). Any other failure - no key, API error, timeout, every
model busy - raises LlmUnavailable, and the caller answers with the
word-for-word FAQ answer of Sprint 1.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

from google import genai
from google.genai import errors, types

from app.config import Settings

logger = logging.getLogger(__name__)

# 429: the model's free limit is reached; 503: the model is overloaded ("high demand").
# Both come back fast, and another model can still answer in time.
TRY_NEXT_MODEL = {429: "rate_limited", 503: "overloaded"}


class LlmUnavailable(Exception):
    """No model answered; the caller falls back to the FAQ answer."""


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    prompt_tokens: int | None
    output_tokens: int | None
    latency_ms: int


class Llm(Protocol):
    def generate(self, system: str, prompt: str, json_schema: dict[str, Any]) -> Generation: ...


class GeminiLlm:
    def __init__(
        self,
        models: list[str],
        timeout_seconds: float,
        thinking_level: str = "",
        api_key: str = "",
        client: genai.Client | None = None,
    ):
        self._models = models
        self._thinking_level = thinking_level.strip()
        # No retry_options: the SDK then makes one attempt, and a 429 goes straight
        # to the next model instead of being retried with back-off.
        self._client = client or genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000))
        )

    def generate(self, system: str, prompt: str, json_schema: dict[str, Any]) -> Generation:
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=json_schema,
            thinking_config=types.ThinkingConfig(thinking_level=self._thinking_level) if self._thinking_level else None,
        )
        for model in self._models:
            started = time.monotonic()
            try:
                response = self._client.models.generate_content(model=model, contents=prompt, config=config)
            except errors.APIError as error:
                latency_ms = _elapsed_ms(started)
                if error.code in TRY_NEXT_MODEL:
                    logger.warning("gemini model=%s outcome=%s latency_ms=%d", model, TRY_NEXT_MODEL[error.code], latency_ms)
                    continue
                logger.warning(
                    "gemini model=%s outcome=api_error code=%s latency_ms=%d message=%s",
                    model,
                    error.code,
                    latency_ms,
                    error.message,
                )
                raise LlmUnavailable(f"{model}: API error {error.code}") from error
            except Exception as error:  # timeouts and network errors from the HTTP client
                logger.warning(
                    "gemini model=%s outcome=%s latency_ms=%d", model, type(error).__name__, _elapsed_ms(started)
                )
                raise LlmUnavailable(f"{model}: {type(error).__name__}") from error

            usage = response.usage_metadata
            generation = Generation(
                text=response.text or "",
                model=model,
                prompt_tokens=usage.prompt_token_count if usage else None,
                output_tokens=usage.candidates_token_count if usage else None,
                latency_ms=_elapsed_ms(started),
            )
            logger.info(
                "gemini model=%s outcome=ok prompt_tokens=%s output_tokens=%s latency_ms=%d",
                generation.model,
                generation.prompt_tokens,
                generation.output_tokens,
                generation.latency_ms,
            )
            return generation
        raise LlmUnavailable("every model is at its free limit or overloaded")


def get_llm(settings: Settings) -> Llm | None:
    """The configured model, or None without a key (Sprint 1 answers only)."""
    if not settings.gemini_api_key.strip() or not settings.gemini_model_list:
        return None
    return _gemini(
        settings.gemini_api_key,
        tuple(settings.gemini_model_list),
        settings.gemini_timeout_seconds,
        settings.gemini_thinking_level,
    )


@lru_cache(maxsize=4)
def _gemini(api_key: str, models: tuple[str, ...], timeout_seconds: float, thinking_level: str) -> GeminiLlm:
    # One client (and its HTTP connection pool) per configuration, not one per question.
    return GeminiLlm(list(models), timeout_seconds, thinking_level, api_key=api_key)


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
