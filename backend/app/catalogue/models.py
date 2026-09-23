from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, Numeric, String, true
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
        CheckConstraint("tuition_fee >= 0", name="ck_program_tuition_fee_non_negative"),
    )

    program_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    tuition_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    application_deadline: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
