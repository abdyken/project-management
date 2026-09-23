from __future__ import annotations

import pytest

from app.assistant.service import AssistantService
from app.checklist.service import MISSING_REQUIREMENTS_WARNING
from app.config import get_settings


@pytest.fixture
def service(assistant_session) -> AssistantService:
    return AssistantService(assistant_session, get_settings())


def test_faq_question_returns_its_item_and_source_link(service, faq_items):
    for item in faq_items:
        response = service.answer(item.question)
        assert response.faq_id == item.faq_id
        assert response.source_link == item.source_link
        assert response.answer == item.answer


def test_out_of_scope_question_returns_fallback(service):
    response = service.answer("What is the capital of France?")
    assert response.faq_id is None
    assert response.source_link is None
    assert "contact" in response.answer.lower()


def test_document_question_returns_the_checklist(service):
    response = service.answer("What documents do I need for Computer Science?")
    assert response.answer.startswith("Required documents for Computer Science")
    assert response.faq_id is None


def test_document_question_for_program_without_requirements_warns(service):
    response = service.answer("What documents do I need for Management?")
    assert MISSING_REQUIREMENTS_WARNING in response.answer
    assert get_settings().admissions_office_contact in response.answer


def test_document_question_for_unknown_program_falls_back_to_faq_search(service):
    response = service.answer("What documents do I need for Astrophysics?")
    assert response is not None
