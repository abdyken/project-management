"""drop the approximate HNSW index on faq_embeddings: exact search

The FAQ base is rebuilt (all rows deleted and re-inserted) on every API start
and in every assistant test. Deleted rows stay in an HNSW graph until vacuum,
and the approximate search then sometimes misses the right item: a FAQ
question asked word for word was answered with the "could not find" fallback
(3 of 8 test runs failed with the index, 0 of 8 without).

With a FAQ base of tens to a few thousand items an exact scan is well under a
millisecond and always returns the true nearest items. Recreate an ANN index
only if the base grows to hundreds of thousands of rows.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-01
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("faq_embeddings_embedding_idx", table_name="faq_embeddings")


def downgrade() -> None:
    op.execute(
        "CREATE INDEX faq_embeddings_embedding_idx ON faq_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )
