"""Sprint 7: online applications and uploaded documents; additive for rollback.

Both tables are new, so creating their indexes inline locks nothing in use. The
downgrade drops them; files on the uploads volume are not touched by migrations.
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

STATUSES = "('draft', 'submitted', 'in_review', 'needs_changes', 'accepted', 'rejected')"
EDUCATION = "('school', 'college', 'bachelor', 'master')"


def upgrade():
    op.create_table(
        "application",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.String(64), sa.ForeignKey("program.program_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("applicant_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("language", sa.String(2), nullable=False, server_default="en"),
        sa.Column("full_name", sa.String(200)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("citizenship", sa.String(100)),
        sa.Column("phone", sa.String(30)),
        sa.Column("education_level", sa.String(20)),
        sa.Column("graduation_year", sa.Integer()),
        sa.Column("exam_total", sa.Integer()),
        sa.Column("consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("staff_note", sa.Text()),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("staff_user.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("status_changed_at", sa.DateTime(timezone=True)),
        sa.Column("notified_status", sa.String(20)),
        sa.CheckConstraint(f"status IN {STATUSES}", name="ck_application_status"),
        sa.CheckConstraint("applicant_type IN ('local', 'international')", name="ck_application_applicant_type"),
        sa.CheckConstraint("language IN ('en', 'ru', 'kk')", name="ck_application_language"),
        sa.CheckConstraint(
            f"education_level IS NULL OR education_level IN {EDUCATION}", name="ck_application_education"
        ),
    )
    op.create_index("ix_application_applicant_id", "application", ["applicant_id"])
    op.create_index("ix_application_program_id", "application", ["program_id"])
    op.create_index("ix_application_queue", "application", ["status", "submitted_at"])
    op.create_index("ix_application_reviewed_by_id", "application", ["reviewed_by_id"])
    op.create_index(
        "uq_application_live",
        "application",
        ["applicant_id", "program_id", "applicant_type"],
        unique=True,
        postgresql_where=sa.text("status <> 'rejected'"),
    )
    op.create_table(
        "application_document",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "application_id", sa.Integer(), sa.ForeignKey("application.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("program_document_requirement.id", ondelete="SET NULL"),
        ),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(64), nullable=False, unique=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_application_document_application_id", "application_document", ["application_id"])
    op.create_index("ix_application_document_requirement_id", "application_document", ["requirement_id"])


def downgrade():
    op.drop_table("application_document")
    op.drop_table("application")
