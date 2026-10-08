"""US13 feedback API and export: stored context, one rating, seven-day window."""
from __future__ import annotations

import csv
import io
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.assistant.feedback import AnswerFeedback
from app.conversation.service import record_answer, record_question
from app.db import get_session_factory
from app.main import app
from scripts.export_negative_feedback import export_feedback


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(db_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _answer(session, session_id="s1", question="When is the deadline?", answer="October 2"):
    record_question(session, session_id, question)
    return record_answer(
        session, session_id, answer,
        [{"faq_id": "faq-1", "question": "Deadline?", "link": "https://sdu.edu.kz/faq"}],
    )


def test_feedback_saves_answer_question_sources_and_reason(client, db_session):
    answer = _answer(db_session)

    response = client.post("/api/assistant/feedback", json={
        "answer_id": str(answer.id), "session_id": "s1", "rating": "down", "reason": "outdated",
    })

    assert response.status_code == 201
    assert response.json() == {"answer_id": str(answer.id), "rating": "down", "reason": "outdated"}
    saved = db_session.scalar(select(AnswerFeedback).where(AnswerFeedback.answer_id == answer.id))
    assert (saved.session_id, saved.question, saved.answer, saved.reason) == (
        "s1", "When is the deadline?", "October 2", "outdated"
    )
    assert saved.sources == answer.sources


def test_one_rating_per_answer_and_unknown_answer(client, db_session):
    answer = _answer(db_session)
    body = {"answer_id": str(answer.id), "session_id": "s1", "rating": "up"}
    assert client.post("/api/assistant/feedback", json=body).status_code == 201
    duplicate = client.post("/api/assistant/feedback", json=body)
    assert duplicate.status_code == 409
    assert duplicate.json()["error_code"] == "ALREADY_RATED"
    assert client.post("/api/assistant/feedback", json={**body, "answer_id": "999999999"}).status_code == 404


def test_invalid_feedback_is_rejected(client, db_session):
    question = record_question(db_session, "s1", "Question only")
    for body in (
        {"answer_id": str(question.id), "session_id": "s1", "rating": "down"},
        {"answer_id": "garbage", "session_id": "s1", "rating": "down"},
        {"answer_id": str(question.id), "session_id": "s1", "rating": "maybe"},
        {"answer_id": str(question.id), "session_id": "s1", "rating": "up", "reason": "outdated"},
    ):
        response = client.post("/api/assistant/feedback", json=body)
        assert response.status_code in (404, 422)
    assert db_session.scalars(select(AnswerFeedback)).all() == []


def test_export_only_recent_negative_feedback_and_redacts_contact_details(client, db_session):
    now = datetime.now(timezone.utc)
    recent = _answer(db_session, question="Contact me at user@example.com or +7 777 123 45 67")
    old = _answer(db_session, "s2")
    positive = _answer(db_session, "s3")
    for answer, rating in ((recent, "down"), (old, "down"), (positive, "up")):
        assert client.post("/api/assistant/feedback", json={
            "answer_id": str(answer.id), "session_id": answer.session_id, "rating": rating, "reason": "outdated" if rating == "down" else None,
        }).status_code == 201
    db_session.scalar(select(AnswerFeedback).where(AnswerFeedback.answer_id == old.id)).created_at = now - timedelta(days=8)
    db_session.commit()

    output = io.StringIO()
    assert export_feedback(db_session, output, days=7, now=now) == 1
    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert len(rows) == 1
    assert rows[0]["reason"] == "outdated"
    assert "faq-1" in rows[0]["sources"]
    assert "user@example.com" not in output.getvalue()
    assert "+7 777 123 45 67" not in output.getvalue()
    assert "session_id" not in output.getvalue()


def test_an_answer_can_only_be_rated_from_its_own_session(client, db_session):
    answer = _answer(db_session, "applicant-a")

    response = client.post(
        "/api/assistant/feedback", json={"answer_id": str(answer.id), "session_id": "applicant-b", "rating": "down"}
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "ANSWER_NOT_FOUND"
    assert db_session.scalars(select(AnswerFeedback)).all() == []


@pytest.mark.parametrize("answer_id", ["2147483648", "999999999999999999"])
def test_answer_id_beyond_the_id_range_is_not_found(client, answer_id):
    response = client.post("/api/assistant/feedback", json={"answer_id": answer_id, "session_id": "s1", "rating": "up"})

    assert response.status_code == 404


def test_session_id_is_required(client, db_session):
    answer = _answer(db_session)

    response = client.post("/api/assistant/feedback", json={"answer_id": str(answer.id), "rating": "up"})

    assert response.status_code == 422
