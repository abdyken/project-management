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
    assert response.answer.startswith(
        f"Required documents for Computer Science (bachelor, 6B06102), {applicant_type} applicant"
    )
    lines = response.answer.splitlines()[1:]
    assert len(lines) == len(requirements)
    for line, requirement in zip(lines, requirements, strict=True):
        assert line.startswith(f"- {requirement.name} ({requirement.document_format}")
    assert response.similarity_score is None


def test_document_question_without_applicant_type_asks_for_it(service):
    response = service.answer("What documents do I need for Computer Science?", "s1")
    assert "local and international" in response.answer
    assert "Computer Science (6B06102)" in response.answer
    assert not response.answer.startswith("Required documents")


def test_program_title_is_matched_case_insensitively(service):
    response = service.answer("Which documents do I need for applied law as a foreign student?", "s1")
    assert response.answer.startswith("Required documents for Applied Law (bachelor, 6B04201), international applicant")


def test_long_program_title_is_matched_by_most_of_its_words(service):
    response = service.answer("Which documents do I need for kazakh literature as a local applicant?", "s1")
    assert response.answer.startswith(
        "Required documents for Kazakh Language and Literature (bachelor, 6B01701), local applicant"
    )


def test_one_shared_word_does_not_select_a_program(service):
    response = service.answer("What do I need to submit for doctoral studies?", "s1")
    assert "Translation Studies" not in response.answer


def test_degree_word_picks_between_programs_with_the_same_title(service):
    response = service.answer("Which documents do I need for a master's in Information Systems as a local applicant?", "s1")
    assert response.answer.startswith("Required documents for Information Systems (master, 7M06101), local applicant")


def test_program_code_picks_the_program(service):
    response = service.answer("Which documents do I need for Information Systems (7M06101) as a local applicant?", "s1")
    assert response.answer.startswith("Required documents for Information Systems (master, 7M06101), local applicant")


def test_shared_title_without_degree_asks_which_program(service):
    response = service.answer("Which documents do I need for Information Systems as a local applicant?", "s1")
    assert response.answer.startswith("Your question matches several programs:")
    assert "Information Systems (bachelor, 6B06101)" in response.answer
    assert "Information Systems (master, 7M06101)" in response.answer
    assert response.faq_id is None


def test_degree_word_filters_a_single_title_match(service):
    response = service.answer("What documents do I need for a master's in Computer Science as a local applicant?", "s1")
    assert "6B06102" not in response.answer


def test_international_in_program_title_is_not_read_as_applicant_type(service):
    response = service.answer("Documents for International Relations for a local applicant?", "s1")
    assert response.answer.startswith("Required documents for International Relations (bachelor, 6B03101), local applicant")


def test_international_relations_for_international_applicants(service):
    response = service.answer("Which documents do I need for International Relations as an international applicant?", "s1")
    assert response.answer.startswith(
        "Required documents for International Relations (bachelor, 6B03101), international applicant"
    )


def test_citizenship_alone_does_not_mean_local(service):
    response = service.answer("Which documents do I need for Computer Science as a citizen of Uzbekistan?", "s1")
    assert "local and international" in response.answer


def test_applicant_words_do_not_select_a_program(service, faq_items):
    item = next(item for item in faq_items if item.faq_id == "faq-007")
    response = service.answer(item.question, "s1")
    assert response.faq_id == "faq-007"


@pytest.mark.parametrize(
    "question",
    [
        "Master degree deadline 2026",
        "What is the application deadline for the master program?",
        "Which documents do I need for a master program as an international applicant?",
    ],
)
def test_faq_item_for_another_degree_is_not_used(service, assistant_session, question):
    response = service.answer(question, "s1")
    assert response.faq_id is None
    assert followups(assistant_session) == [(UNANSWERED_QUESTION, None)]


def test_same_topic_item_for_the_asked_applicant_type_is_used(service):
    response = service.answer("When is the application deadline for local applicants?", "s1")
    assert response.faq_id == "faq-002"


def test_local_deadline_question_gets_the_local_deadlines(service):
    response = service.answer("Until when can citizens of Kazakhstan apply for a bachelor's program?", "s1")
    assert response.faq_id == "faq-002"


def test_russian_applicant_type_is_recognised(service):
    response = service.answer("Какие документы нужны на Computer Science для иностранцев?", "s1")
    assert response.answer.startswith("Required documents for Computer Science (bachelor, 6B06102), international applicant")


def test_program_without_requirements_warns_once_and_is_logged(service, assistant_session):
    response = service.answer("What documents do I need for Management as an international applicant?", "s1")
    assert response.answer == f"{MISSING_REQUIREMENTS_WARNING} {get_settings().admissions_office_contact}"
    assert response.answer.lower().count("contact the admissions office") == 1
    assert followups(assistant_session) == [(MISSING_DOCUMENTS, "7M04115")]


def test_document_question_for_unknown_program_falls_back_to_faq_search(service):
    response = service.answer("What documents do I need for Astrophysics?", "s1")
    assert not response.answer.startswith("Required documents")


def test_tuition_answer_uses_the_catalogue_figures(service):
    response = service.answer("How much is tuition for Computer Science?", "s1")
    assert "33,000 KZT (about USD 90) per ECTS credit" in response.answer
    assert response.source_link == "https://sdu.edu.kz/en/computer-science-3/"
    assert response.faq_id is None
    assert response.similarity_score is None


def test_tuition_question_with_a_degree_picks_that_program(service):
    response = service.answer("How much does a master's in Information Systems cost?", "s1")
    assert response.answer.startswith("Information Systems (master, 7M06101) costs 27,000 KZT")


def test_tuition_question_for_a_shared_title_asks_which_program(service):
    response = service.answer("What is the price of Information Systems?", "s1")
    assert "matches several programs" in response.answer
    assert "How much is tuition for Information Systems (6B06101)?" in response.answer


def test_tuition_without_a_published_fee_points_to_the_office(service, assistant_session):
    from app.catalogue.models import Program

    program = assistant_session.get(Program, "6B06102")
    program.tuition_per_ects_kzt = None
    program.tuition_per_ects_usd = None
    assistant_session.flush()

    response = service.answer("How much is tuition for Computer Science?", "s1")
    assert response.answer == (
        "The catalogue does not publish a tuition fee for Computer Science (bachelor, 6B06102). "
        f"{get_settings().admissions_office_contact}"
    )
    assert response.source_link is None


def test_tuition_question_without_a_program_still_uses_the_faq(service):
    response = service.answer("How are tuition fees calculated at SDU?", "s1")
    assert response.faq_id == "faq-017"


def test_dormitory_cost_question_is_not_answered_from_the_catalogue(service):
    response = service.answer("How much does the dormitory cost?", "s1")
    assert response.faq_id == "faq-022"
