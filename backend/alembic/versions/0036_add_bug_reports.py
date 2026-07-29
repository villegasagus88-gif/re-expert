"""Add bug_reports: reportes de error que mandan los usuarios

Tabla única para Ayuda → Informar un error:
- `ticket`: número corto y legible (secuencia propia de Postgres) para hablar
  con el usuario sin exponer el UUID.
- `user_id` con ondelete=SET NULL + copia de `reporter_email`: el reporte
  sobrevive si el usuario borra su cuenta, pero se despersonaliza el vínculo.
- CHECK en `status` y `severity`: los estados son un contrato, no una
  convención de comentario (evita que un typo deje un reporte invisible en la
  bandeja del admin).
- Índice compuesto (status, created_at) para la bandeja filtrada por estado.

Revision ID: 0036_add_bug_reports
Revises: 0035_add_corralon_cache
Create Date: 2026-07-26 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0036_add_bug_reports"
down_revision: str | None = "0035_add_corralon_cache"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Secuencia propia para el número de ticket (legible, monotónico, sin reuso).
    op.execute("CREATE SEQUENCE IF NOT EXISTS bug_report_ticket_seq START 1000")

    op.create_table(
        "bug_reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "ticket",
            sa.Integer(),
            server_default=sa.text("nextval('bug_report_ticket_seq')"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reporter_email", sa.String(length=320), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("section", sa.String(length=60), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), server_default="normal", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="new", nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("attachments_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("ticket", name="uq_bug_reports_ticket"),
        sa.CheckConstraint(
            "status IN ('new','in_review','resolved','dismissed')",
            name="ck_bug_reports_status",
        ),
        sa.CheckConstraint(
            "severity IN ('low','normal','high')", name="ck_bug_reports_severity"
        ),
    )
    # La secuencia pertenece a la tabla: un DROP TABLE se la lleva.
    op.execute("ALTER SEQUENCE bug_report_ticket_seq OWNED BY bug_reports.ticket")

    op.create_index("ix_bug_reports_user_id", "bug_reports", ["user_id"])
    op.create_index("ix_bug_reports_status", "bug_reports", ["status"])
    op.create_index("ix_bug_reports_created_at", "bug_reports", ["created_at"])
    op.create_index("ix_bug_reports_status_created", "bug_reports", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_bug_reports_status_created", table_name="bug_reports")
    op.drop_index("ix_bug_reports_created_at", table_name="bug_reports")
    op.drop_index("ix_bug_reports_status", table_name="bug_reports")
    op.drop_index("ix_bug_reports_user_id", table_name="bug_reports")
    op.drop_table("bug_reports")   # OWNED BY se lleva la secuencia
