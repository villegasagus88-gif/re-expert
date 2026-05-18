"""Add password_resets table for forgot/reset password flow

Store password reset tokens with TTL. Each token is single-use and
expires after RESET_TOKEN_TTL_MINUTES. We never expose the user's
existing password — only allow them to set a new one.

Revision ID: 0014_add_password_resets
Revises: 0013_add_stripe_events
Create Date: 2026-05-06
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_add_password_resets"
down_revision: str | None = "0013_add_stripe_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "password_resets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # SHA-256 hex digest of the random token. Store only the hash so
        # that a leaked DB doesn't allow direct reset (defense-in-depth).
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_password_resets_user_id",
        "password_resets",
        ["user_id"],
    )
    op.create_index(
        "ix_password_resets_expires_at",
        "password_resets",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_password_resets_expires_at", table_name="password_resets")
    op.drop_index("ix_password_resets_user_id", table_name="password_resets")
    op.drop_table("password_resets")
