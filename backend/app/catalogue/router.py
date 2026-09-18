from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.catalogue.schemas import DegreeLevel, ProgramListResponse, ProgramOut
from app.catalogue.service import search_programs
from app.db import get_db_session

router = APIRouter(prefix="/programs", tags=["catalogue"])


def _clean(value: str | None) -> str | None:
    """Treat blank or whitespace-only query values as 'no filter'."""
    if value is None:
        return None
    return value.strip() or None


@router.get("", response_model=ProgramListResponse)
def list_programs(
    session: Annotated[Session, Depends(get_db_session)],
    q: Annotated[str | None, Query(max_length=100, description="Keyword in the program title or faculty")] = None,
    faculty: Annotated[str | None, Query(max_length=255)] = None,
    degree_level: Annotated[DegreeLevel | None, Query()] = None,
    language: Annotated[str | None, Query(max_length=50)] = None,
) -> ProgramListResponse:
    programs = search_programs(
        session,
        keyword=_clean(q),
        faculty=_clean(faculty),
        degree_level=degree_level,
        language=_clean(language),
    )
    return ProgramListResponse(
        total=len(programs),
        programs=[ProgramOut.model_validate(program) for program in programs],
    )
