"""Who last edited a program in the staff area (US21).

Nullable columns only, so the previous API version keeps working after a rollback.

Revision ID: 0017
Revises: 0016
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "program", sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("staff_user.id", ondelete="SET NULL"))
    )
    op.add_column("program", sa.Column("updated_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("program", "updated_at")
    op.drop_column("program", "updated_by_id")
