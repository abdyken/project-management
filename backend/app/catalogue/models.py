from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

class Program(Base):
    __tablename__ = "program"
    __table_args__ = (
        CheckConstraint(
            "degree_level IN ('bachelor', 'master', 'phd')",
            name="ck_program_degree_level",
        ),
        CheckConstraint("tuition_per_ects_kzt >= 0", name="ck_program_tuition_kzt_non_negative"),
        CheckConstraint("tuition_per_ects_usd >= 0", name="ck_program_tuition_usd_non_negative"),
    )

    program_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ru: Mapped[str | None] = mapped_column(String(255))
    title_kk: Mapped[str | None] = mapped_column(String(255))
    faculty: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str | None] = mapped_column(String(50))
    tuition_per_ects_kzt: Mapped[int | None] = mapped_column(Integer)
    tuition_per_ects_usd: Mapped[int | None] = mapped_column(Integer)
    deadline_local: Mapped[date | None] = mapped_column(Date)
    deadline_international: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    # US21: the last staff edit; null for programs as imported from catalogue.json.
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("staff_user.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
