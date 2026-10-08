from __future__ import annotations

from app.assistant.schemas import Answer, Language
from app.assistant.texts import contact, text
from app.config import Settings

FALLBACK_TEMPLATE = text("en", "fallback")


def build_fallback_response(settings: Settings, similarity_score: float | None, language: Language = "en") -> Answer:
    return Answer(
        answer=text(language, "fallback", contact=contact(language, settings.admissions_office_contact)),
        source_link=None,
        faq_id=None,
        similarity_score=similarity_score,
    )
