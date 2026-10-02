from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.assistant.embeddings import DIMENSIONS
from app.db import Base


class FaqEmbeddingRecord(Base):
    # No approximate (HNSW) index: exact search is always correct and instant for
    # a FAQ base of this size - see migration 0010.
    __tablename__ = "faq_embeddings"

    faq_id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    source_link: Mapped[str] = mapped_column(String, nullable=False)
    last_update: Mapped[str] = mapped_column(String, nullable=False)
    degrees: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    applicant_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSIONS), nullable=False)
