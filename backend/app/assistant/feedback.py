from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AnswerFeedback(Base):
    __tablename__ = "answer_feedback"
    __table_args__ = (
        UniqueConstraint("answer_id", name="uq_answer_feedback_answer_id"),
        CheckConstraint("rating IN ('up', 'down')", name="ck_answer_feedback_rating"),
        CheckConstraint("rating = 'down' OR reason IS NULL", name="ck_answer_feedback_reason"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("chat_turn.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[str] = mapped_column(String(4), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(20))
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
