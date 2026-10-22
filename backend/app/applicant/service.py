from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.errors import ApiProblem
from app.applicant.models import Applicant, ApplicantSession, DocumentProgress, SavedProgram
from app.applicant.schemas import SavedChecklistOut, TrackerItem
from app.catalogue.models import Program
from app.checklist.models import ProgramDocumentRequirement
from app.checklist.service import MISSING_REQUIREMENTS_WARNING, get_requirements
from app.config import Settings
from app.staff.passwords import DUMMY_HASH, verify_password
from app.staff.service import normalize_email


def now() -> datetime:
    return datetime.now(timezone.utc)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate(session: Session, email: str, password: str) -> Applicant | None:
    user = session.scalar(select(Applicant).where(Applicant.email == normalize_email(email)))
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    return user if user and user.verified and valid else None


def start_session(session: Session, user: Applicant, settings: Settings) -> str:
    token = secrets.token_urlsafe(32)
    session.execute(delete(ApplicantSession).where(ApplicantSession.expires_at <= now()))
    session.add(
        ApplicantSession(
            token_hash=token_hash(token),
            applicant_id=user.id,
            expires_at=now() + timedelta(hours=settings.applicant_session_hours),
        )
    )
    session.commit()
    return token


def user_for_token(session: Session, token: str | None) -> Applicant:
    if not token:
        raise ApiProblem(401, "NOT_LOGGED_IN", "Please log in.")
    user = session.scalar(
        select(Applicant)
        .join(ApplicantSession, ApplicantSession.applicant_id == Applicant.id)
        .where(
            ApplicantSession.token_hash == token_hash(token),
            ApplicantSession.expires_at > now(),
            Applicant.verified.is_(True),
        )
    )
    if user is None:
        raise ApiProblem(401, "NOT_LOGGED_IN", "Please log in.")
    return user


def active_program(session: Session, program_id: str) -> Program:
    program = session.get(Program, program_id)
    if program is None or not program.is_active:
        raise ApiProblem(404, "PROGRAM_NOT_FOUND", "Program not found.")
    return program


def saved_checklist(
    session: Session, user: Applicant, program_id: str, applicant_type: str, settings: Settings
) -> SavedChecklistOut:
    program = session.get(Program, program_id)
    if session.get(SavedProgram, (user.id, program_id, applicant_type)) is None or program is None:
        raise ApiProblem(404, "SAVED_PROGRAM_NOT_FOUND", "Save this checklist first.")
    return checklist_snapshot(session, program, applicant_type, settings, user)


def checklist_snapshot(
    session: Session, program: Program, applicant_type: str, settings: Settings, user: Applicant | None = None
) -> SavedChecklistOut:
    program_id = program.program_id
    requirements = get_requirements(session, program_id, applicant_type)
    completed = (
        set(session.scalars(select(DocumentProgress.requirement_id).where(DocumentProgress.applicant_id == user.id)))
        if user
        else set()
    )
    items = [
        TrackerItem(
            id=r.id,
            name=r.name,
            format=r.document_format,
            translation=r.translation_required,
            notarisation=r.notarisation_required,
            deadline=r.deadline,
            prepared=r.id in completed,
        )
        for r in requirements
    ]
    return SavedChecklistOut(
        program=program,
        applicant_type=applicant_type,
        items=items,
        prepared=sum(item.prepared for item in items),
        total=len(items),
        warning=None if items else MISSING_REQUIREMENTS_WARNING,
        contact=None if items else settings.admissions_office_contact,
    )


def save_program(session: Session, user: Applicant, program_id: str, applicant_type: str) -> None:
    active_program(session, program_id)
    session.execute(
        insert(SavedProgram)
        .values(
            applicant_id=user.id,
            program_id=program_id,
            applicant_type=applicant_type,
        )
        .on_conflict_do_nothing()
    )
    session.commit()


def remove_program(session: Session, user: Applicant, program_id: str, applicant_type: str) -> None:
    ids = select(ProgramDocumentRequirement.id).where(
        ProgramDocumentRequirement.program_id == program_id,
        ProgramDocumentRequirement.applicant_type == applicant_type,
    )
    session.execute(
        delete(DocumentProgress).where(
            DocumentProgress.applicant_id == user.id,
            DocumentProgress.requirement_id.in_(ids),
        )
    )
    session.execute(
        delete(SavedProgram).where(
            SavedProgram.applicant_id == user.id,
            SavedProgram.program_id == program_id,
            SavedProgram.applicant_type == applicant_type,
        )
    )
    session.commit()
