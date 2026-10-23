from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Applicant(Base):
    __tablename__ = "applicant"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    language: Mapped[str] = mapped_column(String(2), server_default="en")
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    verification_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApplicantSession(Base):
    __tablename__ = "applicant_session"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicant.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SavedProgram(Base):
    __tablename__ = "saved_program"
    __table_args__ = (CheckConstraint("applicant_type IN ('local', 'international')", name="ck_saved_applicant_type"),)

    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicant.id", ondelete="CASCADE"), primary_key=True)
    program_id: Mapped[str] = mapped_column(ForeignKey("program.program_id", ondelete="CASCADE"), primary_key=True)
    applicant_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentProgress(Base):
    __tablename__ = "document_progress"

    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicant.id", ondelete="CASCADE"), primary_key=True)
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("program_document_requirement.id", ondelete="CASCADE"), primary_key=True
    )


class DeadlineReminder(Base):
    """Delivery ledger: one message per saved checklist, deadline and milestone."""

    __tablename__ = "deadline_reminder"

    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicant.id", ondelete="CASCADE"), primary_key=True)
    program_id: Mapped[str] = mapped_column(ForeignKey("program.program_id", ondelete="CASCADE"), primary_key=True)
    applicant_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    deadline: Mapped[date] = mapped_column(Date, primary_key=True)
    milestone: Mapped[int] = mapped_column(primary_key=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
