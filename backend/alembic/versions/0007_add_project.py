"""Add projects and project_milestones tables

Revision ID: 0007_add_project
Revises: 0006_add_payments
Create Date: 2026-04-26 10:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_add_project"
down_revision: str | None = "0006_add_payments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
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
            unique=True,
        ),
        sa.Column("nombre", sa.String(255), nullable=False, server_default="Mi Proyecto"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="amarillo"),
        sa.Column("estado_texto", sa.String(255), nullable=False, server_default="Proyecto en curso"),
        sa.Column("presupuesto_base", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("costo_real", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("avance_real_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("avance_plan_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("meses_transcurridos", sa.Integer, nullable=False, server_default="0"),
        sa.Column("meses_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fecha_inicio", sa.Date, nullable=True),
        sa.Column("fecha_entrega_programada", sa.Date, nullable=True),
        sa.Column("fecha_entrega_estimada", sa.Date, nullable=True),
        sa.Column(
            "costos_rubros",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "alertas",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("notas", sa.Text, nullable=True),
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
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    op.create_table(
        "project_milestones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("fecha_objetivo", sa.Date, nullable=False),
        sa.Column("fecha_real", sa.Date, nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("detalle", sa.Text, nullable=True),
        sa.Column("orden", sa.Integer, nullable=False, server_default="0"),
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
    op.create_index("ix_project_milestones_project_id", "project_milestones", ["project_id"])
    op.create_index("ix_project_milestones_user_id", "project_milestones", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_project_milestones_user_id", table_name="project_milestones")
    op.drop_index("ix_project_milestones_project_id", table_name="project_milestones")
    op.drop_table("project_milestones")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")
