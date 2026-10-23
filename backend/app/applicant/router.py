from __future__ import annotations

import logging
import secrets
import smtplib
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.errors import ApiProblem, DATABASE_UNAVAILABLE_RESPONSE, ErrorResponse, INVALID_REQUEST_RESPONSE
from app.applicant import mail, service
from app.applicant.models import Applicant, ApplicantSession, DocumentProgress, SavedProgram
from app.applicant.schemas import (
    ApplicantOut,
    MessageOut,
    PreferencesIn,
    ProgressIn,
    RegisterRequest,
    SavedChecklistOut,
    SavedProgramsOut,
    VerifyRequest,
)
from app.checklist.models import ProgramDocumentRequirement
from app.checklist.schemas import ApplicantType
from app.config import get_settings
from app.db import get_db_session
from app.staff.passwords import hash_password
from app.staff.schemas import LoginRequest
from app.staff.service import LoginLimiter, normalize_email

COOKIE_NAME, COOKIE_PATH = "applicant_session", "/api/applicant"
login_limiter, register_limiter = LoginLimiter(), LoginLimiter()
Db = Annotated[Session, Depends(get_db_session)]
Token = Annotated[str | None, Cookie(alias=COOKIE_NAME, include_in_schema=False)]
logger = logging.getLogger(__name__)


def enabled(request: Request) -> None:
    settings = get_settings()
    if not settings.applicant_accounts_enabled:
        raise ApiProblem(503, "ACCOUNTS_UNAVAILABLE", "Applicant accounts are not available yet.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in {settings.public_base_url.rstrip("/"), *settings.cors_origin_list}:
            raise ApiProblem(403, "FORBIDDEN", "This request is not allowed.")


def current_applicant(session: Db, token: Token = None) -> Applicant:
    return service.user_for_token(session, token)


User = Annotated[Applicant, Depends(current_applicant)]
router = APIRouter(
    prefix="/applicant",
    tags=["applicant"],
    dependencies=[Depends(enabled)],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        **INVALID_REQUEST_RESPONSE,
        **DATABASE_UNAVAILABLE_RESPONSE,
    },
)


def client_ip(request: Request) -> str:
    # Use the socket address, never an untrusted forwarded header (uvicorn handles trusted proxies).
    return request.client.host if request.client else "unknown"


def set_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.applicant_cookie_secure,
        samesite="strict",
        max_age=settings.applicant_session_hours * 3600,
    )
    response.headers["Cache-Control"] = "no-store"


@router.post("/register", response_model=MessageOut, status_code=202)
def register(body: RegisterRequest, request: Request, session: Db) -> MessageOut:
    settings = get_settings()
    if not settings.smtp_host:
        raise ApiProblem(503, "MAIL_UNAVAILABLE", "E-mail delivery is not configured.")
    keys = (f"email:{body.email}", f"ip:{client_ip(request)}")
    if register_limiter.blocked(*keys):
        raise ApiProblem(429, "TOO_MANY_ATTEMPTS", "Please try again in 15 minutes.")
    register_limiter.record_failure(*keys)
    # Same response for an existing account; registration also resends an unexpired verification.
    user = session.scalar(select(Applicant).where(Applicant.email == body.email).with_for_update())
    if user is None:
        session.execute(
            insert(Applicant)
            .values(
                email=body.email,
                password_hash=hash_password(body.password),
                language=body.language,
            )
            .on_conflict_do_nothing(index_elements=[Applicant.email])
        )
        user = session.scalar(select(Applicant).where(Applicant.email == body.email).with_for_update())
    if not user.verified:
        user.password_hash = hash_password(body.password)
        user.language = body.language
        token = secrets.token_urlsafe(32)
        user.verification_hash = service.token_hash(token)
        user.verification_expires_at = service.now() + timedelta(hours=24)
        subjects = {
            "en": "Verify your SDU applicant account",
            "ru": "Подтвердите аккаунт абитуриента SDU",
            "kk": "SDU талапкер аккаунтын растаңыз",
        }
        instructions = {
            "en": "Confirm your e-mail using this link (valid for 24 hours):",
            "ru": "Подтвердите почту по ссылке (действует 24 часа):",
            "kk": "Поштаны сілтеме арқылы растаңыз (24 сағат жарамды):",
        }
        try:
            mail.send_mail(
                settings,
                user.email,
                subjects[user.language],
                f"{instructions[user.language]}\n\n{settings.public_base_url.rstrip('/')}/account/verify#token={token}\n",
            )
        except (OSError, smtplib.SMTPException):
            session.rollback()
            raise ApiProblem(503, "MAIL_UNAVAILABLE", "E-mail could not be sent. Please try again.") from None
        session.commit()
    return MessageOut(message="If the account needs verification, a link has been sent to your e-mail.")


@router.post("/verify", response_model=ApplicantOut)
def verify(body: VerifyRequest, response: Response, session: Db) -> ApplicantOut:
    user = session.scalar(
        select(Applicant)
        .where(
            Applicant.verification_hash == service.token_hash(body.token),
            Applicant.verification_expires_at > service.now(),
            Applicant.verified.is_(False),
        )
        .with_for_update()
    )
    if user is None:
        raise ApiProblem(422, "INVALID_VERIFICATION", "This verification link is invalid or expired.")
    user.verified, user.verification_hash, user.verification_expires_at = True, None, None
    set_cookie(response, service.start_session(session, user, get_settings()))
    return ApplicantOut.model_validate(user)


