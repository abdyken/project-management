"""Source-backed guidance and private admissions requests; additive for rollback."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "program_guidance",
        sa.Column(
            "program_id",
            sa.String(64),
            sa.ForeignKey("program.program_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_by_id",
            sa.Integer(),
            sa.ForeignKey("staff_user.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "admissions_request",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "applicant_id",
            sa.Integer(),
            sa.ForeignKey("applicant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("client_key", sa.String(64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("answer", sa.Text()),
        sa.Column(
            "answered_by_id",
            sa.Integer(),
            sa.ForeignKey("staff_user.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("answered_at", sa.DateTime(timezone=True)),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("applicant_id", "client_key", name="uq_request_client_key"),
        sa.CheckConstraint("language IN ('en','ru','kk')", name="ck_request_language"),
    )
    op.create_index("ix_request_applicant", "admissions_request", ["applicant_id"])
    op.create_index("ix_request_created", "admissions_request", ["created_at"])


def downgrade():
    op.drop_table("admissions_request")
    op.drop_table("program_guidance")
