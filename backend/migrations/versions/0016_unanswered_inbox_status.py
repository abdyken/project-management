"""Inbox status of unanswered questions (US22): new, answered with an FAQ item, or dismissed.

Every existing row becomes `new`. The columns are nullable or have a default, so the
previous API version keeps working if a deployment is rolled back.

Revision ID: 0016
Revises: 0015
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("admissions_followup", sa.Column("status", sa.String(length=10), nullable=False, server_default="new"))
    op.add_column("admissions_followup", sa.Column("faq_id", sa.String(length=32)))
    op.add_column(
        "admissions_followup",
        sa.Column("handled_by_id", sa.Integer(), sa.ForeignKey("staff_user.id", ondelete="SET NULL")),
    )
    op.add_column("admissions_followup", sa.Column("handled_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "ck_admissions_followup_status", "admissions_followup", "status IN ('new', 'answered', 'dismissed')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_admissions_followup_status", "admissions_followup", type_="check")
    for column in ("handled_at", "handled_by_id", "faq_id", "status"):
        op.drop_column("admissions_followup", column)
