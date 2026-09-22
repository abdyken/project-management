"""T3.5 contract: exact request/response/error shape of POST /api/assistant/ask."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.assistant import router as router_module
from app.main import app


@pytest.fixture(autouse=True)
def _reset_service_singleton():
    router_module.reset_assistant_service_cache()
    yield
    router_module.reset_assistant_service_cache()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_valid_question_returns_200_with_contract_shape(client: TestClient):
    response = client.post(
        "/api/assistant/ask",
        json={"question": "What is the deadline to apply for the Fall intake?", "session_id": "s1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"answer", "source_link", "faq_id", "similarity_score"}
    assert body["faq_id"] == "faq-001"


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
    """Fallback (T3.4) uses the normal 200 response shape — the front-end
    should not need a separate branch for it (see T3.5 contract)."""
    response = client.post(
        "/api/assistant/ask", json={"question": "What is the capital of France?", "session_id": "s1"}
    )
    assert response.status_code == 200
    assert response.json()["faq_id"] is None
