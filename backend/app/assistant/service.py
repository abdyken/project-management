from __future__ import annotations

from sqlalchemy.orm import Session

from app.assistant import retrieval
from app.assistant.catalogue import (
    MAX_COMPARED,
    CatalogueRequest,
    answer_from_catalogue,
    catalogue_request,
    summary_request,
)
from app.assistant.fallback import build_fallback_response
from app.assistant.generation import generate_catalogue_answer, generate_grounded_answer
from app.assistant.intents import (
    applicant_type_from_question,
    applicant_type_mentioned,
    degrees_mentioned,
    is_contextual_follow_up,
    is_document_question,
    resolve_programs,
)
from app.assistant.llm import Llm, get_llm
from app.assistant.schemas import Answer, AnswerSource, FaqItem
from app.catalogue.models import Program
from app.catalogue.service import search_programs
from app.checklist.service import MISSING_REQUIREMENTS_WARNING, get_requirements
from app.config import Settings
from app.followups.service import log_missing_documents, log_unanswered_question

_DOCUMENT_EXAMPLE = "Which documents do I need for {title} ({program_id}) as a local applicant?"
MAX_LISTED_FOR_MODEL = 15


class AssistantService:
    def __init__(self, session: Session, settings: Settings, llm: Llm | None = None, topic: str | None = None):
        self._session = session
        self._settings = settings
        self._llm = llm if llm is not None else get_llm(settings)
        self._topic = topic

    def answer(self, question: str, session_id: str) -> Answer:
        programs = search_programs(self._session)
        if is_document_question(question):
            matched = resolve_programs(question, programs)
            if len(matched) == 1:
                return self._answer_document_question(question, session_id, matched[0])
            if len(matched) > 1:
                return _choose_program(matched, _DOCUMENT_EXAMPLE)
        else:
            request = catalogue_request(self._session, question, programs)
            if request is not None:
                return self._answer_from_catalogue(question, request)

        results = retrieval.search(self._session, question, limit=self._settings.grounding_top_k)
        result = _best_for_audience(question, results)
        if self._below_threshold(result) and self._topic and is_contextual_follow_up(question):
            in_context = f"{self._topic}: {question}"
            context_results = retrieval.search(self._session, in_context, limit=self._settings.grounding_top_k)
            context_result = _best_for_audience(in_context, context_results)
            if not self._below_threshold(context_result):
                question, results, result = in_context, context_results, context_result
        if result is None or self._below_threshold(result):
            summary = summary_request(question, programs)
            if summary is not None:
                return self._answer_from_catalogue(question, summary)
            score = results[0].similarity_score if results else None
            log_unanswered_question(self._session, question, score, session_id)
            return build_fallback_response(self._settings, score)

        if self._llm is not None:
            sources = [result.faq_item] + self._faq_sources(question, results, exclude=result)
            generated = generate_grounded_answer(self._llm, question, sources, result.similarity_score)
            if generated is not None:
                return generated

        return Answer(
            answer=result.faq_item.answer,
            sources=[AnswerSource.from_faq(result.faq_item)],
            source_link=result.faq_item.source_link,
            faq_id=result.faq_item.faq_id,
            similarity_score=result.similarity_score,
        )

    def _below_threshold(self, result: retrieval.SearchResult | None) -> bool:
        return result is None or result.similarity_score < self._settings.similarity_threshold

    def _answer_from_catalogue(self, question: str, request: CatalogueRequest) -> Answer:
        contact = self._settings.admissions_office_contact
        if self._llm is not None and _model_can_answer(request):
            results = retrieval.search(self._session, question, limit=self._settings.grounding_top_k)
            items = self._faq_sources(question, results)
            generated = generate_catalogue_answer(self._llm, question, request.programs, items, contact)
            if generated is not None:
                return generated
        rendered = answer_from_catalogue(request, contact)
        return _text_answer(rendered.text, rendered.sources)

    def _faq_sources(
        self, question: str, results: list[retrieval.SearchResult], exclude: retrieval.SearchResult | None = None
    ) -> list[FaqItem]:
        return [
            r.faq_item
            for r in results
            if r is not exclude
            and r.similarity_score >= self._settings.similarity_threshold
            and _written_for(question, r.faq_item)
        ]

    def _answer_document_question(self, question: str, session_id: str, program: Program) -> Answer:
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


def _model_can_answer(request: CatalogueRequest) -> bool:
    if request.ambiguous or not request.programs:
        return False
    if request.listing is not None:
        return len(request.programs) <= MAX_LISTED_FOR_MODEL
    return len(request.programs) <= MAX_COMPARED


def _label(program: Program) -> str:
    return f"{program.title} ({program.degree_level}, {program.program_id})"


def _choose_program(programs: list[Program], example_question: str) -> Answer:
    example = programs[0]
    return _text_answer(
        f"Your question matches several programs: {'; '.join(_label(program) for program in programs)}. "
        f'Ask again with the program code, for example: '
        f'"{example_question.format(title=example.title, program_id=example.program_id)}"'
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


def _text_answer(text: str, sources: list[AnswerSource] | None = None) -> Answer:
    sources = sources or []
    return Answer(
        answer=text,
        sources=sources,
        source_link=sources[0].link if sources else None,
        faq_id=None,
        similarity_score=None,
    )
