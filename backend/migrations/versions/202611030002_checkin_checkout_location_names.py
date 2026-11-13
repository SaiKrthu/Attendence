"""Store place names and check-out coordinates with attendance.

Revision ID: 202611030002
Revises: 202611030001
Create Date: 2026-11-03 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202611030002"
down_revision = "202611030001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attendance", sa.Column("check_in_location_name", sa.String(length=1000), nullable=True))
    op.add_column("attendance", sa.Column("check_out_latitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_out_longitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_out_location_name", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("attendance", "check_out_location_name")
    op.drop_column("attendance", "check_out_longitude")
    op.drop_column("attendance", "check_out_latitude")
    op.drop_column("attendance", "check_in_location_name")
