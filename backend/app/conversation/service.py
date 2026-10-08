from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.assistant.models import FaqEmbeddingRecord
from app.conversation.models import ASSISTANT, RETENTION_DAYS, ROLES, USER, ChatTurn

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
    latest = session.scalars(
        select(ChatTurn)
        .where(ChatTurn.session_id == session_id)
        .order_by(ChatTurn.created_at.desc(), ChatTurn.id.desc())
        .limit(limit)
    ).all()
    return list(reversed(latest))


def delete_expired_turns(session: Session, retention_days: int = RETENTION_DAYS) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = session.execute(delete(ChatTurn).where(ChatTurn.created_at < cutoff)).rowcount
    session.commit()
    return deleted


def faq_topic(session: Session, history: list[ChatTurn]) -> str | None:
    last_answer = next((turn for turn in reversed(history) if turn.role == ASSISTANT), None)
    if last_answer is None:
        return None
    faq_ids = [source["faq_id"] for source in last_answer.sources or [] if source.get("faq_id")]
    if not faq_ids:
        return None
    return session.scalar(select(FaqEmbeddingRecord.category).where(FaqEmbeddingRecord.faq_id == faq_ids[0]))
