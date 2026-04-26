"""Add password_hash column to profiles table

Enables standalone bcrypt authentication without Supabase Auth dependency.

Revision ID: 0005_add_password_hash
Revises: 0004_add_conversation_section
Create Date: 2026-04-25 21:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_password_hash"
down_revision: str | None = "0004_add_conversation_section"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("password_hash", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("profiles", "password_hash")
