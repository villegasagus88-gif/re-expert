"""Multi-proyecto en el Panel: N proyectos por usuario + pagos por proyecto.

- Saca la unicidad de projects.user_id (un usuario puede tener varios proyectos).
- Agrega payments.project_id (FK a projects, nullable) + índice.
- Backfill: hoy hay 1 proyecto por usuario → cada pago se asigna a ese proyecto.

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021_multiproject_panel"
down_revision: str | None = "0020_add_opportunities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) Permitir N proyectos por usuario. Según cómo lo creó SQLAlchemy
    #    (unique=True + index=True), la unicidad puede estar como índice único
    #    `ix_projects_user_id` o como constraint `projects_user_id_key`. Las
    #    sacamos defensivamente y dejamos un índice NO único.
    op.execute("ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_user_id_key")
    op.execute("DROP INDEX IF EXISTS ix_projects_user_id")
    op.create_index("ix_projects_user_id", "projects", ["user_id"], unique=False)

    # 2) Pagos por proyecto: payments.project_id (nullable) + FK + índice.
    op.add_column(
        "payments",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_payments_project_id",
        "payments",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_payments_project_id", "payments", ["project_id"])

    # 3) Backfill: cada pago va al (único) proyecto de su usuario.
    op.execute(
        """
        UPDATE payments p
        SET project_id = (
            SELECT pr.id FROM projects pr
            WHERE pr.user_id = p.user_id
            ORDER BY pr.created_at ASC
            LIMIT 1
        )
        WHERE p.project_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_payments_project_id", table_name="payments")
    op.drop_constraint("fk_payments_project_id", "payments", type_="foreignkey")
    op.drop_column("payments", "project_id")
    # Restaurar unicidad (asume que no quedaron usuarios con > 1 proyecto).
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.create_index("ix_projects_user_id", "projects", ["user_id"], unique=True)
