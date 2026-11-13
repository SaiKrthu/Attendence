"""Store check-in GPS coordinates on attendance records.

Revision ID: 202611030001
Revises: 202610230001
Create Date: 2026-11-03 11:30:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202611030001"
down_revision = "202610230001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attendance", sa.Column("check_in_latitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_in_longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("attendance", "check_in_longitude")
    op.drop_column("attendance", "check_in_latitude")
