"""US10 / T10.1, T10.3: Gemini model chain with a fake client (no network)."""
from __future__ import annotations

import logging
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors

from app.assistant.llm import GeminiLlm, LlmUnavailable, get_llm
from app.config import get_settings

MODELS = ["model-a", "model-b", "model-c"]
SCHEMA = {"type": "object"}


def rate_limited() -> errors.ClientError:
    return errors.ClientError(429, {"error": {"code": 429, "message": "Quota exceeded", "status": "RESOURCE_EXHAUSTED"}})


def ok(text: str = '{"answer": "ok", "cited_faq_ids": []}'):
    usage = SimpleNamespace(prompt_token_count=120, candidates_token_count=15)
    return SimpleNamespace(text=text, usage_metadata=usage)


class FakeClient:
    """Answers each call with the next outcome: a response, or an exception to raise."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.models_called: list[str] = []
        self.models = self

    def generate_content(self, model, contents, config):
        self.models_called.append(model)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def llm(client: FakeClient) -> GeminiLlm:
    return GeminiLlm(MODELS, timeout_seconds=5, thinking_level="minimal", client=client)


def test_first_model_answers_and_its_model_tokens_and_latency_are_logged(caplog):
    client = FakeClient(ok())
    with caplog.at_level(logging.INFO, logger="app.assistant.llm"):
        generation = llm(client).generate("system", "prompt", SCHEMA)

    assert client.models_called == ["model-a"]
    assert (generation.model, generation.prompt_tokens, generation.output_tokens) == ("model-a", 120, 15)
    assert "model=model-a outcome=ok prompt_tokens=120 output_tokens=15 latency_ms=" in caplog.text


def test_model_at_its_free_limit_is_replaced_by_the_next_one():
    client = FakeClient(rate_limited(), ok())

    generation = llm(client).generate("system", "prompt", SCHEMA)

    assert client.models_called == ["model-a", "model-b"]
    assert generation.model == "model-b"


def test_all_models_at_their_limit_is_unavailable():
    client = FakeClient(rate_limited(), rate_limited(), rate_limited())

    with pytest.raises(LlmUnavailable, match="free limit"):
        llm(client).generate("system", "prompt", SCHEMA)
    assert client.models_called == MODELS


@pytest.mark.parametrize(
    "failure",
    [
        errors.ServerError(500, {"error": {"code": 500, "message": "Internal", "status": "INTERNAL"}}),
        errors.ClientError(400, {"error": {"code": 400, "message": "Bad model", "status": "INVALID_ARGUMENT"}}),
        httpx.ReadTimeout("timed out"),
        httpx.ConnectError("no network"),
    ],
)
def test_api_error_or_timeout_is_unavailable_without_trying_the_next_model(failure):
    client = FakeClient(failure, ok())

    with pytest.raises(LlmUnavailable):
        llm(client).generate("system", "prompt", SCHEMA)
    assert client.models_called == ["model-a"]


def test_no_api_key_means_no_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert get_llm(get_settings()) is None


def test_with_a_key_the_configured_models_are_used_in_order(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODELS", " model-x , model-y ,")

    settings = get_settings()

    assert settings.gemini_model_list == ["model-x", "model-y"]
    assert isinstance(get_llm(settings), GeminiLlm)
