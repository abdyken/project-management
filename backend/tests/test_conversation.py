"""US11 T11.1: chat turn storage, session isolation and 30-day retention."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, select

from app.conversation.models import ASSISTANT, RETENTION_DAYS, USER, ChatTurn
from app.conversation.service import (
    CONTEXT_TURNS,
    delete_expired_turns,
    record_answer,
    record_question,
    record_turn,
    recent_turns,
)


@pytest.fixture
def conversation_session(db_session):
    db_session.execute(delete(ChatTurn))
    return db_session


def test_question_and_answer_are_stored(conversation_session):
    record_question(conversation_session, "s1", "Which documents do I need for 6B06102?")
    record_answer(
        conversation_session,
        "s1",
        "You need a passport and a school certificate.",
        [{"faq_id": "faq-001", "question": "Which documents?", "link": "https://sdu.edu.kz/faq"}],
    )

    turns = recent_turns(conversation_session, "s1")

    assert [(turn.role, turn.text) for turn in turns] == [
        (USER, "Which documents do I need for 6B06102?"),
        (ASSISTANT, "You need a passport and a school certificate."),
    ]
    assert turns[0].sources is None
    assert turns[1].sources == [{"faq_id": "faq-001", "question": "Which documents?", "link": "https://sdu.edu.kz/faq"}]
    assert turns[0].created_at.tzinfo is not None


def test_only_the_last_six_turns_are_returned_oldest_first(conversation_session):
    for number in range(1, 11):
        record_question(conversation_session, "s1", f"question {number}")

    turns = recent_turns(conversation_session, "s1")

    assert CONTEXT_TURNS == 6
    assert [turn.text for turn in turns] == [f"question {number}" for number in range(5, 11)]


def test_limit_can_be_overridden(conversation_session):
    for number in range(1, 5):
        record_question(conversation_session, "s1", f"question {number}")

    assert [turn.text for turn in recent_turns(conversation_session, "s1", limit=2)] == ["question 3", "question 4"]


def test_turns_of_another_session_are_never_returned(conversation_session):
    record_question(conversation_session, "other-applicant", "Which documents for 6B06101?")
    record_answer(conversation_session, "other-applicant", "Passport and diploma.")
    record_question(conversation_session, "s1", "and as an international applicant?")

    turns = recent_turns(conversation_session, "s1")

    assert [turn.text for turn in turns] == ["and as an international applicant?"]
    assert all(turn.session_id == "s1" for turn in turns)


def test_a_new_session_id_starts_an_empty_context(conversation_session):
    record_question(conversation_session, "s1", "Which documents do I need for 6B06102?")

    assert recent_turns(conversation_session, "s2") == []


def test_unknown_role_is_rejected(conversation_session):
    with pytest.raises(ValueError, match="role must be one of"):
        record_turn(conversation_session, "s1", "system", "not allowed")

    assert conversation_session.scalars(select(ChatTurn)).all() == []


def test_turns_older_than_the_retention_window_are_deleted(conversation_session):
    old = record_question(conversation_session, "s1", "old question")
    recent = record_question(conversation_session, "s1", "recent question")
    old.created_at = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS, minutes=1)
    conversation_session.commit()

    deleted = delete_expired_turns(conversation_session)

    assert deleted == 1
    assert [turn.text for turn in conversation_session.scalars(select(ChatTurn))] == ["recent question"]
    assert conversation_session.get(ChatTurn, recent.id) is not None


def test_retention_window_is_configurable(conversation_session):
    turn = record_question(conversation_session, "s1", "two days old")
    turn.created_at = datetime.now(timezone.utc) - timedelta(days=2)
    conversation_session.commit()

    assert delete_expired_turns(conversation_session, retention_days=30) == 0
    assert delete_expired_turns(conversation_session, retention_days=1) == 1


def test_chat_turn_stores_no_applicant_identity(db_engine):
    """Privacy constraint: the table holds the anonymous session id and nothing else
    that identifies an applicant."""
    columns = {column.name for column in ChatTurn.__table__.columns}

    assert columns == {"id", "session_id", "role", "text", "sources", "created_at"}
