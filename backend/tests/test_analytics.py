"""US9 admissions dashboard: numbers on a fixed dataset match a hand count."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.analytics.service import build_report
from app.assistant.feedback import AnswerFeedback
from app.conversation.models import ChatTurn
from app.db import get_db_session
from app.followups.models import UNANSWERED_QUESTION, AdmissionsFollowup
from app.main import app
from app.staff.service import create_user, login_limiter

# 16.10.2026 10:00 in Kazakhstan (UTC+5).
NOW = datetime(2026, 10, 16, 5, 0, tzinfo=timezone.utc)
PASSWORD = "correct horse battery"


def _turn(session, session_id, role, text, hours_ago, sources=None):
    turn = ChatTurn(session_id=session_id, role=role, text=text, sources=sources, created_at=NOW - timedelta(hours=hours_ago))
    session.add(turn)
    session.flush()
    return turn


@pytest.fixture
def dataset(db_session):
    db_session.execute(delete(ChatTurn))
    dorm = [{"faq_id": "faq-022", "question": "How much does the dormitory cost?", "link": "https://sdu.edu.kz"}]
    # Today (16.10): 3 questions from 2 sessions.
    _turn(db_session, "a", "user", "How much is the dormitory?", 1)
    first = _turn(db_session, "a", "assistant", "552,500 KZT", 1, dorm)
    _turn(db_session, "b", "user", "how much is the DORMITORY", 2)
    second = _turn(db_session, "b", "assistant", "552,500 KZT", 2, dorm)
    _turn(db_session, "b", "user", "Call me +7 777 123 45 67", 3)
    _turn(db_session, "b", "assistant", "Sorry", 3)
    # Yesterday local time (15.10, 23:30 = 18:30 UTC): Russian and Kazakh questions.
    _turn(db_session, "c", "user", "Сколько стоит общежитие?", 10.5)
    _turn(db_session, "c", "assistant", "552 500 тг", 10.5, dorm)
    _turn(db_session, "d", "user", "Жатақхана қанша тұрады?", 11)
    # Outside a 7-day window.
    _turn(db_session, "e", "user", "Old question", 24 * 8)
    for hours, text in ((3, "Call me +7 777 123 45 67"), (11, "Жатақхана қанша тұрады?"), (24 * 8, "Old question")):
        db_session.add(
            AdmissionsFollowup(kind=UNANSWERED_QUESTION, question=text, session_id="x", created_at=NOW - timedelta(hours=hours))
        )
    db_session.add_all(
        [
            AnswerFeedback(answer_id=first.id, rating="up", session_id="a", question="q", answer="a", created_at=NOW),
            AnswerFeedback(
                answer_id=second.id, rating="down", reason="outdated", session_id="b", question="q", answer="a", created_at=NOW
            ),
        ]
    )
    db_session.flush()
    return db_session


def test_report_matches_the_hand_count(dataset):
    report = build_report(dataset, days=7, now=NOW)

    assert (report.questions, report.sessions, report.unanswered) == (5, 4, 2)
    assert report.per_day[-1] == {"date": "2026-10-16", "questions": 3, "unanswered": 1}
    assert report.per_day[-2] == {"date": "2026-10-15", "questions": 2, "unanswered": 1}
    assert len(report.per_day) == 7 and report.per_day[0]["date"] == "2026-10-10"
    assert report.top_questions[0] == {"question": "How much is the dormitory?", "count": 2}
    assert {"question": "Call me [phone redacted]", "count": 1} in report.top_questions
    assert report.top_sources == [{"faq_id": "faq-022", "question": "How much does the dormitory cost?", "count": 3}]
    assert report.languages == {"en": 3, "ru": 1, "kk": 1}
    assert report.ratings == {"up": 1, "down": 1}
    assert report.down_reasons == {"outdated": 1}


def test_one_day_window_is_today_in_kazakhstan_time(dataset):
    report = build_report(dataset, days=1, now=NOW)
    assert (report.questions, report.unanswered) == (3, 1)


def test_api_needs_login_limits_days_and_hides_sessions(dataset):
    login_limiter.reset(*list(login_limiter._failures))
    app.dependency_overrides[get_db_session] = lambda: dataset
    try:
        client = TestClient(app, base_url="https://testserver")
        assert client.get("/api/staff/analytics").status_code == 401
        create_user(dataset, "officer@sdu.edu.kz", "Aigerim", "officer", PASSWORD)
        client.post("/api/staff/login", json={"email": "officer@sdu.edu.kz", "password": PASSWORD})

        response = client.get("/api/staff/analytics", params={"days": 30})

        assert response.status_code == 200
        assert response.json()["days"] == 30
        assert '"a"' not in response.text and "+7 777" not in response.text
        assert client.get("/api/staff/analytics", params={"days": 31}).status_code == 422
    finally:
        app.dependency_overrides.clear()
