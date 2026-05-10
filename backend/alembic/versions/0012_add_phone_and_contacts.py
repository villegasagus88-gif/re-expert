"""Add phone column to profiles + contacts table

SOL agente necesita saber el teléfono del usuario y la libreta de contactos
(amigos / proveedores / clientes) para enviar PDFs/recordatorios vía
WhatsApp/Telegram deep links.

Revision ID: 0012_add_phone_and_contacts
Revises: 0011_add_agent_tables
Create Date: 2026-05-10 02:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_add_phone_and_contacts"
down_revision: str | None = "0011_add_agent_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ─── profiles.phone ───────────────────────────────────────────────────
    op.add_column(
        "profiles",
        sa.Column("phone", sa.String(32), nullable=True),
    )
    # ─── profiles.automation_prefs ────────────────────────────────────────
    # JSON con preferencias de automatización del usuario (ej. {"daily_summary": true,
    # "alert_overruns": true, "preferred_channel": "telegram"}). Lo va llenando SOL
    # a medida que va aprendiendo qué cosas avisarle.
    op.add_column(
        "profiles",
        sa.Column("automation_prefs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # ─── contacts ─────────────────────────────────────────────────────────
    op.create_table(
        "contacts",
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
        sa.Column("name", sa.String(200), nullable=False),
        # Teléfono en formato internacional (ej. +5491155555555). Lo normaliza
        # el backend antes de guardar.
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        # chat_id de Telegram si el contacto tiene cuenta — opcional
        sa.Column("telegram_chat_id", sa.String(64), nullable=True),
        sa.Column("role", sa.String(80), nullable=True),  # ej. "Proveedor", "Cliente", "Arquitecto"
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index("ix_contacts_user_id", "contacts", ["user_id"])
    # Búsqueda por nombre (normalizado lowercase) — usaremos ILIKE en la app
    op.create_index("ix_contacts_user_name", "contacts", ["user_id", "name"])


def downgrade() -> None:
    op.drop_index("ix_contacts_user_name", table_name="contacts")
    op.drop_index("ix_contacts_user_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_column("profiles", "automation_prefs")
    op.drop_column("profiles", "phone")
