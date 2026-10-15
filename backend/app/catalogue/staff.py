"""Catalogue and checklist management for the admissions office (US21).

The database is the source of truth since Sprint 4: the API start imports catalogue.json
only into an empty catalogue. Program pages, the checklist and the assistant read the
tables directly, so an edit is visible at once."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, field_validator
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.api.errors import INVALID_REQUEST_RESPONSE, PROGRAM_NOT_FOUND, ErrorResponse
from app.catalogue.models import Program
from app.checklist.models import ProgramDocumentRequirement
from app.db import get_db_session
from app.staff.models import StaffUser
from app.staff.router import STAFF_RESPONSES, require_staff

PROGRAM_EXISTS = "PROGRAM_EXISTS"
ApplicantType = Literal["local", "international"]
APPLICANT_TYPES: tuple[ApplicantType, ...] = ("local", "international")


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


class ProgramFields(BaseModel):
    """Every editable fact of a program. `null` means "not published" and is shown that
    way to applicants, never as 0 or an empty date."""

    title: str = Field(min_length=1, max_length=255)
    title_ru: str | None = Field(default=None, max_length=255)
    title_kk: str | None = Field(default=None, max_length=255)
    faculty: str = Field(min_length=1, max_length=255)
    degree_level: Literal["bachelor", "master", "phd"]
    language: str | None = Field(default=None, max_length=50)
    tuition_per_ects_kzt: NonNegativeInt | None = None
    tuition_per_ects_usd: NonNegativeInt | None = None
    deadline_local: date | None = None
    deadline_international: date | None = None
    source_url: str | None = Field(default=None, max_length=500, pattern=r"^https://")
    is_active: bool = True

    @field_validator("title", "faculty", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("title_ru", "title_kk", "language", "source_url", mode="before")
    @classmethod
    def _optional(cls, value: object) -> object:
        return _blank_to_none(value)


class ProgramCreate(ProgramFields):
    program_id: str = Field(min_length=2, max_length=64, pattern=r"^[0-9A-Z]+$")


class DocumentIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    format: Literal["original", "copy"]
    translation: bool = False
    notarisation: bool = False
    deadline: str = Field(min_length=1, max_length=500)

    @field_validator("name", "deadline", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class DocumentListIn(BaseModel):
    documents: list[DocumentIn] = Field(max_length=60)


class StaffProgramOut(ProgramCreate):
    model_config = ConfigDict(from_attributes=True)

    documents: dict[ApplicantType, list[DocumentIn]]
    updated_at: datetime | None
    updated_by: str | None


class StaffProgramListItem(BaseModel):
    program_id: str
    title: str
    degree_level: str
    faculty: str
    is_active: bool
    documents_local: int
    documents_international: int
    updated_at: datetime | None
    updated_by: str | None


class StaffProgramListResponse(BaseModel):
    items: list[StaffProgramListItem]


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=ErrorResponse(error_code=code, message=message).model_dump())


def _not_found() -> JSONResponse:
    return _error(404, PROGRAM_NOT_FOUND, "Program not found.")


def _editor_names(session: Session, ids: set[int | None]) -> dict[int, str]:
    ids = {value for value in ids if value is not None}
    if not ids:
        return {}
    return dict(session.execute(select(StaffUser.id, StaffUser.name).where(StaffUser.id.in_(ids))).tuples().all())


def _documents(session: Session, program_id: str) -> dict[ApplicantType, list[DocumentIn]]:
    rows = session.scalars(
        select(ProgramDocumentRequirement)
        .where(ProgramDocumentRequirement.program_id == program_id)
        .order_by(ProgramDocumentRequirement.applicant_type, ProgramDocumentRequirement.display_order)
    )
    documents: dict[ApplicantType, list[DocumentIn]] = {kind: [] for kind in APPLICANT_TYPES}
    for row in rows:
        documents[row.applicant_type].append(
            DocumentIn(
                name=row.name,
                format=row.document_format,
                translation=row.translation_required,
                notarisation=row.notarisation_required,
                deadline=row.deadline,
            )
        )
    return documents


def _out(session: Session, program: Program) -> StaffProgramOut:
    names = _editor_names(session, {program.updated_by_id})
    return StaffProgramOut(
        **ProgramCreate.model_validate(program, from_attributes=True).model_dump(),
        documents=_documents(session, program.program_id),
        updated_at=program.updated_at,
        updated_by=names.get(program.updated_by_id) if program.updated_by_id else None,
    )


def _touch(program: Program, user: StaffUser) -> None:
    program.updated_by_id = user.id
    program.updated_at = datetime.now(timezone.utc)


router = APIRouter(prefix="/staff/programs", tags=["staff: catalogue"])

Staff = Annotated[StaffUser, Depends(require_staff())]
DbSession = Annotated[Session, Depends(get_db_session)]
ProgramId = Annotated[str, Path(max_length=64)]
NOT_FOUND_RESPONSE = {
    404: {
        "model": ErrorResponse,
        "description": "No program with this id.",
        "content": {"application/json": {"example": {"error_code": PROGRAM_NOT_FOUND, "message": "Program not found."}}},
    }
}


@router.get(
    "",
    response_model=StaffProgramListResponse,
    responses={**STAFF_RESPONSES, **INVALID_REQUEST_RESPONSE},
    summary="All programs, archived ones included",
)
def list_programs(
    _: Staff,
    session: DbSession,
    q: Annotated[str | None, Query(max_length=100, description="Text in the code, title or school")] = None,
    degree_level: Literal["bachelor", "master", "phd"] | None = None,
    active: bool | None = None,
) -> StaffProgramListResponse:
    query = select(Program).order_by(Program.degree_level, Program.program_id)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                Program.program_id.ilike(pattern),
                Program.title.ilike(pattern),
                Program.title_ru.ilike(pattern),
                Program.title_kk.ilike(pattern),
                Program.faculty.ilike(pattern),
            )
        )
    if degree_level:
        query = query.where(Program.degree_level == degree_level)
    if active is not None:
        query = query.where(Program.is_active.is_(active))
    programs = list(session.scalars(query))
    counts = {
        (program_id, kind): count
        for program_id, kind, count in session.execute(
            select(
                ProgramDocumentRequirement.program_id,
                ProgramDocumentRequirement.applicant_type,
                func.count(),
            ).group_by(ProgramDocumentRequirement.program_id, ProgramDocumentRequirement.applicant_type)
        ).tuples()
    }
    names = _editor_names(session, {program.updated_by_id for program in programs})
    return StaffProgramListResponse(
        items=[
            StaffProgramListItem(
                program_id=program.program_id,
                title=program.title,
                degree_level=program.degree_level,
                faculty=program.faculty,
                is_active=program.is_active,
                documents_local=counts.get((program.program_id, "local"), 0),
                documents_international=counts.get((program.program_id, "international"), 0),
                updated_at=program.updated_at,
                updated_by=names.get(program.updated_by_id) if program.updated_by_id else None,
            )
            for program in programs
        ]
    )


@router.get("/{program_id}", response_model=StaffProgramOut, responses={**STAFF_RESPONSES, **NOT_FOUND_RESPONSE}, summary="One program with its document lists")
def get_program(program_id: ProgramId, _: Staff, session: DbSession) -> StaffProgramOut | JSONResponse:
    program = session.get(Program, program_id)
    if program is None:
        return _not_found()
    return _out(session, program)


@router.post(
    "",
    status_code=201,
    response_model=StaffProgramOut,
    responses={
        **STAFF_RESPONSES,
        **INVALID_REQUEST_RESPONSE,
        409: {
            "model": ErrorResponse,
            "description": "A program with this code already exists.",
            "content": {"application/json": {"example": {"error_code": PROGRAM_EXISTS, "message": "Program 6B06102 already exists."}}},
        },
    },
    summary="Add a program",
    description="The program has no document lists until they are added; until then its pages show the missing-data warning.",
)
def create_program(body: ProgramCreate, user: Staff, session: DbSession) -> StaffProgramOut | JSONResponse:
    if session.get(Program, body.program_id) is not None:
        return _error(409, PROGRAM_EXISTS, f"Program {body.program_id} already exists.")
    program = Program(**body.model_dump())
    _touch(program, user)
    session.add(program)
    session.commit()
    return _out(session, program)


@router.put(
    "/{program_id}",
    response_model=StaffProgramOut,
    responses={**STAFF_RESPONSES, **NOT_FOUND_RESPONSE, **INVALID_REQUEST_RESPONSE},
    summary="Change a program's facts",
    description="`is_active: false` archives the program: it leaves the catalogue, the comparison and the assistant's answers.",
)
def update_program(program_id: ProgramId, body: ProgramFields, user: Staff, session: DbSession) -> StaffProgramOut | JSONResponse:
    program = session.get(Program, program_id)
    if program is None:
        return _not_found()
    for field, value in body.model_dump().items():
        setattr(program, field, value)
    _touch(program, user)
    session.commit()
    return _out(session, program)


@router.put(
    "/{program_id}/documents/{applicant_type}",
    response_model=StaffProgramOut,
    responses={**STAFF_RESPONSES, **NOT_FOUND_RESPONSE, **INVALID_REQUEST_RESPONSE},
    summary="Replace the document list of one applicant type",
    description="The list replaces the old one in the given order. An empty list means no official list is "
    "published: the checklist then shows the missing-data warning.",
)
def replace_documents(
    program_id: ProgramId, applicant_type: ApplicantType, body: DocumentListIn, user: Staff, session: DbSession
) -> StaffProgramOut | JSONResponse:
    program = session.get(Program, program_id)
    if program is None:
        return _not_found()
    session.execute(
        delete(ProgramDocumentRequirement).where(
            ProgramDocumentRequirement.program_id == program_id,
            ProgramDocumentRequirement.applicant_type == applicant_type,
        )
    )
    session.add_all(
        ProgramDocumentRequirement(
            program_id=program_id,
            applicant_type=applicant_type,
            name=document.name,
            document_format=document.format,
            translation_required=document.translation,
            notarisation_required=document.notarisation,
            deadline=document.deadline,
            display_order=order,
        )
        for order, document in enumerate(body.documents)
    )
    _touch(program, user)
    session.commit()
    return _out(session, program)
