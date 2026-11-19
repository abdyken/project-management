"""US31-US33 and US6: applicant and staff endpoints for online applications."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import ApiProblem, ErrorResponse
from app.applicant.models import Applicant, DocumentProgress
from app.applicant.router import User, enabled
from app.applicant.service import now
from app.applications import storage
from app.applications.models import (
    ACCEPTED,
    DRAFT,
    EDITABLE,
    IN_REVIEW,
    NEEDS_CHANGES,
    REJECTED,
    SUBMITTED,
    Application,
    ApplicationDocument,
)
from app.applications.schemas import (
    ApplicationCreate,
    ApplicationFields,
    ApplicationOut,
    ApplicationsOut,
    ApplicationSummary,
    DocumentOut,
    RequirementOut,
    StaffApplicationOut,
    StaffApplicationsOut,
    StaffApplicationSummary,
    StatusAnswerOut,
    StatusIn,
    StatusLine,
)
from app.applications.service import NOTE_REQUIRED, NOTIFY, STAFF_TRANSITIONS, notify_now, status_answer, status_lines, touch
from app.catalogue.models import Program
from app.catalogue.schemas import ProgramOut
from app.checklist.service import get_requirements
from app.config import Settings, get_settings
from app.db import get_db_session, get_session_factory
from app.staff.models import StaffUser
from app.staff.router import require_staff

logger = logging.getLogger(__name__)

MAX_LIVE_APPLICATIONS = 10
MAX_DOCUMENTS = 20
REQUIRED_FIELDS = ("full_name", "date_of_birth", "citizenship", "phone", "education_level", "graduation_year")

Db = Annotated[Session, Depends(get_db_session)]
Staff = Annotated[StaffUser, Depends(require_staff())]
SessionFactory = Callable[[], AbstractContextManager[Session]]
OpenSession = Annotated[SessionFactory, Depends(get_session_factory)]
ERRORS = {code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 413, 415, 422, 503)}


def applications_on() -> None:
    settings = get_settings()
    if not (settings.applications_enabled and settings.applicant_accounts_enabled):
        raise ApiProblem(503, "APPLICATIONS_UNAVAILABLE", "Online applications are not available yet.")


applicant_router = APIRouter(
    prefix="/applicant/applications",
    tags=["applicant: applications"],
    dependencies=[Depends(applications_on), Depends(enabled)],
    responses=ERRORS,
)
staff_router = APIRouter(
    prefix="/staff/applications",
    tags=["staff: applications"],
    dependencies=[Depends(applications_on)],
    responses=ERRORS,
)


# ---- shared helpers


def _program_out(session: Session, program_id: str) -> ProgramOut:
    return ProgramOut.model_validate(session.get(Program, program_id))


def _documents(session: Session, application: Application) -> list[ApplicationDocument]:
    return list(
        session.scalars(
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == application.id)
            .order_by(ApplicationDocument.uploaded_at, ApplicationDocument.id)
        )
    )


def _missing(application: Application, documents: list[ApplicationDocument]) -> list[str]:
    missing = [field for field in REQUIRED_FIELDS if getattr(application, field) in (None, "")]
    if not application.consent:
        missing.append("consent")
    if not documents:
        missing.append("documents")
    return missing


def _detail(session: Session, application: Application, settings: Settings) -> dict:
    documents = _documents(session, application)
    uploaded = {document.requirement_id for document in documents}
    requirements = [
        RequirementOut(
            id=row.id,
            name=row.name,
            format=row.document_format,
            translation=row.translation_required,
            notarisation=row.notarisation_required,
            deadline=row.deadline,
            uploaded=row.id in uploaded,
        )
        for row in get_requirements(session, application.program_id, application.applicant_type)
    ]
    return dict(
        id=application.id,
        program=_program_out(session, application.program_id),
        applicant_type=application.applicant_type,
        status=application.status,
        language=application.language,
        full_name=application.full_name,
        date_of_birth=application.date_of_birth,
        citizenship=application.citizenship,
        phone=application.phone,
        education_level=application.education_level,
        graduation_year=application.graduation_year,
        exam_total=application.exam_total,
        consent=application.consent,
        staff_note=application.staff_note,
        editable=application.status in EDITABLE,
        created_at=application.created_at,
        updated_at=application.updated_at,
        submitted_at=application.submitted_at,
        status_changed_at=application.status_changed_at,
        requirements=requirements,
        documents=[DocumentOut.model_validate(document) for document in documents],
        bytes_used=sum(document.size_bytes for document in documents),
        bytes_limit=settings.application_max_bytes,
        missing=_missing(application, documents),
    )


def _document_counts(session: Session, ids: list[int]) -> dict[int, int]:
    if not ids:
        return {}
    return dict(
        session.execute(
            select(ApplicationDocument.application_id, func.count())
            .where(ApplicationDocument.application_id.in_(ids))
            .group_by(ApplicationDocument.application_id)
        ).all()
    )


def _file_response(settings: Settings, document: ApplicationDocument) -> FileResponse:
    path = storage.file_path(settings, document.storage_key)
    if not path.is_file():
        logger.error("Uploaded file %s of document %s is missing on disk.", document.storage_key, document.id)
        raise ApiProblem(404, "DOCUMENT_NOT_FOUND", "Document not found.")
    return FileResponse(
        path,
        media_type=document.content_type,
        filename=document.original_name,
        content_disposition_type="attachment",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


# ---- applicant


def _own(session: Session, user: Applicant, application_id: int, lock: bool = False) -> Application:
    query = select(Application).where(Application.id == application_id, Application.applicant_id == user.id)
    application = session.scalar(query.with_for_update() if lock else query)
    if application is None:
        raise ApiProblem(404, "APPLICATION_NOT_FOUND", "Application not found.")
    return application


def _editable(application: Application) -> None:
    if application.status not in EDITABLE:
        raise ApiProblem(409, "APPLICATION_LOCKED", "This application can no longer be changed.")


@applicant_router.get("", response_model=ApplicationsOut)
def my_applications(user: User, session: Db) -> ApplicationsOut:
    rows = list(
        session.scalars(
            select(Application)
            .where(Application.applicant_id == user.id)
            .order_by(Application.updated_at.desc(), Application.id.desc())
        )
    )
    counts = _document_counts(session, [row.id for row in rows])
    items = [
        ApplicationSummary(
            id=row.id,
            program=_program_out(session, row.program_id),
            applicant_type=row.applicant_type,
            status=row.status,
            updated_at=row.updated_at,
            submitted_at=row.submitted_at,
            documents=counts.get(row.id, 0),
        )
        for row in rows
    ]
    return ApplicationsOut(items=items, total=len(items))


@applicant_router.get("/status", response_model=StatusAnswerOut, summary="US6: stage and next step for the chat")
def my_status(
    user: User, session: Db, response: Response, language: Annotated[Literal["en", "ru", "kk"], Query()] = "en"
) -> StatusAnswerOut:
    response.headers["Cache-Control"] = "no-store"
    rows = list(
        session.scalars(
            select(Application)
            .where(Application.applicant_id == user.id)
            .order_by(Application.updated_at.desc(), Application.id.desc())
        )
    )
    lines = status_lines(session, rows, language)
    return StatusAnswerOut(
        answer=status_answer(session, user, language),
        items=[
            StatusLine(id=row.id, program_id=row.program_id, status=row.status, stage=stage, next_step=next_step)
            for row, (stage, next_step) in zip(rows, lines, strict=True)
        ],
    )


@applicant_router.post("", response_model=ApplicationOut, status_code=201)
def start_application(body: ApplicationCreate, user: User, session: Db) -> ApplicationOut:
    # Serialise this applicant's creates so two clicks cannot pass the checks together.
    session.scalar(select(Applicant).where(Applicant.id == user.id).with_for_update())
    program = session.get(Program, body.program_id)
    if program is None or not program.is_active:
        raise ApiProblem(404, "PROGRAM_NOT_FOUND", "Programme not found.")
    live = select(Application).where(Application.applicant_id == user.id, Application.status != REJECTED)
    if session.scalar(live.where(Application.program_id == body.program_id, Application.applicant_type == body.applicant_type)):
        raise ApiProblem(409, "APPLICATION_EXISTS", "You already have an application for this programme.")
    if session.scalar(select(func.count()).select_from(live.subquery())) >= MAX_LIVE_APPLICATIONS:
        raise ApiProblem(409, "TOO_MANY_APPLICATIONS", f"You can have at most {MAX_LIVE_APPLICATIONS} applications.")
    application = Application(
        applicant_id=user.id,
        program_id=body.program_id,
        applicant_type=body.applicant_type,
        language=body.language,
        status=DRAFT,
    )
    session.add(application)
    session.commit()
    session.refresh(application)
    return ApplicationOut(**_detail(session, application, get_settings()))


@applicant_router.get("/{application_id}", response_model=ApplicationOut)
def my_application(application_id: int, user: User, session: Db, response: Response) -> ApplicationOut:
    response.headers["Cache-Control"] = "no-store"
    return ApplicationOut(**_detail(session, _own(session, user, application_id), get_settings()))


@applicant_router.put("/{application_id}", response_model=ApplicationOut)
def save_form(application_id: int, body: ApplicationFields, user: User, session: Db) -> ApplicationOut:
    application = _own(session, user, application_id, lock=True)
    _editable(application)
    for field, value in body.model_dump(exclude={"language"}).items():
        setattr(application, field, value)
    if body.language:
        application.language = body.language
    touch(application)
    session.commit()
    return ApplicationOut(**_detail(session, application, get_settings()))


@applicant_router.post("/{application_id}/submit", response_model=ApplicationOut)
def submit(application_id: int, user: User, session: Db) -> ApplicationOut:
    application = _own(session, user, application_id, lock=True)
    _editable(application)
    missing = _missing(application, _documents(session, application))
    if missing:
        raise ApiProblem(422, "APPLICATION_INCOMPLETE", "Complete the application first: " + ", ".join(missing))
    application.status, application.submitted_at = SUBMITTED, now()
    application.status_changed_at = application.submitted_at
    touch(application)
    session.commit()
    return ApplicationOut(**_detail(session, application, get_settings()))


@applicant_router.delete("/{application_id}", status_code=204)
def delete_draft(application_id: int, user: User, session: Db) -> Response:
    application = _own(session, user, application_id, lock=True)
    if application.status != DRAFT:
        raise ApiProblem(409, "APPLICATION_LOCKED", "Only a draft can be deleted.")
    keys = [document.storage_key for document in _documents(session, application)]
    session.delete(application)
    session.commit()
    storage.delete_files(get_settings(), keys)
    return Response(status_code=204)


def _upload_room(
    session: Session, settings: Settings, application: Application, user: Applicant, requirement_id: int | None
) -> tuple[int, str]:
    """Bytes this upload may use and the error code when it would go over (ADR 0003)."""
    _editable(application)
    documents = _documents(session, application)
    if len(documents) >= MAX_DOCUMENTS:
        raise ApiProblem(409, "TOO_MANY_DOCUMENTS", f"An application can have at most {MAX_DOCUMENTS} documents.")
    if requirement_id is not None and requirement_id not in {
        row.id for row in get_requirements(session, application.program_id, application.applicant_type)
    }:
        raise ApiProblem(422, "INVALID_REQUIREMENT", "This document is not on the programme's checklist.")
    used_by_applicant = session.scalar(
        select(func.coalesce(func.sum(ApplicationDocument.size_bytes), 0))
        .join(Application, Application.id == ApplicationDocument.application_id)
        .where(Application.applicant_id == user.id)
    )
    limits = [
        (settings.upload_max_bytes, "FILE_TOO_LARGE"),
        (settings.application_max_bytes - sum(document.size_bytes for document in documents), "APPLICATION_FULL"),
        (settings.applicant_max_bytes - used_by_applicant, "ACCOUNT_STORAGE_FULL"),
    ]
    room, code = min(limits)
    if room <= 0:
        raise ApiProblem(413, code, "There is no room left for this file.")
    return room, code


@applicant_router.post("/{application_id}/documents", response_model=DocumentOut, status_code=201)
def upload_document(
    application_id: int,
    user: User,
    session: Db,
    file: Annotated[UploadFile, File(description="PDF, JPEG or PNG, up to 10 MB")],
    requirement_id: Annotated[int | None, Form()] = None,
) -> DocumentOut:
    settings = get_settings()
    storage.ensure_free_space(settings)
    # Check first, write the file without holding the row lock, then check again under it:
    # a slow disk must not block the applicant's other tabs or staff.
    room, code = _upload_room(session, settings, _own(session, user, application_id), user, requirement_id)
    session.rollback()
    try:
        stored = storage.save_upload(file.file, settings, room)
    except ApiProblem as problem:
        if problem.code == "FILE_TOO_LARGE" and code != "FILE_TOO_LARGE":
            raise ApiProblem(413, code, "There is no room left for this file.") from None
        raise
    try:
        application = _own(session, user, application_id, lock=True)
        room, code = _upload_room(session, settings, application, user, requirement_id)
        if stored.size_bytes > room:
            raise ApiProblem(413, code, "There is no room left for this file.")
        document = ApplicationDocument(
            application_id=application.id,
            requirement_id=requirement_id,
            original_name=storage.download_name(file.filename, stored.content_type),
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            storage_key=stored.storage_key,
        )
        session.add(document)
        if requirement_id is not None:
            # A scan of a checklist document also ticks it in the tracker (US25).
            session.execute(
                insert(DocumentProgress)
                .values(applicant_id=user.id, requirement_id=requirement_id)
                .on_conflict_do_nothing()
            )
        touch(application)
        session.commit()
    except BaseException:
        session.rollback()
        storage.delete_files(settings, [stored.storage_key])
        raise
    session.refresh(document)
    return DocumentOut.model_validate(document)


def _own_document(session: Session, application: Application, document_id: int) -> ApplicationDocument:
    document = session.scalar(
        select(ApplicationDocument).where(
            ApplicationDocument.id == document_id, ApplicationDocument.application_id == application.id
        )
    )
    if document is None:
        raise ApiProblem(404, "DOCUMENT_NOT_FOUND", "Document not found.")
    return document


@applicant_router.get("/{application_id}/documents/{document_id}", response_class=FileResponse)
def download_my_document(application_id: int, document_id: int, user: User, session: Db) -> FileResponse:
    application = _own(session, user, application_id)
    return _file_response(get_settings(), _own_document(session, application, document_id))


@applicant_router.delete("/{application_id}/documents/{document_id}", status_code=204)
def delete_document(application_id: int, document_id: int, user: User, session: Db) -> Response:
    application = _own(session, user, application_id, lock=True)
    _editable(application)
    document = _own_document(session, application, document_id)
    key = document.storage_key
    session.delete(document)
    touch(application)
    session.commit()
    storage.delete_files(get_settings(), [key])
    return Response(status_code=204)


# ---- staff (US33)

QueueFilter = Literal["open", "submitted", "in_review", "needs_changes", "accepted", "rejected", "all"]
QUEUE = {
    "open": (SUBMITTED, IN_REVIEW),
    "all": (SUBMITTED, IN_REVIEW, NEEDS_CHANGES, ACCEPTED, REJECTED),
}


def _staff_application(session: Session, application_id: int, lock: bool = False) -> Application:
    query = select(Application).where(Application.id == application_id, Application.status != DRAFT)
    application = session.scalar(query.with_for_update() if lock else query)
    if application is None:
        raise ApiProblem(404, "APPLICATION_NOT_FOUND", "Application not found.")
    return application


@staff_router.get("", response_model=StaffApplicationsOut)
def queue(
    session: Db,
    _: Staff,
    response: Response,
    status: QueueFilter = "open",
    program_id: Annotated[str | None, Query(max_length=64)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> StaffApplicationsOut:
    response.headers["Cache-Control"] = "no-store"
    statuses = QUEUE.get(status, (status,))
    query = select(Application).where(Application.status.in_(statuses))
    if program_id:
        query = query.where(Application.program_id == program_id)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    # Oldest submission first, so nobody waits at the bottom of the queue.
    rows = list(
        session.scalars(
            query.order_by(Application.submitted_at.asc().nulls_last(), Application.id).offset(offset).limit(limit)
        )
    )
    counts = _document_counts(session, [row.id for row in rows])
    emails = dict(
        session.execute(select(Applicant.id, Applicant.email).where(Applicant.id.in_({row.applicant_id for row in rows}))).all()
    )
    items = [
        StaffApplicationSummary(
            id=row.id,
            program=_program_out(session, row.program_id),
            applicant_type=row.applicant_type,
            status=row.status,
            updated_at=row.updated_at,
            submitted_at=row.submitted_at,
            documents=counts.get(row.id, 0),
            applicant_email=emails.get(row.applicant_id, ""),
            full_name=row.full_name,
        )
        for row in rows
    ]
    return StaffApplicationsOut(items=items, total=total)


@staff_router.get("/{application_id}", response_model=StaffApplicationOut)
def staff_application(application_id: int, session: Db, _: Staff, response: Response) -> StaffApplicationOut:
    response.headers["Cache-Control"] = "no-store"
    application = _staff_application(session, application_id)
    applicant = session.get(Applicant, application.applicant_id)
    return StaffApplicationOut(**_detail(session, application, get_settings()), applicant_email=applicant.email)


@staff_router.get("/{application_id}/documents/{document_id}", response_class=FileResponse)
def staff_document(application_id: int, document_id: int, session: Db, _: Staff) -> FileResponse:
    application = _staff_application(session, application_id)
    return _file_response(get_settings(), _own_document(session, application, document_id))


@staff_router.post("/{application_id}/status", response_model=StaffApplicationOut)
def set_status(
    application_id: int,
    body: StatusIn,
    request: Request,
    session: Db,
    user: Staff,
    background: BackgroundTasks,
    open_session: OpenSession,
) -> StaffApplicationOut:
    # Staff cookies are SameSite=Strict; also reject untrusted origins (same check as US30 answers).
    enabled(request)
    application = _staff_application(session, application_id, lock=True)
    if body.status not in STAFF_TRANSITIONS.get(application.status, ()):
        raise ApiProblem(409, "INVALID_STATUS_CHANGE", f"An application that is {application.status} cannot become {body.status}.")
    if body.status in NOTE_REQUIRED and not body.note:
        raise ApiProblem(422, "NOTE_REQUIRED", "Write a note to the applicant.")
    application.status, application.staff_note = body.status, body.note
    application.reviewed_by_id, application.status_changed_at = user.id, now()
    # Every change is a new event: a second "changes requested" must be e-mailed again.
    application.notified_status = None
    touch(application)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiProblem(409, "CONFLICT", "The application changed meanwhile. Reload it.") from None
    if body.status in NOTIFY:
        background.add_task(notify_now, open_session, get_settings(), application.id)
    applicant = session.get(Applicant, application.applicant_id)
    return StaffApplicationOut(**_detail(session, application, get_settings()), applicant_email=applicant.email)
