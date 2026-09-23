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
_APPLICANT_STEMS = _LOCAL_STEMS + _INTERNATIONAL_STEMS
_STOPWORDS = {"and", "of", "the", "in", "for", "a", "an"}
_TOKEN = re.compile(r"[a-zа-яёәғқңөұүһі0-9]+")
_SUFFIXES = ("ational", "ical", "ics", "ing", "ies", "ed", "es", "er", "al", "e", "s", "y")
_DEGREE_STEMS = {
    "bachelor": ("bachelor", "undergraduate", "бакалавр"),
    "master": ("master", "магистр"),
    "phd": ("phd", "doctoral", "докторант"),
}
_PARTIAL_TITLE_MIN_WORDS = 3
_PARTIAL_TITLE_SHARE = 2 / 3


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def is_document_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in _DOCUMENT_KEYWORDS)


def _title_matches(program: Program, question: str, question_stems: set[str]) -> bool:
    if program.title.lower() in question.lower():
        return True
    title_stems = [_stem(token) for token in _tokens(program.title) if token not in _STOPWORDS]
    matched = sum(stem in question_stems for stem in title_stems)
    if title_stems and matched == len(title_stems):
        return True
    return len(title_stems) >= _PARTIAL_TITLE_MIN_WORDS and matched / len(title_stems) >= _PARTIAL_TITLE_SHARE


def degrees_mentioned(text: str) -> set[str]:
    tokens = _tokens(text)
    return {degree for degree, stems in _DEGREE_STEMS.items() if any(token.startswith(stems) for token in tokens)}


def resolve_program(question: str, programs: list[Program]) -> Program | None:
    tokens = _tokens(question)
    for program in programs:
        if program.program_id.lower() in tokens:
            return program

    stems = {_stem(token) for token in tokens if not token.startswith(_APPLICANT_STEMS)}
    candidates = [program for program in programs if _title_matches(program, question, stems)]
    degrees = degrees_mentioned(question)
    if degrees and len(candidates) > 1:
        candidates = [program for program in candidates if program.degree_level in degrees]
    return candidates[0] if len(candidates) == 1 else None


def applicant_type_from_question(question: str, program: Program) -> str | None:
    title_tokens = set(_tokens(program.title))
    tokens = [token for token in _tokens(question) if token not in title_tokens]
    is_local = any(token.startswith(_LOCAL_STEMS) for token in tokens)
    is_international = any(token.startswith(_INTERNATIONAL_STEMS) for token in tokens)
    if is_local == is_international:
        return None
    return "local" if is_local else "international"
