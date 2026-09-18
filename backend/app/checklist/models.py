"""Database model for US4 document requirements."""
from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ProgramDocumentRequirement(Base):
    __tablename__ = "program_document_requirement"
    __table_args__ = (
        CheckConstraint(
            "applicant_type IN ('local', 'international')",
            name="ck_requirement_applicant_type",
        ),
        CheckConstraint(
            "document_format IN ('original', 'copy')",
            name="ck_requirement_document_format",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("program.program_id", ondelete="CASCADE"), nullable=False, index=True
    )
    applicant_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_format: Mapped[str] = mapped_column(String(20), nullable=False)
    translation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notarisation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deadline: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
