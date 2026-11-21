"""Site search: GET /api/assistant/search returns published FAQ answers as written."""
from __future__ import annotations

from contextlib import nullcontext

from fastapi.testclient import TestClient

from app.db import get_session_factory
from app.main import app


def _search(session, **params):
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(session)
    try:
        return TestClient(app).get("/api/assistant/search", params=params)
    finally:
        app.dependency_overrides.clear()


def test_a_question_finds_its_faq_answer(assistant_session, faq_items):
    item = next(item for item in faq_items if item.faq_id == "faq-002")
    response = _search(assistant_session, q=item.question)
    assert response.status_code == 200
    results = response.json()["results"]
    assert results and results[0]["faq_id"] == "faq-002"
    assert results[0]["answer"] == item.answer
    assert set(results[0]) == {"faq_id", "question", "answer", "category", "source_link"}


def test_results_come_in_the_requested_language(assistant_session, faq_items):
    item = next(item for item in faq_items if item.faq_id == "faq-002")
    results = _search(assistant_session, q=item.question_kk, lang="kk").json()["results"]
    assert results and results[0]["faq_id"] == "faq-002"
    assert results[0]["question"] == item.question_kk
    assert results[0]["answer"] == item.answer_kk


def test_at_most_five_results(assistant_session):
    assert len(_search(assistant_session, q="bachelor documents deadline").json()["results"]) <= 5


def test_query_is_validated(assistant_session):
    assert _search(assistant_session, q="a").status_code == 422
    assert _search(assistant_session, q="x" * 201).status_code == 422
    assert _search(assistant_session, q="deadline", lang="de").status_code == 422
