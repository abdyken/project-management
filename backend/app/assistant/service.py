from __future__ import annotations

from sqlalchemy.orm import Session

from app.assistant import retrieval
from app.assistant.catalogue import (
    MAX_COMPARED,
    CatalogueRequest,
    answer_from_catalogue,
    catalogue_request,
    label,
    summary_request,
    title_in,
)
from app.assistant.catalogue_tools import program_facts
from app.assistant.fallback import build_fallback_response
from app.assistant.generation import generate_catalogue_answer, generate_chat_reply, generate_grounded_answer
from app.assistant.intents import (
    DEADLINE,
    applicant_type_from_question,
    applicant_type_mentioned,
    catalogue_fields,
    degrees_mentioned,
    is_contextual_follow_up,
    is_document_question,
    resolve_programs,
)
from app.assistant.language import detect_language
from app.assistant.llm import Llm, get_llm
from app.assistant.schemas import Answer, AnswerSource, FaqItem, Language
from app.assistant.texts import contact, text
from app.catalogue.models import Program
from app.catalogue.service import search_programs
from app.checklist.service import get_requirements
from app.config import Settings
from app.followups.service import log_missing_documents, log_unanswered_question

MAX_LISTED_FOR_MODEL = 15
CALENDAR = "calendar"
FAQ_OVER_TITLE_MATCH = 0.8


class AssistantService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        llm: Llm | None = None,
        topic: str | None = None,
        language: Language | None = None,
        history: list[tuple[str, str]] | None = None,
    ):
        self._session = session
        self._settings = settings
        self._llm = llm if llm is not None else get_llm(settings)
        self._topic = topic
        self._language = language
        self._history = history or []
        self._search_language: Language = language or "en"

    def answer(self, question: str, session_id: str) -> Answer:
        language = self._language or detect_language(question)
        self._search_language = language
        programs = search_programs(self._session)
        if is_document_question(question):
            matched = resolve_programs(question, programs)
            if len(matched) == 1:
                return self._answer_document_question(question, session_id, matched[0], language)
            if len(matched) > 1:
                return _choose_program(matched, language)
        else:
            request = catalogue_request(self._session, question, programs)
            if request is not None and not self._faq_answers_better(question, request):
                return self._answer_from_catalogue(question, request, language)

        results = self._search(question)
        result = _best_for_audience(question, results)
        if self._topic and is_contextual_follow_up(question):
            in_context = f"{self._topic}: {question}"
            context_results = self._search(in_context)
            context_result = _best_for_audience(in_context, context_results)
            if context_result is not None and not self._below_threshold(context_result) and (
                result is None or context_result.similarity_score > result.similarity_score
            ):
                question, results, result = in_context, context_results, context_result
        if result is None or self._below_threshold(result):
            summary = summary_request(question, programs)
            if summary is not None:
                return self._answer_from_catalogue(question, summary, language)
            score = results[0].similarity_score if results else None
            chat = self._chat_reply(question, language)
            if chat is not None:
                reply, is_admission_question = chat
                if is_admission_question:
                    log_unanswered_question(self._session, question, score, session_id)
                return _text_answer(reply)
            log_unanswered_question(self._session, question, score, session_id)
            return build_fallback_response(self._settings, score, language)

        if self._llm is not None:
            sources = ([result.faq_item] + self._faq_sources(question, results, exclude=result))[
                : self._settings.grounding_top_k
            ]
            localized = [item.localized(language) for item in sources]
            generated = generate_grounded_answer(self._llm, question, localized, result.similarity_score)
            if generated is not None:
                return generated

        item = result.faq_item.localized(language)
        answer = item.answer if result.faq_item.has(language) else text(language, "english_only", answer=item.answer)
        return Answer(
            answer=answer,
            sources=[AnswerSource.from_faq(item)],
            source_link=item.source_link,
            faq_id=item.faq_id,
            similarity_score=result.similarity_score,
        )

    def _faq_answers_better(self, question: str, request: CatalogueRequest) -> bool:
        if request.by_code or request.listing is not None:
            return False
        results = self._search(question)
        best = _best_for_audience(question, results)
        return best is not None and best.similarity_score >= FAQ_OVER_TITLE_MATCH

    def _chat_reply(self, question: str, language: Language) -> tuple[str, bool] | None:
        if self._llm is None:
            return None
        return generate_chat_reply(self._llm, question, self._history, self._contact(language))

    def _search(self, question: str) -> list[retrieval.SearchResult]:
        return retrieval.search(
            self._session, question, limit=2 * self._settings.grounding_top_k, language=self._search_language
        )

    def _below_threshold(self, result: retrieval.SearchResult | None) -> bool:
        return result is None or result.similarity_score < self._settings.similarity_threshold

    def _contact(self, language: Language) -> str:
        return contact(language, self._settings.admissions_office_contact)

    def _answer_from_catalogue(self, question: str, request: CatalogueRequest, language: Language) -> Answer:
        office = self._contact(language)
        if self._llm is not None and _model_can_answer(request):
            results = self._search(question)
            items = [
                item.localized(language)
                for item in self._faq_sources(question, results)[: self._settings.grounding_top_k]
            ]
            generated = generate_catalogue_answer(self._llm, question, request.programs, items, office)
            if generated is not None:
                return generated
        rendered = answer_from_catalogue(request, office, language)
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

    def _answer_document_question(
        self, question: str, session_id: str, program: Program, language: Language
    ) -> Answer:
        facts = program_facts(program)
        name = label(facts, language)
        applicant_type = applicant_type_from_question(question, program)
        if applicant_type is None:
            return _text_answer(
                text(
                    language,
                    "ask_applicant_type",
                    label=name,
                    title=title_in(facts, language),
                    code=program.program_id,
                )
            )

        requirements = get_requirements(self._session, program.program_id, applicant_type)
        if not requirements:
            log_missing_documents(self._session, program.program_id, applicant_type, question, session_id)
            return _text_answer(text(language, "missing_documents", contact=self._contact(language)))

        lines = [
            text(
                language,
                "document_line",
                name=doc.name,
                format=text(language, f"format.{doc.document_format}"),
                translation=text(language, "translation_required") if doc.translation_required else "",
                notarisation=text(language, "notarisation_required") if doc.notarisation_required else "",
                deadline=doc.deadline,
            )
            for doc in requirements
        ]
        header = text(language, "documents_header", label=name, kind=text(language, f"kind.{applicant_type}"))
        return _text_answer(header + "\n" + "\n".join(lines))


