"""US20 FAQ management: the faq_item table as the source of truth, the staff API, and the
assistant using an edit at once."""
from __future__ import annotations

from contextlib import nullcontext
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.assistant.models import FaqEmbeddingRecord
from app.assistant.retrieval import load_faq_base, search
from app.assistant.suggestions import STARTERS, suggest
from app.db import get_db_session, get_session_factory
from app.faq.models import FaqRecord
from app.faq.service import to_faq_item
from app.main import app
from app.staff.service import create_user, login_limiter

from tests.conftest import BACKEND_ROOT

PASSWORD = "correct horse battery"
NEW_ITEM = {
    "category": "dormitory",
    "question": "Can I keep a bicycle at the dormitory?",
    "answer": "Yes, the Student House has a bicycle room on the ground floor.",
    "source_link": "https://sdu.edu.kz/en/student-house/",
    "degrees": ["bachelor"],
    "applicant_types": ["local", "international"],
}


@pytest.fixture
def client(assistant_session):
    login_limiter.reset(*list(login_limiter._failures))
    app.dependency_overrides[get_db_session] = lambda: assistant_session
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        yield TestClient(app, base_url="https://testserver")
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def officer_client(client, assistant_session):
    create_user(assistant_session, "officer@sdu.edu.kz", "Aigerim", "officer", PASSWORD)
    assert client.post("/api/staff/login", json={"email": "officer@sdu.edu.kz", "password": PASSWORD}).status_code == 200
    return client


def _ask(client, question):
    response = client.post("/api/assistant/ask", json={"question": question, "session_id": "faq-admin-test"})
    assert response.status_code == 200
    return response.json()


def test_migration_moved_every_faq_item_unchanged(db_session):
    from_file = {item.faq_id: item.model_dump() for item in load_faq_base(BACKEND_ROOT / "app" / "data" / "faq.json")}
    from_table = {record.faq_id: to_faq_item(record).model_dump() for record in db_session.scalars(select(FaqRecord))}
    assert set(from_file) <= set(from_table)
    # The tests share the dev database: a staff edit there stamps a new last_update, so
    # only the items still carrying the file's date are compared.
    copied = [faq_id for faq_id in from_file if from_table[faq_id]["last_update"] == from_file[faq_id]["last_update"]]
    assert len(copied) >= 70
    assert all(from_table[faq_id] == from_file[faq_id] for faq_id in copied)
    evidence = db_session.scalar(select(FaqRecord.evidence).where(FaqRecord.faq_id == "faq-022"))
    assert evidence


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/staff/faq"),
        ("get", "/api/staff/faq/faq-022"),
        ("post", "/api/staff/faq"),
        ("put", "/api/staff/faq/faq-022"),
        ("post", "/api/staff/faq/faq-022/publish"),
        ("post", "/api/staff/faq/faq-022/retire"),
        ("post", "/api/staff/faq/faq-022/unpublish"),
    ],
)
def test_every_faq_endpoint_needs_login(client, method, path):
    response = getattr(client, method)(path, **({"json": NEW_ITEM} if method in ("post", "put") else {}))
    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_LOGGED_IN"


def test_list_filters_and_shows_languages(officer_client):
    listed = officer_client.get("/api/staff/faq", params={"category": "dormitory"}).json()
    assert [item["faq_id"] for item in listed["items"]] == ["faq-022", "faq-023", "faq-049"]
    assert listed["items"][0]["languages"] == ["en", "ru", "kk"]
    assert "dormitory" in listed["categories"]

    found = officer_client.get("/api/staff/faq", params={"q": "общежит"}).json()["items"]
    assert "faq-022" in [item["faq_id"] for item in found]
    assert officer_client.get("/api/staff/faq", params={"status": "draft"}).json()["items"] == []
    assert officer_client.get("/api/staff/faq/faq-999").status_code == 404


