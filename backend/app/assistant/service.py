"""T3.3 — Answer service endpoint (core logic).
T3.4 — below-threshold fallback is delegated to app.assistant.fallback.
T3.6 — document-checklist questions are detected and routed separately.

Kept transport-agnostic (no FastAPI/HTTP here) so it is easy to unit test;
app/assistant/router.py wraps this in the HTTP contract from T3.5.
"""
from __future__ import annotations

import re

from app.assistant.catalog_client import CatalogClient
from app.assistant.checklist_client import ChecklistClient
from app.assistant.fallback import build_fallback_response
from app.assistant.index_factory import SearchableIndex
from app.assistant.intents import is_document_question, resolve_program
from app.assistant.providers import EmbeddingProvider
from app.assistant.schemas import AskResponse
from app.config import Settings

DEFAULT_APPLICANT_TYPE = "international"


def applicant_type_from_question(question: str) -> str:
    """Local when the question says so; otherwise the international default."""
    if re.search(r"\blocal\b", question.lower()):
        return "local"
    return DEFAULT_APPLICANT_TYPE


class AssistantService:
    def __init__(
        self,
        settings: Settings,
        index: SearchableIndex,
        embedder: EmbeddingProvider,
        catalog_client: CatalogClient,
        checklist_client: ChecklistClient,
    ):
        self._settings = settings
        self._index = index
        self._embedder = embedder
        self._catalog_client = catalog_client
        self._checklist_client = checklist_client

    def answer(self, question: str, session_id: str) -> AskResponse:
        if is_document_question(question):
            document_answer = self._answer_document_question(question)
            if document_answer is not None:
                return document_answer
            # Program not recognised — fall through to normal FAQ retrieval
            # below, which will most likely land below threshold and return
            # the standard fallback (T3.4) asking to contact the office.

        results = self._index.search(question, self._embedder, top_k=1)
        if not results or results[0].similarity_score < self._settings.similarity_threshold:
            score = results[0].similarity_score if results else 0.0
            return build_fallback_response(self._settings, score)

        top = results[0]
        return AskResponse(
            answer=top.faq_item.answer,
            source_link=top.faq_item.source_link,
            faq_id=top.faq_item.faq_id,
            similarity_score=top.similarity_score,
        )

    def _answer_document_question(self, question: str) -> AskResponse | None:
        """T3.6: recognise the program, call the checklist endpoint (T4.2/T4.3),
        answer with the program name and its document list."""
        programs = self._catalog_client.list_programs()
        program = resolve_program(question, programs)
        if program is None:
            return None

        applicant_type = applicant_type_from_question(question)
        checklist = self._checklist_client.get_checklist(program.program_id, applicant_type)

        if checklist.warning:
            return AskResponse(
                answer=(
                    f"{checklist.warning} Please contact the admissions office: "
                    f"{self._settings.admissions_office_contact}"
                ),
                source_link=None,
                faq_id=None,
                similarity_score=1.0,
            )

        document_lines = [
            f"- {doc.name} ({doc.format}"
            + (", translation required" if doc.translation else "")
            + (", notarisation required" if doc.notarisation else "")
            + f", deadline {doc.deadline})"
            for doc in checklist.items
        ]
        answer_text = (
            f"Required documents for {program.title} ({applicant_type} applicant):\n" + "\n".join(document_lines)
        )
        return AskResponse(answer=answer_text, source_link=None, faq_id=None, similarity_score=1.0)
