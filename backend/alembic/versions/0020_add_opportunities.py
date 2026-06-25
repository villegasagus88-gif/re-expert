"""Add opportunities table (Opportunity Scanner)

Revision ID: 0020_add_opportunities
Revises: 0019_fix_project_ms
Create Date: 2026-06-25 00:00:00.000000

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_add_opportunities"
down_revision: str | None = "0019_fix_project_ms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
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
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("titulo", sa.String(255), nullable=False, server_default="Oportunidad"),
        sa.Column("zona", sa.String(160), nullable=True),
        sa.Column("ciudad", sa.String(120), nullable=True),
        sa.Column("tipo_inmueble", sa.String(40), nullable=False, server_default="terreno"),
        sa.Column("objetivo", sa.String(40), nullable=True),
        sa.Column("superficie_terreno_m2", sa.Float, nullable=True),
        sa.Column("m2_vendibles", sa.Float, nullable=True),
        sa.Column("precio_pedido", sa.Numeric(14, 2), nullable=True),
        sa.Column("costo_obra_m2", sa.Numeric(12, 2), nullable=True),
        sa.Column("precio_venta_m2", sa.Numeric(12, 2), nullable=True),
        sa.Column("moneda", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("recomendacion", sa.String(24), nullable=True),
        sa.Column("estado_pipeline", sa.String(24), nullable=False, server_default="nueva"),
        sa.Column(
            "inputs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "analysis",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_opportunities_user_id", "opportunities", ["user_id"])
    op.create_index("ix_opportunities_project_id", "opportunities", ["project_id"])
    op.create_index(
        "ix_opportunities_user_estado", "opportunities", ["user_id", "estado_pipeline"]
    )


def downgrade() -> None:
    op.drop_index("ix_opportunities_user_estado", table_name="opportunities")
    op.drop_index("ix_opportunities_project_id", table_name="opportunities")
    op.drop_index("ix_opportunities_user_id", table_name="opportunities")
    op.drop_table("opportunities")
