from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assistant.schemas import Language
from app.conversation.models import USER, ChatTurn
from app.faq.service import published_by_id

STARTER_IDS = ["faq-001", "faq-011", "faq-014", "faq-005"]
FOLLOW_UP_IDS = ["faq-003", "faq-006", "faq-012", "faq-017", "faq-035", "faq-022", "faq-036", "faq-049"]

STARTERS = [
    "What are the application deadlines for international applicants?",
    "Is the UNT required for admission to bachelor's programmes?",
    "What English level do I need for bachelor's admission?",
    "What documents do I need for tuition-based (paid) bachelor's enrollment?",
]

STARTER_LIMIT = 4
FOLLOW_UP_LIMIT = 3


def _questions(session: Session, faq_ids: list[str], language: Language) -> list[str]:
    # Only published items (US20): a retired or draft item is never suggested.
    faq = published_by_id(session, faq_ids)
    return [faq[faq_id].localized(language).question for faq_id in faq_ids if faq_id in faq and faq[faq_id].has(language)]


def suggest(session: Session, session_id: str, language: Language = "en") -> list[str]:
    asked = {
        text.strip()
        for text in session.scalars(
            select(ChatTurn.text).where(ChatTurn.session_id == session_id, ChatTurn.role == USER)
        ).all()
    }
    candidates = list(dict.fromkeys(_questions(session, STARTER_IDS + FOLLOW_UP_IDS, language)))
    if not asked:
        return candidates[:STARTER_LIMIT]
    return [question for question in candidates if question.strip() not in asked][:FOLLOW_UP_LIMIT]
