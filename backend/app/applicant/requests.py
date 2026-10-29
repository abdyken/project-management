"""US30: durable private questions, one staff answer and retryable notifications."""

from __future__ import annotations

import smtplib
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.api.errors import ApiProblem, ErrorResponse
from app.applicant import mail
from app.applicant.models import Applicant
from app.applicant.router import User, enabled
from app.applicant.service import now
from app.config import Settings
from app.db import Base, get_db_session
from app.staff.models import StaffUser
from app.staff.router import require_staff


class AdmissionsRequest(Base):
    __tablename__ = "admissions_request"
    __table_args__ = (
        UniqueConstraint("applicant_id", "client_key", name="uq_request_client_key"),
        CheckConstraint("language IN ('en','ru','kk')", name="ck_request_language"),
        Index("ix_request_applicant", "applicant_id"),
        Index("ix_request_created", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("applicant.id", ondelete="CASCADE")
    )
    client_key: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    answer: Mapped[str | None] = mapped_column(Text)
    answered_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff_user.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )


class RequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    client_key: str = Field(min_length=16, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    language: Literal["en", "ru", "kk"] = "en"

    @field_validator("question")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Enter a question")
        return value.strip()


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=6000)

    @field_validator("answer")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Enter an answer")
        return value.strip()


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question: str
    language: str
    answer: str | None
    created_at: datetime
    answered_at: datetime | None
    notification_sent_at: datetime | None


class RequestsOut(BaseModel):
    items: list[RequestOut]
    total: int


Db = Annotated[Session, Depends(get_db_session)]
Staff = Annotated[StaffUser, Depends(require_staff())]
applicant_router = APIRouter(
    prefix="/applicant/requests",
    tags=["applicant: requests"],
    dependencies=[Depends(enabled)],
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 429, 503)
    },
)
staff_router = APIRouter(
    prefix="/staff/requests",
    tags=["staff: requests"],
    responses={
        code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 503)
    },
)


@applicant_router.post("", response_model=RequestOut, status_code=201)
def create(body: RequestIn, user: User, session: Db):
    # Serialize this applicant's submissions, including simultaneous retries.
    session.scalar(select(Applicant).where(Applicant.id == user.id).with_for_update())
    existing = session.scalar(
        select(AdmissionsRequest).where(
            AdmissionsRequest.applicant_id == user.id,
            AdmissionsRequest.client_key == body.client_key,
        )
    )
    if existing:
        if existing.question != body.question or existing.language != body.language:
            raise ApiProblem(
                409, "REQUEST_KEY_REUSED", "Use a new key for a different question."
            )
        return existing
    count = session.scalar(
        select(func.count())
        .select_from(AdmissionsRequest)
        .where(
            AdmissionsRequest.applicant_id == user.id,
            AdmissionsRequest.created_at > now() - timedelta(hours=1),
        )
    )
    if count >= 5:
        raise ApiProblem(
            429, "TOO_MANY_REQUESTS", "Send at most five questions per hour."
        )
    row = AdmissionsRequest(
        applicant_id=user.id,
        client_key=body.client_key,
        question=body.question,
        language=body.language,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _list(session: Session, query, offset: int, limit: int) -> RequestsOut:
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.scalars(
        query.order_by(AdmissionsRequest.created_at.desc(), AdmissionsRequest.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return RequestsOut(
        items=[RequestOut.model_validate(row) for row in rows], total=total
    )


@applicant_router.get("", response_model=RequestsOut)
def mine(
    user: User,
    session: Db,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
):
    return _list(
        session,
        select(AdmissionsRequest).where(AdmissionsRequest.applicant_id == user.id),
        offset,
        limit,
    )


@applicant_router.get("/{request_id}", response_model=RequestOut)
def my_request(request_id: int, user: User, session: Db):
    row = session.scalar(
        select(AdmissionsRequest).where(
            AdmissionsRequest.id == request_id,
            AdmissionsRequest.applicant_id == user.id,
        )
    )
    if row is None:
        raise ApiProblem(404, "REQUEST_NOT_FOUND", "Request not found.")
    return row


@staff_router.get("", response_model=RequestsOut)
def queue(
    session: Db,
    _: Staff,
    status: Literal["new", "answered", "all"] = "new",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
):
    query = select(AdmissionsRequest)
    if status != "all":
        query = query.where(
            AdmissionsRequest.answer.is_(None)
            if status == "new"
            else AdmissionsRequest.answer.is_not(None)
        )
    return _list(session, query, offset, limit)


@staff_router.get("/{request_id}", response_model=RequestOut)
def staff_request(request_id: int, session: Db, _: Staff):
    row = session.get(AdmissionsRequest, request_id)
    if row is None:
        raise ApiProblem(404, "REQUEST_NOT_FOUND", "Request not found.")
    return row


@staff_router.post("/{request_id}/answer", response_model=RequestOut)
def answer(request_id: int, body: AnswerIn, request: Request, session: Db, user: Staff):
    # Staff cookies are protected by SameSite=Strict; reject untrusted origins too.
    enabled(request)
    row = session.scalar(
        select(AdmissionsRequest)
        .where(AdmissionsRequest.id == request_id)
        .with_for_update()
    )
    if row is None:
        raise ApiProblem(404, "REQUEST_NOT_FOUND", "Request not found.")
    if row.answer is not None:
        if row.answer != body.answer:
            raise ApiProblem(
                409, "ALREADY_ANSWERED", "This request has already been answered."
            )
        return row
    row.answer, row.answered_by_id, row.answered_at = body.answer, user.id, now()
    session.commit()  # Notification failures cannot discard the answer.
    session.refresh(row)
    return row


def send_request_notifications(session: Session, settings: Settings) -> int:
    if not settings.applicant_accounts_enabled or not settings.smtp_host:
        return 0
    sent = 0
    ids = list(
        session.scalars(
            select(AdmissionsRequest.id).where(
                AdmissionsRequest.answer.is_not(None),
                AdmissionsRequest.notification_sent_at.is_(None),
            )
        )
    )
    for request_id in ids:
        row = session.scalar(
            select(AdmissionsRequest)
            .where(
                AdmissionsRequest.id == request_id,
                AdmissionsRequest.notification_sent_at.is_(None),
            )
            .with_for_update(skip_locked=True)
        )
        if row is None:
            session.commit()
            continue
        user = session.get(Applicant, row.applicant_id)
        if not user or not user.verified:
            session.commit()
            continue
        subject, text = {
            "en": (
                "SDU: the admissions office answered your question",
                "Read your answer in your account",
            ),
            "ru": (
                "SDU: приёмная комиссия ответила на ваш вопрос",
                "Прочитайте ответ в личном кабинете",
            ),
            "kk": (
                "SDU: қабылдау комиссиясы сұрағыңызға жауап берді",
                "Жауапты жеке кабинеттен оқыңыз",
            ),
        }[row.language]
        # No private question/answer text or tracking token in an e-mail.
        try:
            mail.send_mail(
                settings,
                user.email,
                subject,
                f"{text}: {settings.public_base_url.rstrip('/')}/account/requests\n",
            )
        except (OSError, smtplib.SMTPException):
            session.rollback()
            continue
        row.notification_sent_at = now()
        session.commit()
        sent += 1
    return sent
