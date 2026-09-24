from __future__ import annotations

from sqlalchemy.orm import Session

from app.assistant import retrieval
from app.assistant.fallback import build_fallback_response
from app.assistant.intents import (
    applicant_type_from_question,
    applicant_type_mentioned,
    degrees_mentioned,
    is_document_question,
    resolve_programs,
)
from app.assistant.schemas import AskResponse, FaqItem
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
            programs = resolve_programs(question, search_programs(self._session))
            if len(programs) == 1:
                return self._answer_document_question(question, session_id, programs[0])
            if len(programs) > 1:
                return _choose_program(programs)

        results = retrieval.search(self._session, question)
        result = _best_for_audience(question, results)
        if result is None or result.similarity_score < self._settings.similarity_threshold:
            score = results[0].similarity_score if results else None
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
                f"{_label(program)} has separate document lists for local and international applicants. "
                f'Ask again with "local" or "international", for example: '
                f'"Which documents do I need for {program.title} ({program.program_id}) as an international applicant?"'
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
            f"Required documents for {_label(program)}, {applicant_type} applicant:\n" + "\n".join(lines)
        )


def _label(program: Program) -> str:
    return f"{program.title} ({program.degree_level}, {program.program_id})"


def _choose_program(programs: list[Program]) -> AskResponse:
    example = programs[0]
    return _text_answer(
        f"Your question matches several programs: {'; '.join(_label(program) for program in programs)}. "
        f'Ask again with the program code, for example: '
        f'"Which documents do I need for {example.title} ({example.program_id}) as a local applicant?"'
    )


def _best_for_audience(question: str, results: list[retrieval.SearchResult]) -> retrieval.SearchResult | None:
    if not results:
        return None
    top = results[0]
    if _written_for(question, top.faq_item):
        return top
    same_topic = (r for r in results[1:] if r.faq_item.category == top.faq_item.category)
    return next((r for r in same_topic if _written_for(question, r.faq_item)), None)


def _written_for(question: str, item: FaqItem) -> bool:
    degrees = degrees_mentioned(question)
    if degrees and item.degrees and not degrees & set(item.degrees):
        return False
    applicant_type = applicant_type_mentioned(question)
    return not (applicant_type and item.applicant_types and applicant_type not in item.applicant_types)


def _text_answer(text: str) -> AskResponse:
    return AskResponse(answer=text, source_link=None, faq_id=None, similarity_score=None)
