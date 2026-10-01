from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

USER = "user"
ASSISTANT = "assistant"
ROLES = (USER, ASSISTANT)

# US11 constraint: turns are kept against the anonymous session id only and
# deleted after 30 days (see app/conversation/service.py::delete_expired_turns).
RETENTION_DAYS = 30


class ChatTurn(Base):
    """One message of a chat session. No applicant identity is stored - only the
    anonymous session id the widget generates."""

    __tablename__ = "chat_turn"
    __table_args__ = (
        CheckConstraint(f"role IN ('{USER}', '{ASSISTANT}')", name="ck_chat_turn_role"),
        Index("ix_chat_turn_session_created", "session_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Sources of an assistant turn: [{"faq_id": ..., "question": ..., "link": ...}]
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
