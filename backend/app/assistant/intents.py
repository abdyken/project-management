from __future__ import annotations

from difflib import SequenceMatcher

from app.catalogue.models import Program

_DOCUMENT_KEYWORDS = (
    "document",
    "documents",
    "paperwork",
    "checklist",
    "what do i need",
    "required documents",
    "документ",
)

_FUZZY_MATCH_CUTOFF = 0.6


def is_document_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in _DOCUMENT_KEYWORDS)


def resolve_program(question: str, programs: list[Program]) -> Program | None:
    lowered = question.lower()

    for program in programs:
        if program.title.lower() in lowered:
            return program

    best_program: Program | None = None
    best_ratio = 0.0
    for program in programs:
        ratio = SequenceMatcher(None, program.title.lower(), lowered).ratio()
        if ratio > best_ratio:
            best_ratio, best_program = ratio, program

    return best_program if best_ratio >= _FUZZY_MATCH_CUTOFF else None
