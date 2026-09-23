from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.assistant import retrieval
from app.assistant.fallback import build_fallback_response
from app.assistant.intents import is_document_question, resolve_program
from app.assistant.schemas import AskResponse
from app.catalogue.service import search_programs
from app.checklist.service import MISSING_REQUIREMENTS_WARNING, get_requirements
from app.config import Settings

DEFAULT_APPLICANT_TYPE = "international"


def applicant_type_from_question(question: str) -> str:
    if re.search(r"\blocal\b", question.lower()):
        return "local"
    return DEFAULT_APPLICANT_TYPE


class AssistantService:
    def __init__(self, session: Session, settings: Settings):
        self._session = session
        self._settings = settings

    def answer(self, question: str) -> AskResponse:
        if is_document_question(question):
            document_answer = self._answer_document_question(question)
            if document_answer is not None:
                return document_answer

        result = retrieval.search(self._session, question)
        if result is None or result.similarity_score < self._settings.similarity_threshold:
            return build_fallback_response(self._settings, result.similarity_score if result else 0.0)

        return AskResponse(
            answer=result.faq_item.answer,
            source_link=result.faq_item.source_link,
            faq_id=result.faq_item.faq_id,
            similarity_score=result.similarity_score,
        )

    def _answer_document_question(self, question: str) -> AskResponse | None:
        program = resolve_program(question, search_programs(self._session))
        if program is None:
            return None

        applicant_type = applicant_type_from_question(question)
        requirements = get_requirements(self._session, program.program_id, applicant_type)

        if not requirements:
            return AskResponse(
                answer=(
                    f"{MISSING_REQUIREMENTS_WARNING} Please contact the admissions office: "
                    f"{self._settings.admissions_office_contact}"
                ),
                source_link=None,
                faq_id=None,
                similarity_score=1.0,
            )

        document_lines = [
            f"- {doc.name} ({doc.document_format}"
            + (", translation required" if doc.translation_required else "")
            + (", notarisation required" if doc.notarisation_required else "")
            + f", deadline {doc.deadline})"
            for doc in requirements
        ]
        answer_text = (
            f"Required documents for {program.title} ({applicant_type} applicant):\n" + "\n".join(document_lines)
        )
        return AskResponse(answer=answer_text, source_link=None, faq_id=None, similarity_score=1.0)
