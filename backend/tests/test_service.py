from __future__ import annotations

import pytest
from sqlalchemy import select

from app.assistant.fallback import FALLBACK_TEMPLATE
from app.assistant.service import AssistantService
from app.checklist.service import MISSING_REQUIREMENTS_WARNING, get_requirements
from app.config import get_settings
from app.followups.models import MISSING_DOCUMENTS, UNANSWERED_QUESTION, AdmissionsFollowup


@pytest.fixture
def service(assistant_session) -> AssistantService:
    return AssistantService(assistant_session, get_settings())


def followups(session) -> list[tuple[str, str | None]]:
    return [(f.kind, f.program_id) for f in session.scalars(select(AdmissionsFollowup))]


def test_faq_question_returns_its_item_and_source_link(service, faq_items):
    for item in faq_items:
        response = service.answer(item.question, "s1")
        assert response.faq_id == item.faq_id
        assert response.source_link == item.source_link
        assert response.answer == item.answer


def test_out_of_scope_question_returns_fallback_and_is_logged(service, assistant_session):
    response = service.answer("What is the capital of France?", "s1")
    assert response.faq_id is None
    assert response.source_link is None
    assert response.answer == FALLBACK_TEMPLATE.format(contact=get_settings().admissions_office_contact)
    assert followups(assistant_session) == [(UNANSWERED_QUESTION, None)]


@pytest.mark.parametrize("applicant_type", ["local", "international"])
def test_document_answer_matches_the_checklist(service, assistant_session, applicant_type):
    response = service.answer(
        f"What documents do I need for Computer Science as a {applicant_type} applicant?", "s1"
    )
    requirements = get_requirements(assistant_session, "6B06102", applicant_type)
    assert response.answer.startswith(f"Required documents for Computer Science ({applicant_type} applicant)")
    lines = response.answer.splitlines()[1:]
    assert len(lines) == len(requirements)
    for line, requirement in zip(lines, requirements, strict=True):
        assert line.startswith(f"- {requirement.name} ({requirement.document_format}")
    assert response.similarity_score is None


def test_document_question_without_applicant_type_asks_for_it(service):
    response = service.answer("What documents do I need for Computer Science?", "s1")
    assert "local and international" in response.answer
    assert not response.answer.startswith("Required documents")


def test_program_title_is_matched_case_insensitively(service):
    response = service.answer("Which documents do I need for applied law as a foreign student?", "s1")
    assert response.answer.startswith("Required documents for Applied Law (international applicant)")


def test_long_program_title_is_matched_by_most_of_its_words(service):
    response = service.answer("Which documents do I need for kazakh literature as a local applicant?", "s1")
    assert response.answer.startswith("Required documents for Kazakh Language and Literature (local applicant)")


def test_one_shared_word_does_not_select_a_program(service):
    response = service.answer("What do I need to submit for doctoral studies?", "s1")
    assert "Translation Studies" not in response.answer


def test_degree_word_picks_between_programs_with_the_same_title(service, assistant_session):
    response = service.answer("Which documents do I need for a master's in Information Systems as a local applicant?", "s1")
    master_documents = get_requirements(assistant_session, "7M06101", "local")
    assert response.answer.startswith("Required documents for Information Systems (local applicant)")
    assert response.answer.splitlines()[1].startswith(f"- {master_documents[0].name}")


def test_international_in_program_title_is_not_read_as_applicant_type(service):
    response = service.answer("Documents for International Relations for a local applicant?", "s1")
    assert response.answer.startswith("Required documents for International Relations (local applicant)")


def test_applicant_words_do_not_select_a_program(service, faq_items):
    item = next(item for item in faq_items if item.faq_id == "faq-007")
    response = service.answer(item.question, "s1")
    assert response.faq_id == "faq-007"


def test_russian_applicant_type_is_recognised(service):
    response = service.answer("Какие документы нужны на Computer Science для иностранцев?", "s1")
    assert response.answer.startswith("Required documents for Computer Science (international applicant)")


def test_program_without_requirements_warns_once_and_is_logged(service, assistant_session):
    response = service.answer("What documents do I need for Management as an international applicant?", "s1")
    assert response.answer == f"{MISSING_REQUIREMENTS_WARNING} {get_settings().admissions_office_contact}"
    assert response.answer.lower().count("contact the admissions office") == 1
    assert followups(assistant_session) == [(MISSING_DOCUMENTS, "7M04115")]


def test_document_question_for_unknown_program_falls_back_to_faq_search(service):
    response = service.answer("What documents do I need for Astrophysics?", "s1")
    assert not response.answer.startswith("Required documents")
