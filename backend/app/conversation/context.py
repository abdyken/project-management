from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.assistant.catalogue import standalone_question_for
from app.assistant.intents import (
    DEADLINE,
    applicant_type_mentioned,
    catalogue_fields,
    is_document_question,
    resolve_programs,
    without_titles,
)
from app.catalogue.models import Program
from app.conversation.models import USER, ChatTurn

DOCUMENTS = "documents"

_WORD = re.compile(r"\w+")
_FILLER = frozenset(
    """
    and also too then what about how much many is are does do the a an as for of to in it its me i my we
    need please applicant applicants student students when which
    а и или для как насчет насчёт что про тогда тоже какой какая когда
    ал ше үшін да де қандай
    """.split()
)


@dataclass(frozen=True)
class Topic:
    intent: str | None = None
    program_id: str | None = None
    applicant_type: str | None = None


def topic_of(question: str, programs: Sequence[Program]) -> Topic:
    matches = resolve_programs(question, list(programs))
    if is_document_question(question):
        intent = DOCUMENTS
    else:
        fields = catalogue_fields(without_titles(question, matches))
        intent = fields[0] if len(fields) == 1 else None
    return Topic(
        intent=intent,
        program_id=matches[0].program_id if len(matches) == 1 else None,
        applicant_type=applicant_type_mentioned(question),
    )


def context_of(history: Sequence[ChatTurn], programs: Sequence[Program]) -> Topic:
    intent = program_id = applicant_type = None
    for turn in reversed(history):
        if turn.role != USER:
            continue
        topic = topic_of(turn.text, programs)
        intent = intent or topic.intent
        program_id = program_id or topic.program_id
        applicant_type = applicant_type or topic.applicant_type
        if intent and program_id and applicant_type:
            break
    return Topic(intent, program_id, applicant_type)


def is_follow_up(question: str, programs: Sequence[Program]) -> bool:
    words = [word.lower() for word in _WORD.findall(question)]
    if not words:
        return False
    matches = resolve_programs(question, list(programs))
    program_words: set[str] = set()
    if len(matches) == 1:
        program_words = {matches[0].program_id.lower(), *_WORD.findall(matches[0].title.lower())}
    return all(
        word in _FILLER
        or word in program_words
        or is_document_question(word)
        or bool(catalogue_fields(word))
        or applicant_type_mentioned(word) is not None
        for word in words
    )


def standalone_question(question: str, history: Sequence[ChatTurn], programs: Sequence[Program]) -> str:
    if not history:
        return question

    current = topic_of(question, programs)
    context = context_of(history, programs)

    if current != Topic() and is_follow_up(question, programs):
        intent = current.intent or context.intent
        program_id = current.program_id or context.program_id
        applicant_type = current.applicant_type or context.applicant_type
        if intent and program_id:
            return _build(intent, program_id, applicant_type)
        return question

    if (
        current.intent == DOCUMENTS
        and current.program_id
        and current.applicant_type is None
        and context.applicant_type
    ):
        return _build(DOCUMENTS, current.program_id, context.applicant_type)
    return question


def _build(intent: str, program_id: str, applicant_type: str | None) -> str:
    if intent != DOCUMENTS:
        question = standalone_question_for(intent, program_id)
        if intent == DEADLINE and applicant_type:
            return question.removesuffix("?") + f" for {applicant_type} applicants?"
        return question
    if applicant_type is None:
        return f"Which documents do I need for {program_id}?"
    article = "an" if applicant_type == "international" else "a"
    return f"Which documents do I need for {program_id} as {article} {applicant_type} applicant?"
