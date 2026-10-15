from __future__ import annotations

import hashlib
import secrets
import threading
from collections import deque
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.staff.models import ROLES, StaffSession, StaffUser
from app.staff.passwords import DUMMY_HASH, hash_password, verify_password

MAX_FAILED_LOGINS = 5
FAILED_LOGIN_WINDOW = timedelta(minutes=15)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


class LoginLimiter:
    """Failed logins per key (account e-mail and client IP) in a sliding window.

    Kept in memory: the API runs as one process, and a restart only resets the
    counters. The keys never hold the password."""

    def __init__(self, limit: int = MAX_FAILED_LOGINS, window: timedelta = FAILED_LOGIN_WINDOW) -> None:
        self.limit = limit
        self.window = window
        self._failures: dict[str, deque[datetime]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: datetime) -> deque[datetime]:
        failures = self._failures.setdefault(key, deque())
        while failures and now - failures[0] >= self.window:
            failures.popleft()
        return failures

    def blocked(self, *keys: str, now: datetime | None = None) -> bool:
        now = now or _now()
        with self._lock:
            return any(len(self._recent(key, now)) >= self.limit for key in keys)

    def record_failure(self, *keys: str, now: datetime | None = None) -> None:
        now = now or _now()
        with self._lock:
            for key in keys:
                self._recent(key, now).append(now)

    def reset(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._failures.pop(key, None)


login_limiter = LoginLimiter()


def authenticate(session: Session, email: str, password: str) -> StaffUser | None:
    user = session.scalar(select(StaffUser).where(StaffUser.email == normalize_email(email)))
    if user is None or not user.active:
        verify_password(password, DUMMY_HASH)
        return None
    return user if verify_password(password, user.password_hash) else None


def start_session(session: Session, user: StaffUser, lifetime: timedelta) -> str:
    """Store a new session for the user and return the token for the cookie."""
    token = secrets.token_urlsafe(32)
    now = _now()
    session.execute(delete(StaffSession).where(StaffSession.expires_at <= now))
    session.add(StaffSession(token_hash=_token_hash(token), user_id=user.id, expires_at=now + lifetime))
    user.last_login_at = now
    session.commit()
    return token


def user_for_token(session: Session, token: str | None) -> StaffUser | None:
    if not token:
        return None
    return session.scalar(
        select(StaffUser)
        .join(StaffSession, StaffSession.user_id == StaffUser.id)
        .where(
            StaffSession.token_hash == _token_hash(token),
            StaffSession.expires_at > _now(),
            StaffUser.active.is_(True),
        )
    )


def end_session(session: Session, token: str | None) -> None:
    if token:
        session.execute(delete(StaffSession).where(StaffSession.token_hash == _token_hash(token)))
        session.commit()


def create_user(session: Session, email: str, name: str, role: str, password: str) -> StaffUser:
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")
    email = normalize_email(email)
    if "@" not in email:
        raise ValueError("email is not valid")
    if session.scalar(select(StaffUser).where(StaffUser.email == email)) is not None:
        raise ValueError(f"{email} already has an account")
    user = StaffUser(email=email, name=name.strip(), role=role, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    return user


def _existing_user(session: Session, email: str) -> StaffUser:
    user = session.scalar(select(StaffUser).where(StaffUser.email == normalize_email(email)))
    if user is None:
        raise ValueError(f"{normalize_email(email)} has no account")
    return user


def set_password(session: Session, email: str, password: str) -> StaffUser:
    user = _existing_user(session, email)
    user.password_hash = hash_password(password)
    session.execute(delete(StaffSession).where(StaffSession.user_id == user.id))
    session.commit()
    return user


def set_active(session: Session, email: str, active: bool) -> StaffUser:
    user = _existing_user(session, email)
    user.active = active
    if not active:
        session.execute(delete(StaffSession).where(StaffSession.user_id == user.id))
    session.commit()
    return user


def list_users(session: Session) -> list[StaffUser]:
    return list(session.scalars(select(StaffUser).order_by(StaffUser.email)))
