"""Planos v2: análisis integral de proyecto + objetivos múltiples

- plan_analyses.plan_id y plan_alerts.plan_id pasan a NULLABLE: un análisis
  con plan_id NULL es un ANÁLISIS INTEGRAL del proyecto (todos los planos
  juntos); sus alertas pueden referenciar un plano puntual o ninguno.
- plan_projects.analysis_goals (JSONB) + analysis_goal_custom (TEXT):
  objetivos múltiples seleccionables + objetivo libre escrito por el usuario.
  La columna vieja analysis_goal queda por compatibilidad.

Revision ID: 0027_plan_analysis_v2
Revises: 0026_add_source_audit

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0027_plan_analysis_v2"
down_revision: str | None = "0026_add_source_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("plan_analyses", "plan_id", existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)
    op.alter_column("plan_alerts", "plan_id", existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)
    op.add_column("plan_projects", sa.Column(
        "analysis_goals", postgresql.JSONB(), nullable=False, server_default="[]"))
    op.add_column("plan_projects", sa.Column(
        "analysis_goal_custom", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("plan_projects", "analysis_goal_custom")
    op.drop_column("plan_projects", "analysis_goals")
    op.alter_column("plan_alerts", "plan_id", existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)
    op.alter_column("plan_analyses", "plan_id", existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)
