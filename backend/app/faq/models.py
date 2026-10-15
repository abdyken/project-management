from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

DRAFT = "draft"
PUBLISHED = "published"
RETIRED = "retired"
STATUSES = (DRAFT, PUBLISHED, RETIRED)


class FaqRecord(Base):
    """The official FAQ (US20): the source of truth since Sprint 4. Migration 0015 loaded
    it once from app/data/faq.json; the admissions office edits it in the staff area.
    Only published items are indexed (faq_embeddings) and used by the assistant."""

    __tablename__ = "faq_item"
    __table_args__ = (
        CheckConstraint(f"status IN ('{DRAFT}', '{PUBLISHED}', '{RETIRED}')", name="ck_faq_item_status"),
    )

    faq_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=PUBLISHED)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    source_link: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    question_ru: Mapped[str | None] = mapped_column(Text)
    answer_ru: Mapped[str | None] = mapped_column(Text)
    source_link_ru: Mapped[str | None] = mapped_column(String(500))
    evidence_ru: Mapped[str | None] = mapped_column(Text)
    question_kk: Mapped[str | None] = mapped_column(Text)
    answer_kk: Mapped[str | None] = mapped_column(Text)
    source_link_kk: Mapped[str | None] = mapped_column(String(500))
    evidence_kk: Mapped[str | None] = mapped_column(Text)
    degrees: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    applicant_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    # Date the facts were last checked, YYYY-MM-DD, as in faq.json; set on every staff edit.
    last_update: Mapped[str] = mapped_column(String(10), nullable=False)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("staff_user.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
