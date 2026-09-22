"""T3.4 DoD: out-of-scope questions always get the fallback, never an
invented answer."""
from __future__ import annotations

from app.assistant.fallback import build_fallback_response
from app.config import Settings


def test_fallback_response_has_no_faq_reference():
    settings = Settings(admissions_office_contact="office@example.com")
    response = build_fallback_response(settings, similarity_score=0.1)

    assert response.faq_id is None
    assert response.source_link is None
    assert "office@example.com" in response.answer
    assert response.similarity_score == 0.1


def test_fallback_message_is_fixed_not_generated():
    """The whole point of T3.4: this path must be a template, not an LLM
    call, so it can never invent an admission rule."""
    settings = Settings()
    first = build_fallback_response(settings, similarity_score=0.2)
    second = build_fallback_response(settings, similarity_score=0.3)
    # same template regardless of score/input — deterministic, not generated
    assert first.answer == second.answer
