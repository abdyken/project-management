from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program_document_requirement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("program_id", sa.String(64), nullable=False),
        sa.Column("applicant_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("document_format", sa.String(20), nullable=False),
        sa.Column("translation_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notarisation_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deadline", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("applicant_type IN ('local', 'international')", name="ck_requirement_applicant_type"),
        sa.CheckConstraint("document_format IN ('original', 'copy')", name="ck_requirement_document_format"),
        sa.ForeignKeyConstraint(["program_id"], ["program.program_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_program_document_requirement_program_id", "program_document_requirement", ["program_id"])
    op.create_index(
        "ix_program_document_requirement_applicant_type", "program_document_requirement", ["applicant_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_program_document_requirement_applicant_type", table_name="program_document_requirement")
    op.drop_index("ix_program_document_requirement_program_id", table_name="program_document_requirement")
    op.drop_table("program_document_requirement")