def test_edited_answer_is_used_by_the_assistant_at_once(officer_client):
    question = "How much does the dormitory cost?"
    assert "552,500" in _ask(officer_client, question)["answer"]
    item = officer_client.get("/api/staff/faq/faq-022").json()
    new_answer = "For the 2026–2027 academic year, Student Residence Accommodation costs 600,000 KZT per year."

    saved = officer_client.put("/api/staff/faq/faq-022", json={**item, "answer": new_answer})

    assert saved.status_code == 200
    assert saved.json()["updated_by"] == "Aigerim"
    assert saved.json()["last_update"] == date.today().isoformat()
    answer = _ask(officer_client, question)
    assert "600,000" in answer["answer"] and "552,500" not in answer["answer"]
    assert answer["sources"][0]["faq_id"] == "faq-022"


def test_new_item_is_a_draft_until_published(officer_client, assistant_session):
    last = max(int(faq_id.split("-")[1]) for faq_id in assistant_session.scalars(select(FaqRecord.faq_id)))
    created = officer_client.post("/api/staff/faq", json=NEW_ITEM)

    assert created.status_code == 201
    body = created.json()
    new_id = f"faq-{last + 1:03d}"
    assert (body["faq_id"], body["status"]) == (new_id, "draft")
    assert _indexed(assistant_session, new_id) == []
    assert "bicycle" not in _ask(officer_client, "Can I keep a bicycle at the dormitory?")["answer"].lower()

    assert officer_client.post(f"/api/staff/faq/{new_id}/publish").json()["status"] == "published"
    assert _indexed(assistant_session, new_id) == ["en"]
    answer = _ask(officer_client, "Can I keep a bicycle at the dormitory?")
    assert "bicycle room" in answer["answer"]

    assert officer_client.post(f"/api/staff/faq/{new_id}/unpublish").json()["status"] == "draft"
    assert _indexed(assistant_session, new_id) == []


def test_retired_item_is_no_longer_found_or_suggested(officer_client, assistant_session):
    assert "faq-001" in [result.faq_item.faq_id for result in search(assistant_session, STARTERS[0])]

    retired = officer_client.post("/api/staff/faq/faq-001/retire")

    assert retired.json()["status"] == "retired"
    assert _indexed(assistant_session, "faq-001") == []
    assert "faq-001" not in [result.faq_item.faq_id for result in search(assistant_session, STARTERS[0])]
    assert STARTERS[0] not in suggest(assistant_session, "fresh-session")
    assert "faq-001" in [item["faq_id"] for item in officer_client.get("/api/staff/faq", params={"status": "retired"}).json()["items"]]


def test_translations_are_indexed_in_their_language(officer_client, assistant_session):
    created = officer_client.post(
        "/api/staff/faq",
        json={
            **NEW_ITEM,
            "question_ru": "Можно ли хранить велосипед в общежитии?",
            "answer_ru": "Да, в Студенческом доме есть велосипедная комната на первом этаже.",
            "source_link_ru": "https://sdu.edu.kz/ru/student-house/",
        },
    ).json()
    officer_client.post(f"/api/staff/faq/{created['faq_id']}/publish")
    assert _indexed(assistant_session, created["faq_id"]) == ["en", "ru"]


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"source_link": "http://sdu.edu.kz/page"}, "source_link"),
        ({"source_link": ""}, "source_link"),
        ({"question": "   "}, "question"),
        ({"question_ru": "Вопрос без ответа?"}, "ru version"),
        ({"degrees": ["school"]}, "degrees"),
        ({"category": "Dormitory!"}, "category"),
    ],
)
def test_invalid_items_are_rejected(officer_client, change, field):
    response = officer_client.post("/api/staff/faq", json={**NEW_ITEM, **change})
    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_REQUEST"
    assert field.split()[0] in response.json()["message"]


def _indexed(session, faq_id):
    return sorted(session.scalars(select(FaqEmbeddingRecord.language).where(FaqEmbeddingRecord.faq_id == faq_id)))
