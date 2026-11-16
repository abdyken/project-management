"""Per-client-IP limits on the public endpoints that may call Gemini."""
from __future__ import annotations

from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import get_db_session, get_session_factory
from app.main import app

TOO_MANY = {"error_code": "TOO_MANY_REQUESTS", "message": "Too many requests. Please wait a minute and try again."}


@pytest.fixture
def client(assistant_session):
    app.dependency_overrides[get_db_session] = lambda: assistant_session
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _ask(client, path="/api/assistant/ask", ip=None):
    headers = {"X-Forwarded-For": f"{ip}, 172.18.0.5"} if ip else {}
    return client.post(path, json={"question": "How much does the dormitory cost?", "session_id": "s1"}, headers=headers)


def test_defaults_are_generous_for_real_applicants():
    settings = Settings()
    assert (settings.assistant_requests_per_minute, settings.recommendations_requests_per_minute) == (20, 10)


def test_ask_and_stream_share_one_limit_per_client_ip(client, monkeypatch):
    monkeypatch.setenv("ASSISTANT_REQUESTS_PER_MINUTE", "3")

    assert _ask(client).status_code == 200
    assert _ask(client, "/api/assistant/ask/stream").status_code == 200
    assert _ask(client).status_code == 200
    for path in ("/api/assistant/ask", "/api/assistant/ask/stream"):
        refused = _ask(client, path)
        assert refused.status_code == 429
        assert refused.json() == TOO_MANY

    assert _ask(client, ip="203.0.113.7").status_code == 200
    assert client.get("/api/assistant/suggestions", params={"session_id": "s1"}).status_code == 200


def test_limit_counts_the_visitor_behind_the_proxy(client, monkeypatch):
    monkeypatch.setenv("ASSISTANT_REQUESTS_PER_MINUTE", "1")

    assert _ask(client, ip="203.0.113.7").status_code == 200
    assert _ask(client, ip="203.0.113.7").status_code == 429
    assert _ask(client, ip="203.0.113.8").status_code == 200


def test_recommendations_are_limited_per_client_ip(client, monkeypatch):
    monkeypatch.setenv("RECOMMENDATIONS_REQUESTS_PER_MINUTE", "2")
    body = {"interests": ["computing"], "scores": {"unt_total": 90}}

    assert [client.post("/api/recommendations", json=body).status_code for _ in range(2)] == [200, 200]
    refused = client.post("/api/recommendations", json=body)
    assert refused.status_code == 429
    assert refused.json() == TOO_MANY
    assert _ask(client).status_code == 200


def test_429_is_documented_in_openapi():
    paths = app.openapi()["paths"]
    for path in ("/api/assistant/ask", "/api/assistant/ask/stream", "/api/recommendations"):
        assert "429" in paths[path]["post"]["responses"]
