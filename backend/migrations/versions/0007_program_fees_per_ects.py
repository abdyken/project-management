from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_program_tuition_fee_non_negative", "program", type_="check")
    op.drop_column("program", "tuition_fee")
    op.drop_column("program", "application_deadline")
    op.add_column("program", sa.Column("tuition_per_ects_kzt", sa.Integer()))
    op.add_column("program", sa.Column("tuition_per_ects_usd", sa.Integer()))
    op.add_column("program", sa.Column("deadline_local", sa.Date()))
    op.add_column("program", sa.Column("deadline_international", sa.Date()))
    op.add_column("program", sa.Column("source_url", sa.String(500)))
    op.create_check_constraint("ck_program_tuition_kzt_non_negative", "program", "tuition_per_ects_kzt >= 0")
    op.create_check_constraint("ck_program_tuition_usd_non_negative", "program", "tuition_per_ects_usd >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_program_tuition_usd_non_negative", "program", type_="check")
    op.drop_constraint("ck_program_tuition_kzt_non_negative", "program", type_="check")
    for column in ("source_url", "deadline_international", "deadline_local", "tuition_per_ects_usd", "tuition_per_ects_kzt"):
        op.drop_column("program", column)
    op.add_column("program", sa.Column("application_deadline", sa.Date()))
    op.add_column("program", sa.Column("tuition_fee", sa.Numeric(12, 2)))
    op.create_check_constraint("ck_program_tuition_fee_non_negative", "program", "tuition_fee >= 0")
