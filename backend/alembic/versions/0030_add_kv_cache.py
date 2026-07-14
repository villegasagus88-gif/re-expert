"""kv_cache: cache persistente con TTL (sobrevive redeploys)

Backing store de caches que hoy viven en RAM y mueren en cada deploy de Railway
(resúmenes/traducciones de noticias). key = identificador del cache (ej.
'digest::<url>'), value = payload JSON, expires_at = vencimiento.

Revision ID: 0030_add_kv_cache
Revises: 0029_material_price_live

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0030_add_kv_cache"
down_revision: str | None = "0029_material_price_live"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "kv_cache",
        sa.Column("key", sa.String(512), primary_key=True),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_kv_cache_expires_at", "kv_cache", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_kv_cache_expires_at", table_name="kv_cache")
    op.drop_table("kv_cache")
