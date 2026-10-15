"""US22 unanswered question inbox: grouping, redaction, dismiss, answer with a published FAQ item."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import get_db_session
from app.followups.models import UNANSWERED_QUESTION, AdmissionsFollowup
from app.main import app
from app.staff.service import create_user, login_limiter

PASSWORD = "correct horse battery"
NEW_ITEM = {
    "category": "student-services",
    "question": "Is there a hackathon at SDU?",
    "answer": "Yes, the SDU hackathon takes place every spring.",
    "source_link": "https://sdu.edu.kz/en/hackathon/",
}


def add(session, question, days_ago=1, score=0.3, session_id="secret-session-id"):
    session.add(
        AdmissionsFollowup(
            kind=UNANSWERED_QUESTION,
            question=question,
            similarity_score=score,
            session_id=session_id,
            created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        )
    )
    session.flush()


@pytest.fixture
def client(db_session):
    login_limiter.reset(*list(login_limiter._failures))
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        yield TestClient(app, base_url="https://testserver")
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def officer(client, db_session):
    create_user(db_session, "officer@sdu.edu.kz", "Aigerim", "officer", PASSWORD)
    assert client.post("/api/staff/login", json={"email": "officer@sdu.edu.kz", "password": PASSWORD}).status_code == 200
    return client


@pytest.fixture
def questions(db_session):
    add(db_session, "Is there a hackathon?", days_ago=3, score=0.31)
    add(db_session, "is there a HACKATHON", days_ago=2, score=0.42)
    add(db_session, "Write to me at aigerim@example.com about parking", days_ago=1)
    add(db_session, "Есть ли бассейн?", days_ago=1)
    add(db_session, "Very old question", days_ago=40)


@pytest.mark.parametrize(("method", "path"), [("get", "/api/staff/inbox"), ("post", "/api/staff/inbox/dismiss"), ("post", "/api/staff/inbox/answer")])
def test_inbox_needs_login(client, method, path):
    response = getattr(client, method)(path, **({"json": {"key": "x", "faq_id": "faq-001"}} if method == "post" else {}))
    assert response.status_code == 401


def test_inbox_groups_counts_and_redacts(officer, questions):
    body = officer.get("/api/staff/inbox").json()

    assert [(item["question"], item["count"]) for item in body["items"]] == [
        ("Is there a hackathon?", 2),
        ("Write to me at [email redacted] about parking", 1),
        ("Есть ли бассейн?", 1),
    ]
    assert body["total_asks"] == 4
    first = body["items"][0]
    assert first["key"] == "is there a hackathon"
    assert first["best_score"] == pytest.approx(0.42)
    assert body["items"][2]["language"] == "ru"
    raw = officer.get("/api/staff/inbox").text
    assert "secret-session-id" not in raw and "aigerim@example.com" not in raw
    assert officer.get("/api/staff/inbox", params={"days": 60}).json()["total_asks"] == 5


def test_dismiss_moves_the_whole_group(officer, questions, db_session):
    response = officer.post("/api/staff/inbox/dismiss", json={"key": "is there a hackathon"})

    assert response.json() == {"key": "is there a hackathon", "status": "dismissed", "updated": 2}
    new = [item["question"] for item in officer.get("/api/staff/inbox").json()["items"]]
    assert "Is there a hackathon?" not in new
    dismissed = officer.get("/api/staff/inbox", params={"status": "dismissed"}).json()["items"]
    assert [item["count"] for item in dismissed] == [2]
    rows = db_session.scalars(select(AdmissionsFollowup).where(AdmissionsFollowup.status == "dismissed")).all()
    assert {row.handled_by_id is not None and row.handled_at is not None for row in rows} == {True}
    assert officer.post("/api/staff/inbox/dismiss", json={"key": "is there a hackathon"}).status_code == 404


def test_answer_needs_a_published_faq_item(officer, questions):
    draft = officer.post("/api/staff/faq", json=NEW_ITEM).json()

    refused = officer.post("/api/staff/inbox/answer", json={"key": "is there a hackathon", "faq_id": draft["faq_id"]})
    assert refused.status_code == 409
    assert refused.json()["error_code"] == "FAQ_NOT_PUBLISHED"
    assert officer.post("/api/staff/inbox/answer", json={"key": "is there a hackathon", "faq_id": "faq-999"}).status_code == 409

    officer.post(f"/api/staff/faq/{draft['faq_id']}/publish")
    answered = officer.post("/api/staff/inbox/answer", json={"key": "is there a hackathon", "faq_id": draft["faq_id"]})

    assert answered.json()["updated"] == 2
    items = officer.get("/api/staff/inbox", params={"status": "answered"}).json()["items"]
    assert [(item["question"], item["faq_id"]) for item in items] == [("Is there a hackathon?", draft["faq_id"])]


def test_a_new_ask_after_handling_starts_a_new_group(officer, questions, db_session):
    officer.post("/api/staff/inbox/dismiss", json={"key": "is there a hackathon"})
    add(db_session, "Is there a hackathon??", days_ago=0)
    items = officer.get("/api/staff/inbox").json()["items"]
    assert ("Is there a hackathon??", 1) in [(item["question"], item["count"]) for item in items]
