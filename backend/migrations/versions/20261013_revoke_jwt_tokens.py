"""Persist JWT logout revocations.

Revision ID: 202610130001
Revises: 202610120001
Create Date: 2026-10-13 14:30:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202610130001"
down_revision = "202610120001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_id", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_revoked_tokens_expires_at"), "revoked_tokens", ["expires_at"], unique=False)
    op.create_index(op.f("ix_revoked_tokens_token_id"), "revoked_tokens", ["token_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_revoked_tokens_token_id"), table_name="revoked_tokens")
    op.drop_index(op.f("ix_revoked_tokens_expires_at"), table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
