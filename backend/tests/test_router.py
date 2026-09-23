from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import get_db_session
from app.main import app


@pytest.fixture
def client(assistant_session):
    app.dependency_overrides[get_db_session] = lambda: assistant_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_valid_question_returns_200_with_contract_shape(client: TestClient, faq_items):
    item = faq_items[0]
    response = client.post("/api/assistant/ask", json={"question": item.question, "session_id": "s1"})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"answer", "source_link", "faq_id", "similarity_score"}
    assert body["faq_id"] == item.faq_id


def test_empty_question_returns_400(client: TestClient):
    response = client.post("/api/assistant/ask", json={"question": "", "session_id": "s1"})
    assert response.status_code == 400
    assert response.json() == {"error_code": "EMPTY_QUESTION"}


def test_missing_session_id_returns_400(client: TestClient):
    response = client.post("/api/assistant/ask", json={"question": "Hello"})
    assert response.status_code == 400
    assert response.json()["error_code"] == "MISSING_SESSION_ID"


def test_question_too_long_returns_400(client: TestClient):
    response = client.post(
        "/api/assistant/ask", json={"question": "a" * 501, "session_id": "s1"}
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "QUESTION_TOO_LONG"


def test_below_threshold_question_returns_200_not_error(client: TestClient):
    response = client.post(
        "/api/assistant/ask", json={"question": "What is the capital of France?", "session_id": "s1"}
    )
    assert response.status_code == 200
    assert response.json()["faq_id"] is None
