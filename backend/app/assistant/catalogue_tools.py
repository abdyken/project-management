from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.catalogue import service as catalogue
from app.assistant.schemas import AnswerSource
from app.catalogue.models import Program

NOT_PUBLISHED = "not published yet"


def search_programs(
    session: Session,
    query: str | None = None,
    degree_level: str | None = None,
    language: str | None = None,
    faculty: str | None = None,
) -> list[dict[str, Any]]:
    programs = catalogue.search_programs(
        session, keyword=query, faculty=faculty, degree_level=degree_level, language=language
    )
    return [program_facts(program) for program in programs]


def get_program(session: Session, program_id: str) -> dict[str, Any] | None:
    program = catalogue.get_active_program(session, program_id)
    return program_facts(program) if program is not None else None


def program_facts(program: Program) -> dict[str, Any]:
    return {
        "program_id": program.program_id,
        "title": program.title,
        "degree_level": program.degree_level,
        "faculty": program.faculty,
        "language": program.language,
        "tuition_per_ects": fees_text(program.tuition_per_ects_kzt, program.tuition_per_ects_usd),
        "tuition_per_ects_kzt": program.tuition_per_ects_kzt,
        "tuition_per_ects_usd": program.tuition_per_ects_usd,
        "deadline_local": _date_text(program.deadline_local),
        "deadline_international": _date_text(program.deadline_international),
        "program_page": program.source_url,
    }


def fees_text(kzt: int | None, usd: int | None) -> str:
    if kzt is None and usd is None:
        return NOT_PUBLISHED
    if kzt is None:
        return f"about USD {usd:,}"
    if usd is None:
        return f"{kzt:,} KZT"
    return f"{kzt:,} KZT (about USD {usd:,})"


def program_source(facts: dict[str, Any]) -> AnswerSource | None:
    if not facts.get("program_page"):
        return None
    return AnswerSource(
        faq_id=None, question=None, link=facts["program_page"], title=f"{facts['title']} ({facts['program_id']})"
    )


def has_missing_values(facts: dict[str, Any]) -> bool:
    return NOT_PUBLISHED in facts.values()


def _date_text(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value is not None else NOT_PUBLISHED
