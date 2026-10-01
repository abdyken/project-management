"""Reading and writing the chat turns of a session (US11)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.conversation.models import ASSISTANT, RETENTION_DAYS, ROLES, USER, ChatTurn

# How many of the latest turns are passed to the answer service as context.
CONTEXT_TURNS = 6


def record_turn(
    session: Session,
    session_id: str,
    role: str,
    text: str,
    sources: list[dict[str, Any]] | None = None,
) -> ChatTurn:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}, got {role!r}")
    turn = ChatTurn(session_id=session_id, role=role, text=text, sources=sources)
    session.add(turn)
    session.commit()
    return turn


def record_question(session: Session, session_id: str, question: str) -> ChatTurn:
    return record_turn(session, session_id, USER, question)


def record_answer(
    session: Session, session_id: str, answer: str, sources: list[dict[str, Any]] | None = None
) -> ChatTurn:
    return record_turn(session, session_id, ASSISTANT, answer, sources)


def recent_turns(session: Session, session_id: str, limit: int = CONTEXT_TURNS) -> list[ChatTurn]:
    """The last `limit` turns of this session only, oldest first.

    Scoped by session_id, so one applicant's context can never reach another's
    answer (US11QATest fail case).
    """
    latest = session.scalars(
        select(ChatTurn)
        .where(ChatTurn.session_id == session_id)
        .order_by(ChatTurn.created_at.desc(), ChatTurn.id.desc())
        .limit(limit)
    ).all()
    return list(reversed(latest))


def delete_expired_turns(session: Session, retention_days: int = RETENTION_DAYS) -> int:
    """Delete turns older than the retention window. Returns how many were deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = session.execute(delete(ChatTurn).where(ChatTurn.created_at < cutoff)).rowcount
    session.commit()
    return deleted
