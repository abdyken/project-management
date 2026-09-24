from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.assistant.embeddings import DIMENSIONS
from app.db import Base


class FaqEmbeddingRecord(Base):
    __tablename__ = "faq_embeddings"
    __table_args__ = (
        Index(
            "faq_embeddings_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    faq_id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    source_link: Mapped[str] = mapped_column(String, nullable=False)
    last_update: Mapped[str] = mapped_column(String, nullable=False)
    degrees: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    applicant_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    embedding: Mapped[list[float]] = mapped_column(Vector(DIMENSIONS), nullable=False)
