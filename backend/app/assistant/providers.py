"""T0.7 — LLM and embedding provider clients.

Two tiny abstractions (``EmbeddingProvider``, ``LLMProvider``) so the rest of
the assistant module never talks to a concrete vendor SDK directly. Each has
a ``mock`` implementation that works fully offline (no API key, no network)
so the service is runnable and testable before real keys exist, and a REST
implementation for the real provider chosen once T0.1/T0.7 are settled.

Provider selection is env-driven (see ``app/config.py``): ``LLM_PROVIDER`` /
``EMBEDDING_PROVIDER`` set to ``mock`` (default) or a real provider name.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import httpx
import numpy as np

from app.config import Settings

MOCK_EMBEDDING_DIM = 256


class ProviderError(RuntimeError):
    """Raised when a real provider call fails or times out.

    The assistant service treats this as "provider unavailable" (see T0.7
    fallback note) and returns 503 to the caller instead of leaking the
    underlying exception.
    """


# --------------------------------------------------------------------------
# Embeddings
# --------------------------------------------------------------------------
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic, offline, hashed bag-of-words "embedding".

    Not a real semantic embedding — it is a hashing vectorizer over
    lower-cased word tokens, L2-normalised. Cosine similarity between two
    mock vectors reflects word overlap, which is good enough to develop and
    unit-test the retrieval/threshold logic without any API key or network
    call. Swap ``EMBEDDING_PROVIDER`` to a real provider for production
    accuracy (see T3.7 accuracy test set).
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    @staticmethod
    def _embed_one(text: str) -> list[float]:
        vector = np.zeros(MOCK_EMBEDDING_DIM, dtype=np.float64)
        for token in text.lower().split():
            index = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % MOCK_EMBEDDING_DIM
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector.tolist()


class RestEmbeddingProvider(EmbeddingProvider):
    """Generic OpenAI-compatible embeddings REST client.

    Works for any provider exposing the ``POST {base_url} {"input": [...],
    "model": ...} -> {"data": [{"embedding": [...]}, ...]}`` shape (OpenAI,
    Voyage AI, and most compatible providers). Pick the concrete provider
    via ``EMBEDDING_PROVIDER`` + set ``EMBEDDING_API_KEY`` / ``EMBEDDING_MODEL``.
    """

    _BASE_URLS = {
        "openai": "https://api.openai.com/v1/embeddings",
        "voyage": "https://api.voyageai.com/v1/embeddings",
    }

    def __init__(self, provider_name: str, api_key: str, model: str, timeout: float = 4.0):
        if provider_name not in self._BASE_URLS:
            raise ValueError(f"Unknown embedding provider: {provider_name!r}")
        if not api_key:
            raise ProviderError(f"EMBEDDING_API_KEY is not set for provider {provider_name!r}")
        self._url = self._BASE_URLS[provider_name]
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = httpx.post(
                self._url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"input": texts, "model": self._model},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Embedding provider request failed: {exc}") from exc
        data = response.json()
        return [item["embedding"] for item in data["data"]]


# --------------------------------------------------------------------------
# LLM (answer generation / rephrasing)
# --------------------------------------------------------------------------
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Return the model's plain-text reply."""


class MockLLMProvider(LLMProvider):
    """Offline stand-in. Echoes the prompt back so tests never depend on a
    real model's wording; the assistant answer text itself must always come
    from the matched FAQ item, never from this provider (see T3.4 guard) —
    this provider exists for the smoke test in scripts/smoke_test_provider.py
    and for an optional future rephrasing step.
    """

    def generate(self, prompt: str, system: str | None = None) -> str:
        return prompt


class AnthropicLLMProvider(LLMProvider):
    """Minimal Claude Messages API client (no SDK dependency, just httpx)."""

    _URL = "https://api.anthropic.com/v1/messages"
    _ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, api_key: str, model: str, timeout: float = 4.0):
        if not api_key:
            raise ProviderError("LLM_API_KEY is not set for provider 'anthropic'")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model": self._model,
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        try:
            response = httpx.post(
                self._URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": self._ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"LLM provider request failed: {exc}") from exc
        data = response.json()
        return "".join(block.get("text", "") for block in data.get("content", []))


# --------------------------------------------------------------------------
# Factories
# --------------------------------------------------------------------------
def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "mock" or not settings.embedding_api_key:
        return MockEmbeddingProvider()
    return RestEmbeddingProvider(
        provider_name=settings.embedding_provider,
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        timeout=settings.assistant_timeout_seconds,
    )


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock" or not settings.llm_api_key:
        return MockLLMProvider()
    if settings.llm_provider == "anthropic":
        return AnthropicLLMProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout=settings.assistant_timeout_seconds,
        )
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider!r}")
