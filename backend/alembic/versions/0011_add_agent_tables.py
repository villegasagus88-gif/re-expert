"""Add agent tables: reminders, user_channels

Tablas que dan soporte al modo agente de SOL:
- `reminders` para recordatorios programados que el scheduler dispara.
- `user_channels` para los canales conectados (Telegram, WhatsApp, push, email).

Revision ID: 0011_add_agent_tables
Revises: 0010_add_ingest_tables
Create Date: 2026-05-10 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_add_agent_tables"
down_revision: str | None = "0010_add_ingest_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ─── reminders ────────────────────────────────────────────────────────
    op.create_table(
        "reminders",
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
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False, server_default="in_app"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"])
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"])
    op.create_index("ix_reminders_status", "reminders", ["status"])
    op.create_index("ix_reminders_due_status", "reminders", ["due_at", "status"])

    # ─── user_channels ────────────────────────────────────────────────────
    op.create_table(
        "user_channels",
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
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("pairing_token", sa.String(64), nullable=True),
        sa.Column("pairing_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "channel", "address", name="uq_user_channel_addr"),
    )
    op.create_index("ix_user_channels_user_id", "user_channels", ["user_id"])
    op.create_index("ix_user_channels_pairing_token", "user_channels", ["pairing_token"])


def downgrade() -> None:
    op.drop_index("ix_user_channels_pairing_token", table_name="user_channels")
    op.drop_index("ix_user_channels_user_id", table_name="user_channels")
    op.drop_table("user_channels")

    op.drop_index("ix_reminders_due_status", table_name="reminders")
    op.drop_index("ix_reminders_status", table_name="reminders")
    op.drop_index("ix_reminders_due_at", table_name="reminders")
    op.drop_index("ix_reminders_user_id", table_name="reminders")
    op.drop_table("reminders")
