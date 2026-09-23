from __future__ import annotations

from app.assistant.schemas import AskResponse
from app.config import Settings

FALLBACK_TEMPLATE = (
    "I could not find this in our official FAQ. "
    "Please contact the admissions office for an accurate answer: {contact}"
)


def build_fallback_response(settings: Settings, similarity_score: float) -> AskResponse:
    return AskResponse(
        answer=FALLBACK_TEMPLATE.format(contact=settings.admissions_office_contact),
        source_link=None,
        faq_id=None,
        similarity_score=similarity_score,
    )
