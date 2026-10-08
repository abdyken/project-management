"""US11 T11.2 / US11QATest: follow-up questions through POST /api/assistant/ask."""
from __future__ import annotations

from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.conversation.models import ASSISTANT, USER, ChatTurn
from app.db import get_session_factory
from app.main import app

LOCAL = "Which documents do I need for 6B06102 as a local applicant?"
FOLLOW_UP = "and as an international applicant?"


@pytest.fixture
def client(assistant_session):
    app.dependency_overrides[get_session_factory] = lambda: lambda: nullcontext(assistant_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def ask(client: TestClient, question: str, session_id: str) -> str:
    response = client.post("/api/assistant/ask", json={"question": question, "session_id": session_id})
    assert response.status_code == 200
    return response.json()["answer"]


def test_follow_up_returns_the_international_list_for_the_same_program(client):
    """US11QATest Pass 1."""
    local = ask(client, LOCAL, "s1")
    follow_up = ask(client, FOLLOW_UP, "s1")
    direct = ask(client, "Which documents do I need for 6B06102 as an international applicant?", "s2")

    assert "6B06102" in local and "local applicant" in local
    assert "6B06102" in follow_up and "international applicant" in follow_up
    assert follow_up == direct


def test_new_conversation_no_longer_uses_the_earlier_program(client):
    """US11QATest Pass 2: the widget's New conversation starts a new session id."""
    ask(client, LOCAL, "old-session")

    answer = ask(client, FOLLOW_UP, "new-session")

    assert "6B06102" not in answer


def test_follow_up_never_uses_another_sessions_context(client):
    """US11QATest Fail case: another applicant's program must not leak in."""
    ask(client, LOCAL, "applicant-a")

    answer = ask(client, FOLLOW_UP, "applicant-b")

    assert "6B06102" not in answer
    assert "Required documents" not in answer


def test_each_question_and_answer_is_stored_for_its_session(client, assistant_session):
    answer = ask(client, LOCAL, "s1")

    turns = assistant_session.scalars(select(ChatTurn).where(ChatTurn.session_id == "s1").order_by(ChatTurn.id)).all()

    assert [(turn.role, turn.text) for turn in turns] == [(USER, LOCAL), (ASSISTANT, answer)]


def test_stored_question_is_what_the_applicant_typed(client, assistant_session):
    ask(client, LOCAL, "s1")
    ask(client, FOLLOW_UP, "s1")

    questions = assistant_session.scalars(
        select(ChatTurn.text).where(ChatTurn.session_id == "s1", ChatTurn.role == USER).order_by(ChatTurn.id)
    ).all()

    assert questions == [LOCAL, FOLLOW_UP]


def test_faq_answer_sources_are_stored(client, assistant_session, faq_items):
    item = faq_items[0]
    body = client.post("/api/assistant/ask", json={"question": item.question, "session_id": "s1"}).json()

    answer_turn = assistant_session.scalars(
        select(ChatTurn).where(ChatTurn.session_id == "s1", ChatTurn.role == ASSISTANT)
    ).one()

    assert answer_turn.sources == [{"faq_id": item.faq_id, "question": item.question, "link": item.source_link, "title": item.question}]
    assert body["sources"] == answer_turn.sources
    assert body["answer_id"] == str(answer_turn.id)


def test_unrelated_question_after_a_program_question_is_answered_on_its_own(client):
    ask(client, LOCAL, "s1")

    answer = ask(client, "How much does the dormitory cost?", "s1")

    assert "6B06102" not in answer
    assert "per ECTS credit" not in answer


def sources(client: TestClient, question: str, session_id: str) -> list[str | None]:
    response = client.post("/api/assistant/ask", json={"question": question, "session_id": session_id})
    return [source["faq_id"] for source in response.json()["sources"]]


def test_faq_follow_up_is_answered_in_the_topic_of_the_previous_answer(client):
    assert sources(client, "How much does the dormitory cost?", "s1") == ["faq-022"]

    assert sources(client, "And when do I have to apply for it?", "s1") == ["faq-023"]


def test_faq_topic_does_not_reach_an_unrelated_question_or_another_session(client):
    sources(client, "How much does the dormitory cost?", "s1")

    assert sources(client, "What is the capital of France?", "s1") == []
    assert sources(client, "And when do I have to apply for it?", "s2") != ["faq-023"]


def test_timed_out_answer_is_not_stored(client, assistant_session, monkeypatch):
    import time

    from app.assistant.service import AssistantService

    monkeypatch.setenv("ASSISTANT_TIMEOUT_SECONDS", "0.1")
    monkeypatch.setattr(AssistantService, "answer", lambda self, question, session_id: time.sleep(0.3) or None)

    response = client.post("/api/assistant/ask", json={"question": "Slow?", "session_id": "slow"})
    time.sleep(0.4)

    assert response.status_code == 504
    assert assistant_session.scalars(select(ChatTurn).where(ChatTurn.session_id == "slow")).all() == []
