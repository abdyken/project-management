"""create program table (T1.1, US1 catalogue)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program",
        sa.Column("program_id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("faculty", sa.String(255), nullable=False),
        sa.Column("degree_level", sa.String(20), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("tuition_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "degree_level IN ('bachelor', 'master', 'phd')",
            name="ck_program_degree_level",
        ),
        sa.CheckConstraint("tuition_fee >= 0", name="ck_program_tuition_fee_non_negative"),
    )


def downgrade() -> None:
    op.drop_table("program")
