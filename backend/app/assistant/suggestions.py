"""Starter and follow-up questions for the chat widget (US14).

The widget shows four of these before the first turn and up to three after an
answer. Each string is an official FAQ question, so sending it back to /ask
returns that item and its source.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.conversation.models import USER, ChatTurn

STARTERS = [
    "What are the application deadlines for international applicants?",
    "Is the UNT required for admission to bachelor's programmes?",
    "What English level do I need for bachelor's admission?",
    "What documents do I need for tuition-based (paid) bachelor's enrollment?",
]

FOLLOW_UPS = [
    "How do I apply online for a bachelor's programme?",
    "What documents do international applicants upload with the online application?",
    "Do international applicants have to take an English test or an interview?",
    "How are tuition fees calculated at SDU?",
    "How can I contact the SDU Admissions Office by email or phone?",
    *STARTERS,
]

STARTER_LIMIT = 4
FOLLOW_UP_LIMIT = 3


def suggest(session: Session, session_id: str) -> list[str]:
    asked = set(
        session.scalars(select(ChatTurn.text).where(ChatTurn.session_id == session_id, ChatTurn.role == USER)).all()
    )
    asked = {text.strip() for text in asked}
    if not asked:
        return list(STARTERS[:STARTER_LIMIT])
    return [question for question in FOLLOW_UPS if question.strip() not in asked][:FOLLOW_UP_LIMIT]
