"""Material price overrides: precios vivos actualizados con IA

El CSV curado queda como base; las actualizaciones automáticas (Tavily +
Claude, disparadas al entrar un usuario si la data está vieja) se guardan
acá y se mergean sobre el CSV en GET /api/materials.

Revision ID: 0029_material_price_live
Revises: 0028_material_interest

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0029_material_price_live"
down_revision: str | None = "0028_material_interest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "material_price_override",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("material", sa.String(255), nullable=False, unique=True),
        sa.Column("precio_ars", sa.Integer(), nullable=False),
        sa.Column("variacion_mensual_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fuente", sa.String(255), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("material_price_override")
