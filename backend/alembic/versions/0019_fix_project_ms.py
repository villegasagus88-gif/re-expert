"""Fix: crear project_milestones si falta en la DB

Contexto: en producción la tabla `projects` existe pero `project_milestones`
NO (relation "project_milestones" does not exist), aunque la migración 0007
crea ambas. Quedó un estado inconsistente (la segunda create_table de 0007 no
persistió, pero 0007 está marcada como aplicada), así que `alembic upgrade head`
no la vuelve a crear. Esto rompía TODO el Panel de Proyecto: el dashboard hace
`selectinload(Project.milestones)` y el endpoint /milestones consulta la tabla
→ 500 (UndefinedTableError).

Esta migración crea `project_milestones` SOLO si no existe (idempotente), con el
mismo esquema que 0007. Segura de correr en cualquier entorno: si la tabla ya
está, no hace nada.

Revision ID: 0019_fix_project_ms
Revises: 0018_add_credits_pipeline
Create Date: 2026-06-24 00:00:00.000000

NOTA: el ID de revisión debe ser <= 32 chars — la columna alembic_version.version_num
es VARCHAR(32). Un ID más largo hace fallar el UPDATE de stamping (y con él TODO el
deploy, porque alembic upgrade head corre como preDeployCommand). Por eso es corto.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_fix_project_ms"
down_revision: str | None = "0018_add_credits_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "project_milestones" not in existing_tables:
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
        op.create_index(
            "ix_project_milestones_project_id", "project_milestones", ["project_id"]
        )
        op.create_index(
            "ix_project_milestones_user_id", "project_milestones", ["user_id"]
        )


def downgrade() -> None:
    # No-op: 0007 ya tiene el downgrade de esta tabla. Esta migración solo
    # repara un estado inconsistente; no la borramos en downgrade para no
    # romper entornos donde sí existía.
    pass
