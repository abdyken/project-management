"""create faq_embeddings table (T3.2, pgvector)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-18

Owned by Serdar (AI/IS developer). Part of the shared Alembic chain:
0001 (T0.3 baseline) -> 0002 (this).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Must match app/assistant/models.py::EMBEDDING_DIMENSIONS (256, the mock
# provider's size). If the real embedding provider has a different output
# size, add a follow-up migration to alter the column before switching.
EMBEDDING_DIMENSIONS = 256


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "faq_embeddings",
        sa.Column("faq_id", sa.String(), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("source_link", sa.String(), nullable=False),
        sa.Column("last_update", sa.String(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
    )
    op.execute(
        "CREATE INDEX faq_embeddings_embedding_idx ON faq_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("faq_embeddings_embedding_idx", table_name="faq_embeddings")
    op.drop_table("faq_embeddings")
