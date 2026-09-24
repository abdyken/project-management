from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column in ("degrees", "applicant_types"):
        op.add_column(
            "faq_embeddings",
            sa.Column(column, sa.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
        )


def downgrade() -> None:
    op.drop_column("faq_embeddings", "applicant_types")
    op.drop_column("faq_embeddings", "degrees")
