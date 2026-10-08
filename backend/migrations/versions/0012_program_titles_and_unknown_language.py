"""Program titles in Kazakh and Russian, language may be unpublished (US15, US16).

Revision ID: 0012
Revises: 0011
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("program", sa.Column("title_ru", sa.String(length=255), nullable=True))
    op.add_column("program", sa.Column("title_kk", sa.String(length=255), nullable=True))
    op.alter_column("program", "language", existing_type=sa.String(length=50), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE program SET language = 'not published' WHERE language IS NULL")
    op.alter_column("program", "language", existing_type=sa.String(length=50), nullable=False)
    op.drop_column("program", "title_kk")
    op.drop_column("program", "title_ru")
