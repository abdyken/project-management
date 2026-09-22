"""T3.3 (answer endpoint logic) + T3.6 (document-checklist questions)."""
from __future__ import annotations

import pytest

from app.assistant.catalog_client import FileCatalogClient
from app.assistant.checklist_client import FileChecklistClient
from app.assistant.providers import MockEmbeddingProvider
from app.assistant.retrieval import RetrievalIndex, load_faq_base
from app.assistant.service import AssistantService
from app.config import Settings

DATA_DIR = "app/data"


@pytest.fixture
def service() -> AssistantService:
    settings = Settings(similarity_threshold=0.72)
    faq_items = load_faq_base(f"{DATA_DIR}/faq_sample.json")
    index = RetrievalIndex.build(faq_items, MockEmbeddingProvider())
    return AssistantService(
        settings=settings,
        index=index,
        embedder=MockEmbeddingProvider(),
        catalog_client=FileCatalogClient(f"{DATA_DIR}/programs_sample.json"),
        checklist_client=FileChecklistClient(f"{DATA_DIR}/checklist_sample.json"),
    )


def test_faq_question_returns_matching_source_link(service: AssistantService):
    response = service.answer("What is the deadline to apply for the Fall intake?", session_id="s1")
    assert response.faq_id == "faq-001"
    assert response.source_link == "https://university.example/admissions/deadlines"


def test_out_of_scope_question_returns_fallback(service: AssistantService):
    response = service.answer("What is the capital of France?", session_id="s1")
    assert response.faq_id is None
    assert "contact" in response.answer.lower()


def test_document_question_returns_matching_checklist(service: AssistantService):
    response = service.answer("What documents do I need for Computer Science?", session_id="s1")
    assert "Computer Science" in response.answer
    assert "Diploma" in response.answer
    assert "Passport copy" in response.answer


def test_document_question_for_program_without_requirements_warns(service: AssistantService):
    response = service.answer("What documents do I need for Architecture?", session_id="s1")
    assert "No document requirements" in response.answer
    assert "admissions office" in response.answer.lower() or "contact" in response.answer.lower()


def test_document_question_unrecognised_program_falls_back_to_faq_search(service: AssistantService):
    # "documents" keyword present but no known program name -> falls through
    # to normal FAQ retrieval instead of crashing.
    response = service.answer("What documents do I need in general?", session_id="s1")
    assert response is not None