def _model_can_answer(request: CatalogueRequest) -> bool:
    if request.ambiguous or not request.programs:
        return False
    if request.listing is not None:
        return len(request.programs) <= MAX_LISTED_FOR_MODEL
    return len(request.programs) <= MAX_COMPARED


def _choose_program(programs: list[Program], language: Language) -> Answer:
    facts = [program_facts(program) for program in programs]
    example = text(
        language, "example.documents", title=title_in(facts[0], language), program_id=programs[0].program_id
    )
    labels = "; ".join(label(item, language) for item in facts)
    return _text_answer(text(language, "choose_program", labels=labels, example=example))


def _best_for_audience(question: str, results: list[retrieval.SearchResult]) -> retrieval.SearchResult | None:
    if not results:
        return None
    top = results[0]
    if _written_for(question, top.faq_item):
        return top
    same_topic = (r for r in results[1:] if r.faq_item.category == top.faq_item.category)
    return next((r for r in same_topic if _written_for(question, r.faq_item)), None)


def _written_for(question: str, item: FaqItem) -> bool:
    if item.category == CALENDAR and DEADLINE in catalogue_fields(question):
        return False
    degrees = degrees_mentioned(question)
    if degrees and item.degrees and not degrees & set(item.degrees):
        return False
    applicant_type = applicant_type_mentioned(question)
    return not (applicant_type and item.applicant_types and applicant_type not in item.applicant_types)


def _text_answer(answer: str, sources: list[AnswerSource] | None = None) -> Answer:
    sources = sources or []
    return Answer(
        answer=answer,
        sources=sources,
        source_link=sources[0].link if sources else None,
        faq_id=None,
        similarity_score=None,
    )
