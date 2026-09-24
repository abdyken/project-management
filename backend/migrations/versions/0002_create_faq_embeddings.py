from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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
