from __future__ import annotations

from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assistant.retrieval import load_faq_base
from app.assistant.schemas import FaqItem, Language
from app.config import get_settings
from app.conversation.models import USER, ChatTurn

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


@lru_cache(maxsize=4)
def _faq_by_id(path: str) -> dict[str, FaqItem]:
    return {item.faq_id: item for item in load_faq_base(path)}


def _questions(faq_ids: list[str], language: Language) -> list[str]:
    faq = _faq_by_id(get_settings().faq_data_path)
    return [faq[faq_id].localized(language).question for faq_id in faq_ids if faq_id in faq and faq[faq_id].has(language)]


def suggest(session: Session, session_id: str, language: Language = "en") -> list[str]:
    asked = {
        text.strip()
        for text in session.scalars(
            select(ChatTurn.text).where(ChatTurn.session_id == session_id, ChatTurn.role == USER)
        ).all()
    }
    candidates = list(dict.fromkeys(_questions(STARTER_IDS + FOLLOW_UP_IDS, language)))
    if not asked:
        return candidates[:STARTER_LIMIT]
    return [question for question in candidates if question.strip() not in asked][:FOLLOW_UP_LIMIT]
