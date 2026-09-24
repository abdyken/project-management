from __future__ import annotations

import time
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from app.assistant.service import AssistantService
from app.db import get_session_factory
from app.main import app


@pytest.fixture
def client(assistant_session):
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_valid_question_returns_200_with_contract_shape(client: TestClient, faq_items):
    item = faq_items[0]
    response = client.post("/api/assistant/ask", json={"question": item.question, "session_id": "s1"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"answer", "source_link", "faq_id", "similarity_score"}
    assert body["faq_id"] == item.faq_id


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"question": "", "session_id": "s1"}, "question"),
        ({"question": "   ", "session_id": "s1"}, "question"),
        ({"question": "a" * 501, "session_id": "s1"}, "question"),
        ({"question": "Hello"}, "session_id"),
        ({"question": "Hello" + chr(0), "session_id": "s1"}, "question"),
    ],
)
def test_invalid_request_returns_422_error_contract(client: TestClient, payload, field):
    response = client.post("/api/assistant/ask", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "INVALID_REQUEST"
    assert body["message"].startswith(f"{field}:")


def test_below_threshold_question_returns_200_not_error(client: TestClient):
    response = client.post(
        "/api/assistant/ask", json={"question": "What is the capital of France?", "session_id": "s1"}
    )
    assert response.status_code == 200
    assert response.json()["faq_id"] is None


def test_slow_answer_returns_504_error_contract(client: TestClient, monkeypatch):
    monkeypatch.setenv("ASSISTANT_TIMEOUT_SECONDS", "0.05")
    monkeypatch.setattr(AssistantService, "answer", lambda self, question, session_id: time.sleep(0.3))
    response = client.post("/api/assistant/ask", json={"question": "Hello", "session_id": "s1"})
    assert response.status_code == 504
    assert response.json()["error_code"] == "ASSISTANT_TIMEOUT"
