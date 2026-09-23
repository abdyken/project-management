from __future__ import annotations

from sqlalchemy.orm import Session

from app.assistant import retrieval
from app.assistant.fallback import build_fallback_response
from app.assistant.intents import applicant_type_from_question, is_document_question, resolve_program
from app.assistant.schemas import AskResponse
from app.catalogue.models import Program
from app.catalogue.service import search_programs
from app.checklist.service import MISSING_REQUIREMENTS_WARNING, get_requirements
from app.config import Settings
from app.followups.service import log_missing_documents, log_unanswered_question


class AssistantService:
    def __init__(self, session: Session, settings: Settings):
        self._session = session
        self._settings = settings

    def answer(self, question: str, session_id: str) -> AskResponse:
        if is_document_question(question):
            program = resolve_program(question, search_programs(self._session))
            if program is not None:
                return self._answer_document_question(question, session_id, program)

        result = retrieval.search(self._session, question)
        if result is None or result.similarity_score < self._settings.similarity_threshold:
            score = result.similarity_score if result else None
            log_unanswered_question(self._session, question, score, session_id)
            return build_fallback_response(self._settings, score)

        return AskResponse(
            answer=result.faq_item.answer,
            source_link=result.faq_item.source_link,
            faq_id=result.faq_item.faq_id,
            similarity_score=result.similarity_score,
        )

    def _answer_document_question(self, question: str, session_id: str, program: Program) -> AskResponse:
        applicant_type = applicant_type_from_question(question, program)
        if applicant_type is None:
            return _text_answer(
                f"{program.title} has separate document lists for local and international applicants. "
                f'Ask again with "local" or "international", for example: '
                f'"Which documents do I need for {program.title} as an international applicant?"'
            )

        requirements = get_requirements(self._session, program.program_id, applicant_type)
        if not requirements:
            log_missing_documents(self._session, program.program_id, applicant_type, question, session_id)
            return _text_answer(f"{MISSING_REQUIREMENTS_WARNING} {self._settings.admissions_office_contact}")

        lines = [
            f"- {doc.name} ({doc.document_format}"
            + (", translation required" if doc.translation_required else "")
            + (", notarisation required" if doc.notarisation_required else "")
            + f", deadline {doc.deadline})"
            for doc in requirements
        ]
        return _text_answer(
            f"Required documents for {program.title} ({applicant_type} applicant):\n" + "\n".join(lines)
        )


def _text_answer(text: str) -> AskResponse:
    return AskResponse(answer=text, source_link=None, faq_id=None, similarity_score=None)
