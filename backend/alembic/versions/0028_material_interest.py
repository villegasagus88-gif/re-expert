"""Material interest: qué materiales se buscan y se compran más (lupa inteligente)

Cada vez que un usuario elige un material en el buscador (search) o toca
"Comprar" (buy) se registra un evento. Alimenta el orden "más buscados
primero" del autocompletado de Cotización de Materiales.

Revision ID: 0028_material_interest
Revises: 0027_plan_analysis_v2

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028_material_interest"
down_revision: str | None = "0027_plan_analysis_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "material_interest",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material", sa.String(255), nullable=False),
        sa.Column("action", sa.String(20), nullable=False, server_default="search"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_material_interest_user_id", "material_interest", ["user_id"])
    op.create_index("ix_material_interest_material", "material_interest", ["material"])


def downgrade() -> None:
    op.drop_index("ix_material_interest_material", table_name="material_interest")
    op.drop_index("ix_material_interest_user_id", table_name="material_interest")
    op.drop_table("material_interest")
