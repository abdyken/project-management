from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

ADMIN = "admin"
OFFICER = "officer"
ROLES = (ADMIN, OFFICER)


class StaffUser(Base):
    """An admissions office account (US19). Accounts are created only with
    scripts/create_staff_user.py; there is no sign-up."""

    __tablename__ = "staff_user"
    __table_args__ = (CheckConstraint(f"role IN ('{ADMIN}', '{OFFICER}')", name="ck_staff_user_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored lower-case, so the login is case-insensitive.
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StaffSession(Base):
    """A logged-in browser. Only the SHA-256 of the cookie token is stored, so a
    database dump cannot be used to log in."""

    __tablename__ = "staff_session"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("staff_user.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
