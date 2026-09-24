from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

UNANSWERED_QUESTION = "unanswered_question"
MISSING_DOCUMENTS = "missing_documents"


class AdmissionsFollowup(Base):
    __tablename__ = "admissions_followup"
    __table_args__ = (
        CheckConstraint(
            f"kind IN ('{UNANSWERED_QUESTION}', '{MISSING_DOCUMENTS}')", name="ck_admissions_followup_kind"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    question: Mapped[str | None] = mapped_column(Text)
    program_id: Mapped[str | None] = mapped_column(String(64))
    applicant_type: Mapped[str | None] = mapped_column(String(20))
    similarity_score: Mapped[float | None] = mapped_column(Float)
    session_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
