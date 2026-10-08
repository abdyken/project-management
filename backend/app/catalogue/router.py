from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import (
    DATABASE_UNAVAILABLE_RESPONSE,
    INVALID_REQUEST,
    INVALID_REQUEST_RESPONSE,
    PROGRAM_NOT_FOUND,
    ErrorResponse,
)
from app.catalogue.schemas import CompareResponse, ComparedProgram, DegreeLevel, ProgramListResponse, ProgramOut
from app.catalogue.service import document_counts, get_active_program, search_programs
from app.db import get_db_session

router = APIRouter(prefix="/programs", tags=["catalogue"])

MIN_COMPARED = 2
MAX_COMPARED = 3


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
    "/compare",
    response_model=CompareResponse,
    responses={
        404: {"model": ErrorResponse, "description": "One of the ids is not an active program."},
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
    summary="Compare two or three study programs side by side",
)
def compare_programs(
    session: Annotated[Session, Depends(get_db_session)],
    ids: Annotated[str, Query(max_length=200, description="2 or 3 comma-separated program ids, in display order")],
) -> CompareResponse | JSONResponse:
    program_ids = [program_id.strip() for program_id in ids.split(",") if program_id.strip()]
    if not MIN_COMPARED <= len(program_ids) <= MAX_COMPARED or len(set(program_ids)) != len(program_ids):
        return _error(422, INVALID_REQUEST, f"ids: give {MIN_COMPARED} or {MAX_COMPARED} different program ids")

    programs = []
    for program_id in program_ids:
        program = get_active_program(session, program_id)
        if program is None:
            return _error(404, PROGRAM_NOT_FOUND, f"Program not found: {program_id}")
        programs.append(program)

    counts = document_counts(session, program_ids)
    return CompareResponse(
        programs=[
            ComparedProgram(
                **ProgramOut.model_validate(program).model_dump(),
                documents_local=counts.get((program.program_id, "local"), 0),
                documents_international=counts.get((program.program_id, "international"), 0),
            )
            for program in programs
        ]
    )


def _error(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorResponse(error_code=error_code, message=message).model_dump())


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
        **INVALID_REQUEST_RESPONSE,
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
