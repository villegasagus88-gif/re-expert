"""Add corralon_cache table (corralones por zona, cacheados)

La sección Materiales & Corralones busca comercios por zona vía web +
modelo; el resultado se cachea acá (los corralones de una zona no cambian
a diario). cache_key = "c:<zona>:<rubro>" o "m:<zona>:<material>".

Revision ID: 0034_add_corralon_cache
Revises: 0033_add_material_list
Create Date: 2026-07-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0034_add_corralon_cache"
down_revision: str | None = "0033_add_material_list"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "corralon_cache",
        sa.Column("cache_key", sa.Text(), primary_key=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("corralon_cache")
