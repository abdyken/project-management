from __future__ import annotations

from collections.abc import Callable, Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings, get_settings


STATEMENT_TIMEOUT_MS = 5000


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine_for(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3, "options": f"-c statement_timeout={STATEMENT_TIMEOUT_MS}"},
    )


def get_engine(settings: Settings):
    return get_engine_for(settings.database_url)


def get_session(settings: Settings) -> Session:
    SessionLocal = sessionmaker(bind=get_engine(settings), autoflush=False, expire_on_commit=False)
    return SessionLocal()


def get_db_session() -> Iterator[Session]:
    with get_session(get_settings()) as session:
        yield session


def get_session_factory() -> Callable[[], Session]:
    settings = get_settings()
    return lambda: get_session(settings)
