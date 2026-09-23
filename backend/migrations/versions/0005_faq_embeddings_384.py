from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_table(dimensions: int) -> None:
    op.create_table(
        "faq_embeddings",
        sa.Column("faq_id", sa.String(), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("source_link", sa.String(), nullable=False),
        sa.Column("last_update", sa.String(), nullable=False),
        sa.Column("embedding", Vector(dimensions), nullable=False),
    )
    op.execute(
        "CREATE INDEX faq_embeddings_embedding_idx ON faq_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def upgrade() -> None:
    op.drop_table("faq_embeddings")
    _create_table(384)


def downgrade() -> None:
    op.drop_table("faq_embeddings")
    _create_table(256)
