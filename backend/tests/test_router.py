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
    assert set(body) == {"answer", "source_link", "faq_id", "similarity_score"}
    assert body["faq_id"] == item.faq_id


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"question": "", "session_id": "s1"}, "question"),
        ({"question": "   ", "session_id": "s1"}, "question"),
        ({"question": "a" * 501, "session_id": "s1"}, "question"),
        ({"question": "Hello"}, "session_id"),
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
