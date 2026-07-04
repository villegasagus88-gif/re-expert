"""Add plan analysis tables (Análisis de Planos: proyectos, planos, análisis, alertas, tareas)

Revision ID: 0025_add_plan_analysis
Revises: 0024_course_order_id
Create Date: 2026-07-01 00:00:00.000000

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025_add_plan_analysis"
down_revision: str | None = "0024_course_order_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def upgrade() -> None:
    op.create_table(
        "plan_projects",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("obra_type", sa.String(40), nullable=False, server_default="otro"),
        sa.Column("location", sa.String(255), nullable=False, server_default=""),
        sa.Column("estimated_area", sa.String(60), nullable=False, server_default=""),
        sa.Column("stage", sa.String(40), nullable=False, server_default="anteproyecto"),
        sa.Column("analysis_goal", sa.String(60), nullable=False, server_default="entender"),
        sa.Column("client_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_plan_projects_user_id", "plan_projects", ["user_id"])

    op.create_table(
        "plan_files",
        _uuid_pk(),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detected_plan_type", sa.String(60), nullable=False, server_default=""),
        sa.Column("discipline", sa.String(40), nullable=False, server_default=""),
        sa.Column("sheet_number", sa.String(60), nullable=False, server_default=""),
        sa.Column("scale", sa.String(40), nullable=False, server_default=""),
        sa.Column("plan_date", sa.String(40), nullable=False, server_default=""),
        sa.Column("floor_level", sa.String(80), nullable=False, server_default=""),
        sa.Column("classification", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(30), nullable=False, server_default="cargado"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("version_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_current_version", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("previous_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_plan_files_project_id", "plan_files", ["project_id"])
    op.create_index("ix_plan_files_user_id", "plan_files", ["user_id"])
    op.create_index("ix_plan_files_status", "plan_files", ["status"])

    op.create_table(
        "plan_analyses",
        _uuid_pk(),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mode", sa.String(30), nullable=False, server_default="simple"),
        sa.Column("profile", sa.String(30), nullable=False, server_default=""),
        sa.Column("compare_plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("detected_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("general_risk", sa.String(20), nullable=False, server_default="medio"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("plan_score", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("missing_info", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("inconsistencies", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("suggested_questions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("checklist", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_plan_analyses_project_id", "plan_analyses", ["project_id"])
    op.create_index("ix_plan_analyses_plan_id", "plan_analyses", ["plan_id"])
    op.create_index("ix_plan_analyses_user_id", "plan_analyses", ["user_id"])

    op.create_table(
        "plan_alerts",
        _uuid_pk(),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=False, server_default=""),
        sa.Column("category", sa.String(60), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("risk", sa.Text(), nullable=False, server_default=""),
        sa.Column("impact", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommendation", sa.Text(), nullable=False, server_default=""),
        sa.Column("priority", sa.String(20), nullable=False, server_default="media"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suggested_action", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("responsible", sa.String(120), nullable=False, server_default=""),
        sa.Column("due_date", sa.String(20), nullable=False, server_default=""),
        sa.Column("pin_x", sa.Float(), nullable=True),
        sa.Column("pin_y", sa.Float(), nullable=True),
        sa.Column("pin_page", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_plan_alerts_analysis_id", "plan_alerts", ["analysis_id"])
    op.create_index("ix_plan_alerts_plan_id", "plan_alerts", ["plan_id"])
    op.create_index("ix_plan_alerts_project_id", "plan_alerts", ["project_id"])
    op.create_index("ix_plan_alerts_user_id", "plan_alerts", ["user_id"])
    op.create_index("ix_plan_alerts_priority", "plan_alerts", ["priority"])
    op.create_index("ix_plan_alerts_status", "plan_alerts", ["status"])

    op.create_table(
        "plan_tasks",
        _uuid_pk(),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plan_alerts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("priority", sa.String(20), nullable=False, server_default="media"),
        sa.Column("responsible", sa.String(120), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("due_date", sa.String(20), nullable=False, server_default=""),
        sa.Column("comments", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_plan_tasks_project_id", "plan_tasks", ["project_id"])
    op.create_index("ix_plan_tasks_user_id", "plan_tasks", ["user_id"])
    op.create_index("ix_plan_tasks_status", "plan_tasks", ["status"])


def downgrade() -> None:
    op.drop_table("plan_tasks")
    op.drop_table("plan_alerts")
    op.drop_table("plan_analyses")
    op.drop_table("plan_files")
    op.drop_table("plan_projects")
