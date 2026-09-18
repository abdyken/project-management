"""SQLAlchemy engine/session setup (T0.1 stack decision: SQLAlchemy + Alembic,
PostgreSQL 16 + pgvector).

Only the ``assistant`` module's own table (``faq_embeddings``, see
``app/assistant/models.py``) lives behind this for now. Once T0.3 (Dinmukhamed)
lands the shared backend skeleton, this file's ``Base``/``get_engine`` should
be replaced by the shared one and the Alembic history in ``migrations/``
merged into the project-wide migration chain.
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine_for(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def get_engine(settings: Settings):
    return get_engine_for(settings.database_url)


def get_session(settings: Settings) -> Session:
    SessionLocal = sessionmaker(bind=get_engine(settings))
    return SessionLocal()
