"""Baseline: empty schema, proves the migration pipeline works (T0.3).

The program table follows in the next migration (T1.1).

Revision ID: 0001
Revises:
Create Date: 2026-09-18
"""
from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
