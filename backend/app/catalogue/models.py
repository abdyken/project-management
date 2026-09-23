from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

DEGREE_LEVELS = ("bachelor", "master", "phd")


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
    faculty: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    tuition_per_ects_kzt: Mapped[int | None] = mapped_column(Integer)
    tuition_per_ects_usd: Mapped[int | None] = mapped_column(Integer)
    deadline_local: Mapped[date | None] = mapped_column(Date)
    deadline_international: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
