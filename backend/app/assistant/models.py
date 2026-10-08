from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.assistant.embeddings import DIMENSIONS
from app.db import Base


class FaqEmbeddingRecord(Base):
    __tablename__ = "faq_embeddings"

    faq_id: Mapped[str] = mapped_column(String, primary_key=True)
    language: Mapped[str] = mapped_column(String(2), primary_key=True, server_default="en")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    source_link: Mapped[str] = mapped_column(String, nullable=False)
    last_update: Mapped[str] = mapped_column(String, nullable=False)
    degrees: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    applicant_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    translations: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSIONS), nullable=False)
