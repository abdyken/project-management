"""US31-US33: applications and their uploaded documents (ADR 0001-0003)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

DRAFT, SUBMITTED, IN_REVIEW, NEEDS_CHANGES, ACCEPTED, REJECTED = (
    "draft",
    "submitted",
    "in_review",
    "needs_changes",
    "accepted",
    "rejected",
)
STATUSES = (DRAFT, SUBMITTED, IN_REVIEW, NEEDS_CHANGES, ACCEPTED, REJECTED)
EDITABLE = (DRAFT, NEEDS_CHANGES)
EDUCATION_LEVELS = ("school", "college", "bachelor", "master")


class Application(Base):
    __tablename__ = "application"
    __table_args__ = (
        CheckConstraint(f"status IN {STATUSES}", name="ck_application_status"),
        CheckConstraint("applicant_type IN ('local', 'international')", name="ck_application_applicant_type"),
        CheckConstraint("language IN ('en', 'ru', 'kk')", name="ck_application_language"),
        CheckConstraint(f"education_level IS NULL OR education_level IN {EDUCATION_LEVELS}", name="ck_application_education"),
        # One live application per programme and applicant type; a rejected one may be followed by a new one.
        Index(
            "uq_application_live",
            "applicant_id",
            "program_id",
            "applicant_type",
            unique=True,
            postgresql_where=text("status <> 'rejected'"),
        ),
        Index("ix_application_queue", "status", "submitted_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicant.id", ondelete="CASCADE"), index=True)
    # RESTRICT: deleting a programme must not silently delete submitted applications and orphan their files.
    program_id: Mapped[str] = mapped_column(ForeignKey("program.program_id", ondelete="RESTRICT"), index=True)
    applicant_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), server_default=DRAFT)
    language: Mapped[str] = mapped_column(String(2), server_default="en")
    full_name: Mapped[str | None] = mapped_column(String(200))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    citizenship: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    education_level: Mapped[str | None] = mapped_column(String(20))
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    exam_total: Mapped[int | None] = mapped_column(Integer)
    consent: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    staff_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("staff_user.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The status the applicant was last e-mailed about; differs from `status` while an e-mail is due.
    notified_status: Mapped[str | None] = mapped_column(String(20))


class ApplicationDocument(Base):
    __tablename__ = "application_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("application.id", ondelete="CASCADE"), index=True)
    # The checklist document this scan is for; null for "other" or when staff removed the requirement.
    requirement_id: Mapped[int | None] = mapped_column(
        ForeignKey("program_document_requirement.id", ondelete="SET NULL"), index=True
    )
    original_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(50))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(64), unique=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