@router.post("/login", response_model=ApplicantOut)
def login(body: LoginRequest, request: Request, response: Response, session: Db, token: Token = None) -> ApplicantOut:
    keys = (f"email:{normalize_email(body.email)}", f"ip:{client_ip(request)}")
    if login_limiter.blocked(*keys):
        raise ApiProblem(429, "TOO_MANY_ATTEMPTS", "Please try again in 15 minutes.")
    user = service.authenticate(session, body.email, body.password)
    if user is None:
        login_limiter.record_failure(*keys)
        raise ApiProblem(401, "INVALID_CREDENTIALS", "Wrong e-mail or password, or e-mail not verified.")
    login_limiter.reset(keys[0])
    if token:
        session.execute(delete(ApplicantSession).where(ApplicantSession.token_hash == service.token_hash(token)))
    set_cookie(response, service.start_session(session, user, get_settings()))
    return ApplicantOut.model_validate(user)


@router.post("/logout", status_code=204)
def logout(session: Db, token: Token = None) -> Response:
    if token:
        session.execute(delete(ApplicantSession).where(ApplicantSession.token_hash == service.token_hash(token)))
        session.commit()
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH)
    return response


@router.get("/me", response_model=ApplicantOut)
def me(user: User) -> ApplicantOut:
    return ApplicantOut.model_validate(user)


@router.patch("/me", response_model=ApplicantOut)
def preferences(body: PreferencesIn, user: User, session: Db) -> ApplicantOut:
    user.language, user.reminders_enabled = body.language, body.reminders_enabled
    session.commit()
    return ApplicantOut.model_validate(user)


@router.delete("/me", status_code=204)
def delete_account(user: User, session: Db) -> Response:
    session.delete(user)
    session.commit()
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH)
    return response


@router.get("/programs", response_model=SavedProgramsOut)
def programs(user: User, session: Db) -> SavedProgramsOut:
    saved = session.scalars(
        select(SavedProgram)
        .where(SavedProgram.applicant_id == user.id)
        .order_by(SavedProgram.created_at, SavedProgram.program_id, SavedProgram.applicant_type)
    )
    return SavedProgramsOut(
        items=[
            service.saved_checklist(session, user, row.program_id, row.applicant_type, get_settings()) for row in saved
        ]
    )


@router.put("/programs/{program_id}/{applicant_type}", response_model=SavedChecklistOut)
def save(program_id: str, applicant_type: ApplicantType, user: User, session: Db) -> SavedChecklistOut:
    service.save_program(session, user, program_id, applicant_type)
    return service.saved_checklist(session, user, program_id, applicant_type, get_settings())


@router.delete("/programs/{program_id}/{applicant_type}", status_code=204)
def unsave(program_id: str, applicant_type: ApplicantType, user: User, session: Db) -> Response:
    service.remove_program(session, user, program_id, applicant_type)
    return Response(status_code=204)


@router.get("/programs/{program_id}/{applicant_type}", response_model=SavedChecklistOut)
def tracker(program_id: str, applicant_type: ApplicantType, user: User, session: Db) -> SavedChecklistOut:
    return service.saved_checklist(session, user, program_id, applicant_type, get_settings())


@router.put("/programs/{program_id}/{applicant_type}/documents/{requirement_id}", response_model=SavedChecklistOut)
def progress(
    program_id: str, applicant_type: ApplicantType, requirement_id: int, body: ProgressIn, user: User, session: Db
) -> SavedChecklistOut:
    service.saved_checklist(session, user, program_id, applicant_type, get_settings())
    service.active_program(session, program_id)
    requirement = session.get(ProgramDocumentRequirement, requirement_id)
    if requirement is None or (requirement.program_id, requirement.applicant_type) != (program_id, applicant_type):
        raise ApiProblem(404, "DOCUMENT_NOT_FOUND", "This document is no longer in the checklist. Refresh the page.")
    if body.prepared:
        session.execute(
            insert(DocumentProgress)
            .values(applicant_id=user.id, requirement_id=requirement_id)
            .on_conflict_do_nothing()
        )
    else:
        session.execute(
            delete(DocumentProgress).where(
                DocumentProgress.applicant_id == user.id, DocumentProgress.requirement_id == requirement_id
            )
        )
    session.commit()
    return service.saved_checklist(session, user, program_id, applicant_type, get_settings())


@router.get(
    "/programs/{program_id}/{applicant_type}/pdf",
    responses={200: {"content": {"application/pdf": {}}}},
    response_class=Response,
)
def download_pdf(
    program_id: str,
    applicant_type: ApplicantType,
    user: User,
    session: Db,
    language: Annotated[str, Query(pattern="^(en|ru|kk)$")] = "en",
) -> Response:
    from app.checklist.pdf import checklist_pdf

    checklist = service.saved_checklist(session, user, program_id, applicant_type, get_settings())
    return Response(
        checklist_pdf(checklist, language, get_settings().admissions_office_contact),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SDU-checklist-{applicant_type}-{language}.pdf"'},
    )
