from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admissions_followup",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("question", sa.Text()),
        sa.Column("program_id", sa.String(64)),
        sa.Column("applicant_type", sa.String(20)),
        sa.Column("similarity_score", sa.Float()),
        sa.Column("session_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('unanswered_question', 'missing_documents')", name="ck_admissions_followup_kind"),
    )


def downgrade() -> None:
    op.drop_table("admissions_followup")
