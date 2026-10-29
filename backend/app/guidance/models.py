from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ProgramGuidance(Base):
    __tablename__ = "program_guidance"

    program_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("program.program_id", ondelete="CASCADE"),
        primary_key=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff_user.id", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
