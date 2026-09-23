from __future__ import annotations

import re

from app.catalogue.models import Program

_DOCUMENT_KEYWORDS = (
    "document",
    "paperwork",
    "checklist",
    "what do i need",
    "документ",
    "құжат",
)
_LOCAL_STEMS = ("local", "kazakhstan", "citizen", "resident", "местн", "казахстан", "гражданин")
_INTERNATIONAL_STEMS = ("international", "foreign", "abroad", "overseas", "иностран", "международ", "зарубеж")
_STOPWORDS = {"and", "of", "the", "in", "for", "a", "an"}
_TOKEN = re.compile(r"[a-zа-яёәғқңөұүһі0-9]+")
_PREFIX = 5
_MIN_TITLE_SHARE = 0.5


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _same_word(a: str, b: str) -> bool:
    return a == b or (len(a) >= _PREFIX and len(b) >= _PREFIX and a[:_PREFIX] == b[:_PREFIX])


def is_document_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in _DOCUMENT_KEYWORDS)


def _title_share(program: Program, question_tokens: list[str]) -> float:
    title_tokens = [token for token in _tokens(program.title) if token not in _STOPWORDS]
    matched = sum(any(_same_word(t, q) for q in question_tokens) for t in title_tokens)
    return matched / len(title_tokens) if title_tokens else 0.0


def resolve_program(question: str, programs: list[Program]) -> Program | None:
    question_tokens = _tokens(question)
    for program in programs:
        if program.program_id.lower() in question_tokens:
            return program

    scored = sorted(((_title_share(p, question_tokens), p) for p in programs), key=lambda pair: -pair[0])
    if not scored or scored[0][0] < _MIN_TITLE_SHARE:
        return None
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None
    return scored[0][1]


def applicant_type_from_question(question: str, program: Program) -> str | None:
    title_tokens = set(_tokens(program.title))
    tokens = [token for token in _tokens(question) if token not in title_tokens]
    is_local = any(token.startswith(_LOCAL_STEMS) for token in tokens)
    is_international = any(token.startswith(_INTERNATIONAL_STEMS) for token in tokens)
    if is_local == is_international:
        return None
    return "local" if is_local else "international"
