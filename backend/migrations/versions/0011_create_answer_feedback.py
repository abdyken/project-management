"""Create answer feedback for US13.

Revision ID: 0011
Revises: 0010
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "answer_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("answer_id", sa.Integer(), sa.ForeignKey("chat_turn.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.String(4), nullable=False),
        sa.Column("reason", sa.String(20)),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("answer_id", name="uq_answer_feedback_answer_id"),
        sa.CheckConstraint("rating IN ('up', 'down')", name="ck_answer_feedback_rating"),
        sa.CheckConstraint("rating = 'down' OR reason IS NULL", name="ck_answer_feedback_reason"),
    )


def downgrade() -> None:
    op.drop_table("answer_feedback")
