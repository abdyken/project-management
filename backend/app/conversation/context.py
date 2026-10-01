"""Turn a follow-up question into a standalone one (US11 T11.2).

"and as an international applicant?" after "Which documents do I need for
6B06102 as a local applicant?" becomes "Which documents do I need for 6B06102
as an international applicant?", so the answer service gets a question it can
answer on its own. The same standalone question is the right input for an
answer model later (US10).

Only clear follow-ups are rewritten: questions made only of filler words, a
topic word ("documents", "fee"), an applicant type and/or a program. A
question with a subject of its own, such as "How much does the dormitory
cost?", is never mixed with an earlier program.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.assistant.intents import (
    applicant_type_mentioned,
    is_document_question,
    is_tuition_question,
    resolve_programs,
)
from app.catalogue.models import Program
from app.conversation.models import USER, ChatTurn

DOCUMENTS = "documents"
TUITION = "tuition"

_WORD = re.compile(r"\w+")
# Words that carry no subject of their own in a follow-up (en / ru / kk).
_FILLER = frozenset(
    """
    and also too then what about how much many is are does do the a an as for of to in it its me i my we
    need please applicant applicants student students
    а и или для как насчет насчёт что про тогда тоже
    ал ше үшін да де
    """.split()
)


@dataclass(frozen=True)
class Topic:
    intent: str | None = None
    program_id: str | None = None
    applicant_type: str | None = None


def topic_of(question: str, programs: Sequence[Program]) -> Topic:
    if is_document_question(question):
        intent = DOCUMENTS
    elif is_tuition_question(question):
        intent = TUITION
    else:
        intent = None
    matches = resolve_programs(question, list(programs))
    return Topic(
        intent=intent,
        program_id=matches[0].program_id if len(matches) == 1 else None,
        applicant_type=applicant_type_mentioned(question),
    )


def context_of(history: Sequence[ChatTurn], programs: Sequence[Program]) -> Topic:
    """The latest intent, program and applicant type the applicant named, each
    taken from the most recent question that mentioned it."""
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
    """True when every word is filler, a topic word, an applicant type or the
    program named in the question - nothing that starts a new subject."""
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
        or is_tuition_question(word)
        or applicant_type_mentioned(word) is not None
        for word in words
    )


def standalone_question(question: str, history: Sequence[ChatTurn], programs: Sequence[Program]) -> str:
    """The question to answer: the applicant's own words, or a rewritten
    standalone question when it is a follow-up to the earlier turns."""
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

    # A full document question for a program, without the applicant type: keep
    # the applicant type named earlier instead of asking again.
    if (
        current.intent == DOCUMENTS
        and current.program_id
        and current.applicant_type is None
        and context.applicant_type
    ):
        return _build(DOCUMENTS, current.program_id, context.applicant_type)
    return question


def _build(intent: str, program_id: str, applicant_type: str | None) -> str:
    if intent == TUITION:
        return f"How much is tuition for {program_id}?"
    if applicant_type is None:
        return f"Which documents do I need for {program_id}?"
    article = "an" if applicant_type == "international" else "a"
    return f"Which documents do I need for {program_id} as {article} {applicant_type} applicant?"
