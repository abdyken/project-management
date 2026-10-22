"""Sprint 5 applicant accounts, saved checklists, progress and reminder ledger.

Revision ID: 0018
Revises: 0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applicant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("language", sa.String(2), nullable=False, server_default="en"),
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_hash", sa.String(64), unique=True),
        sa.Column("verification_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "applicant_session",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_applicant_session_applicant_id", "applicant_session", ["applicant_id"])
    op.create_table(
        "saved_program",
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicant.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "program_id", sa.String(64), sa.ForeignKey("program.program_id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("applicant_type", sa.String(20), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("applicant_type IN ('local', 'international')", name="ck_saved_applicant_type"),
    )
    op.create_table(
        "document_progress",
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicant.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("program_document_requirement.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "deadline_reminder",
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicant.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "program_id", sa.String(64), sa.ForeignKey("program.program_id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("applicant_type", sa.String(20), primary_key=True),
        sa.Column("deadline", sa.Date(), primary_key=True),
        sa.Column("milestone", sa.Integer(), primary_key=True),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    for table in ("deadline_reminder", "document_progress", "saved_program", "applicant_session", "applicant"):
        op.drop_table(table)
