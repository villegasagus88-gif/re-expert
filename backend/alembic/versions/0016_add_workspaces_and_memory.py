"""Add workspaces, workspace_memory, user_profile_global tables + workspace_id on conversations

Capa 1B — Memoria persistente. Crea:
  - workspaces           (carpetas "Proyectos" tipo ChatGPT, N por usuario)
  - workspace_memory     (key/value scopeado al workspace)
  - user_profile_global  (key/value scopeado al usuario, viaja a todos los chats)

Y agrega `conversations.workspace_id` (nullable) para asignar una conversación
a un workspace. Conversaciones sin workspace son "chats sueltos".

Revision ID: 0016_add_workspaces_and_memory
Revises: 0015_add_token_version
Create Date: 2026-05-28
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_add_workspaces_and_memory"
down_revision: str | None = "0015_add_token_version"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── workspaces ──
    op.create_table(
        "workspaces",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_workspaces_user_id", "workspaces", ["user_id"])

    # ── workspace_memory ──
    op.create_table(
        "workspace_memory",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("value", sa.String(1000), nullable=False),
        sa.Column(
            "source", sa.String(20), nullable=False, server_default="manual"
        ),
        sa.Column(
            "confidence", sa.String(10), nullable=False, server_default="high"
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint(
            "workspace_id", "key", name="uq_workspace_memory_workspace_key"
        ),
    )
    op.create_index(
        "ix_workspace_memory_workspace_id", "workspace_memory", ["workspace_id"]
    )

    # ── user_profile_global ──
    op.create_table(
        "user_profile_global",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("value", sa.String(1000), nullable=False),
        sa.Column(
            "source", sa.String(20), nullable=False, server_default="manual"
        ),
        sa.Column(
            "confidence", sa.String(10), nullable=False, server_default="high"
        ),
        sa.Column(
            "sort_order", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint(
            "user_id", "key", name="uq_user_profile_global_user_key"
        ),
    )
    op.create_index(
        "ix_user_profile_global_user_id", "user_profile_global", ["user_id"]
    )

    # ── conversations.workspace_id ──
    op.add_column(
        "conversations",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_conversations_workspace_id", "conversations", ["workspace_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_workspace_id", table_name="conversations")
    op.drop_column("conversations", "workspace_id")

    op.drop_index(
        "ix_user_profile_global_user_id", table_name="user_profile_global"
    )
    op.drop_table("user_profile_global")

    op.drop_index(
        "ix_workspace_memory_workspace_id", table_name="workspace_memory"
    )
    op.drop_table("workspace_memory")

    op.drop_index("ix_workspaces_user_id", table_name="workspaces")
    op.drop_table("workspaces")
