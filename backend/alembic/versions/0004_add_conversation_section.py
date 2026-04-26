"""Add section column to conversations table

Categorizes conversations by topic area (compra, venta, alquiler,
tasacion, general, etc.) to support multi-section chat routing.

Revision ID: 0004_add_conversation_section
Revises: 0003_add_token_usage
Create Date: 2026-04-25 20:30:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_conversation_section"
down_revision: str | None = "0003_add_token_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("section", sa.String(50), nullable=False, server_default="general"),
    )
    op.create_index("ix_conversations_section", "conversations", ["section"])


def downgrade() -> None:
    op.drop_index("ix_conversations_section", table_name="conversations")
    op.drop_column("conversations", "section")
