from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import DATABASE_UNAVAILABLE_RESPONSE, INVALID_REQUEST_RESPONSE, PROGRAM_NOT_FOUND, ErrorResponse
from app.catalogue.schemas import DegreeLevel, ProgramListResponse, ProgramOut
from app.catalogue.service import get_active_program, search_programs
from app.db import get_db_session

router = APIRouter(prefix="/programs", tags=["catalogue"])


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


@router.get(
    "",
    response_model=ProgramListResponse,
    responses={**INVALID_REQUEST_RESPONSE, **DATABASE_UNAVAILABLE_RESPONSE},
    summary="Search and filter study programs",
)
def list_programs(
    session: Annotated[Session, Depends(get_db_session)],
    q: Annotated[str | None, Query(max_length=100, description="Keyword in the program title, faculty, or id")] = None,
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


@router.get(
    "/{program_id}",
    response_model=ProgramOut,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "No active program with this id.",
            "content": {
                "application/json": {
                    "example": {"error_code": PROGRAM_NOT_FOUND, "message": "Program not found."}
                }
            },
        },
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Get one study program",
)
def get_program(
    session: Annotated[Session, Depends(get_db_session)],
    program_id: Annotated[str, Path(max_length=64)],
) -> ProgramOut | JSONResponse:
    program = get_active_program(session, program_id)
    if program is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(error_code=PROGRAM_NOT_FOUND, message="Program not found.").model_dump(),
        )
    return ProgramOut.model_validate(program)
