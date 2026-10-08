"""FAQ index rows per language (US8): Kazakh and Russian texts are searched too.

Revision ID: 0013
Revises: 0012
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("faq_embeddings", sa.Column("language", sa.String(length=2), nullable=False, server_default="en"))
    op.add_column(
        "faq_embeddings",
        sa.Column("translations", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.drop_constraint("faq_embeddings_pkey", "faq_embeddings", type_="primary")
    op.create_primary_key("faq_embeddings_pkey", "faq_embeddings", ["faq_id", "language"])


def downgrade() -> None:
    op.execute("DELETE FROM faq_embeddings WHERE language <> 'en'")
    op.drop_constraint("faq_embeddings_pkey", "faq_embeddings", type_="primary")
    op.create_primary_key("faq_embeddings_pkey", "faq_embeddings", ["faq_id"])
    op.drop_column("faq_embeddings", "translations")
    op.drop_column("faq_embeddings", "language")
