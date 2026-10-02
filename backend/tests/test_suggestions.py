"""US14: GET /api/assistant/suggestions for the chat widget."""
from __future__ import annotations

from contextlib import nullcontext

from fastapi.testclient import TestClient

from app.assistant.suggestions import FOLLOW_UP_LIMIT, STARTER_LIMIT, STARTERS
from app.conversation.service import record_question
from app.db import get_session_factory
from app.main import app


def test_a_new_session_gets_four_starter_questions(assistant_session):
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        response = TestClient(app).get("/api/assistant/suggestions", params={"session_id": "fresh"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert suggestions == STARTERS
    assert len(suggestions) == STARTER_LIMIT


def test_follow_ups_skip_a_question_the_session_already_asked(assistant_session):
    record_question(assistant_session, "s1", STARTERS[0])
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        response = TestClient(app).get("/api/assistant/suggestions", params={"session_id": "s1"})
    finally:
        app.dependency_overrides.clear()

    suggestions = response.json()["suggestions"]
    assert response.status_code == 200
    assert len(suggestions) == FOLLOW_UP_LIMIT
    assert STARTERS[0] not in suggestions


def test_missing_session_id_is_rejected():
    response = TestClient(app).get("/api/assistant/suggestions")
    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_REQUEST"
