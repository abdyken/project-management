"""FAQ items in the database (US20), loaded once from app/data/faq.json.

From this revision on the table, not the file, is the source of truth: the API start
indexes the published rows, and the admissions office edits them in the staff area.

Revision ID: 0015
Revises: 0014
"""
import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FAQ_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "faq.json"
TEXT_FIELDS = (
    "faq_id", "category", "question", "answer", "source_link", "evidence",
    "question_ru", "answer_ru", "source_link_ru", "evidence_ru",
    "question_kk", "answer_kk", "source_link_kk", "evidence_kk", "last_update",
)


def upgrade() -> None:
    faq_item = op.create_table(
        "faq_item",
        sa.Column("faq_id", sa.String(length=32), primary_key=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="published"),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("source_link", sa.String(length=500), nullable=False),
        sa.Column("evidence", sa.Text()),
        sa.Column("question_ru", sa.Text()),
        sa.Column("answer_ru", sa.Text()),
        sa.Column("source_link_ru", sa.String(length=500)),
        sa.Column("evidence_ru", sa.Text()),
        sa.Column("question_kk", sa.Text()),
        sa.Column("answer_kk", sa.Text()),
        sa.Column("source_link_kk", sa.String(length=500)),
        sa.Column("evidence_kk", sa.Text()),
        sa.Column("degrees", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("applicant_types", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_update", sa.String(length=10), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("staff_user.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'published', 'retired')", name="ck_faq_item_status"),
    )
    items = json.loads(FAQ_FILE.read_text(encoding="utf-8"))
    op.bulk_insert(
        faq_item,
        [
            {
                **{field: item.get(field) for field in TEXT_FIELDS},
                "status": "published",
                "degrees": item.get("degrees", []),
                "applicant_types": item.get("applicant_types", []),
            }
            for item in items
        ],
    )


def downgrade() -> None:
    op.drop_table("faq_item")
