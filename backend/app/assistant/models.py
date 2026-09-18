"""SQLAlchemy model for the FAQ retrieval index (T3.2), stored in the same
Postgres DB as the rest of the backend, per the T0.1 stack decision
(PostgreSQL 16 + pgvector, embeddings colocated — no separate vector DB).
"""
from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import Settings
from app.db import Base

# pgvector columns need a fixed width at table-creation time. Must match
# Settings.embedding_dimensions (default 256, the mock provider's size) —
# see the note in app/config.py if this needs to change for a real provider.
EMBEDDING_DIMENSIONS = 256


class FaqEmbeddingRecord(Base):
    __tablename__ = "faq_embeddings"

    faq_id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    source_link: Mapped[str] = mapped_column(String, nullable=False)
    last_update: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)


def assert_dimensions_match(settings: Settings) -> None:
    if settings.embedding_dimensions != EMBEDDING_DIMENSIONS:
        raise ValueError(
            "EMBEDDING_DIMENSIONS setting "
            f"({settings.embedding_dimensions}) does not match the faq_embeddings "
            f"column width ({EMBEDDING_DIMENSIONS}). Update EMBEDDING_DIMENSIONS in "
            "app/assistant/models.py and add a new Alembic migration before reindexing."
        )
