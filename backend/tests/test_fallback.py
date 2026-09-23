from __future__ import annotations

from app.assistant.fallback import build_fallback_response
from app.config import Settings


def test_fallback_response_has_no_faq_reference():
    settings = Settings(admissions_office_contact="office@example.com")
    response = build_fallback_response(settings, similarity_score=0.1)

    assert response.faq_id is None
    assert response.source_link is None
    assert response.answer.startswith("I could not find this information in the official FAQ.")
    assert "office@example.com" in response.answer
    assert response.similarity_score == 0.1


def test_fallback_message_is_fixed_not_generated():
    settings = Settings()
    first = build_fallback_response(settings, similarity_score=0.2)
    second = build_fallback_response(settings, similarity_score=0.3)
    assert first.answer == second.answer
