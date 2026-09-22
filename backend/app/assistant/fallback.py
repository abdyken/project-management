"""T3.4 — Below-threshold fallback.

Deliberately a pure function with **no** provider/LLM call: when the
retrieval score is below the configured threshold we must guarantee no
invented admission rule can appear in the answer, and the cheapest way to
guarantee that is to never call a generator for this path at all.
"""
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
