from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.catalogue.models import Program


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_programs(
    session: Session,
    *,
    keyword: str | None = None,
    faculty: str | None = None,
    degree_level: str | None = None,
    language: str | None = None,
) -> list[Program]:
    query = select(Program).where(Program.is_active.is_(True))

    if keyword:
        pattern = f"%{_escape_like(keyword)}%"
        query = query.where(
            or_(
                Program.title.ilike(pattern, escape="\\"),
                Program.faculty.ilike(pattern, escape="\\"),
                Program.program_id.ilike(pattern, escape="\\"),
            )
        )
    if faculty:
        query = query.where(func.lower(Program.faculty) == faculty.lower())
    if degree_level:
        query = query.where(Program.degree_level == degree_level)
    if language:
        languages = func.concat(",", func.replace(func.lower(Program.language), ", ", ","), ",")
        query = query.where(languages.like(f"%,{_escape_like(language.lower())},%", escape="\\"))

    return list(session.scalars(query.order_by(Program.title, Program.program_id)))


def get_active_program(session: Session, program_id: str) -> Program | None:
    program = session.get(Program, program_id)
    if program is None or not program.is_active:
        return None
    return program
