"""Store employee signup requests for administrator review.

Revision ID: 202610230001
Revises: 202610130001
Create Date: 2026-10-23 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202610230001"
down_revision = "202610130001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_signups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=150), nullable=False),
        sa.Column("designation", sa.String(length=150), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_employee_signups_id"), "employee_signups", ["id"], unique=False)
    op.create_index(op.f("ix_employee_signups_employee_id"), "employee_signups", ["employee_id"], unique=True)
    op.create_index(op.f("ix_employee_signups_email"), "employee_signups", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_employee_signups_email"), table_name="employee_signups")
    op.drop_index(op.f("ix_employee_signups_employee_id"), table_name="employee_signups")
    op.drop_index(op.f("ix_employee_signups_id"), table_name="employee_signups")
    op.drop_table("employee_signups")
