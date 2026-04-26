"""Add ingest tables: payments, milestones, materials, budgets

Tablas alimentadas por el endpoint POST /api/data/ingest (datos
estructurados extraidos por SOL u otros flujos de carga manual).

Revision ID: 0004_add_ingest_tables
Revises: 0003_add_token_usage
Create Date: 2026-04-25 12:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_add_ingest_tables"
down_revision: str | None = "0003_add_token_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # payments
    op.create_table(
        "payments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="ARS"),
        sa.Column("provider", sa.String(200), nullable=True),
        sa.Column("concept", sa.String(500), nullable=True),
        sa.Column("paid_at", sa.Date, nullable=True),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="sol"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_created_at", "payments", ["created_at"])

    # milestones
    op.create_table(
        "milestones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("completed_at", sa.Date, nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="sol"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_milestones_user_id", "milestones", ["user_id"])
    op.create_index("ix_milestones_created_at", "milestones", ["created_at"])

    # materials
    op.create_table(
        "materials",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="ARS"),
        sa.Column("supplier", sa.String(200), nullable=True),
        sa.Column("quoted_at", sa.Date, nullable=True),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="sol"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_materials_user_id", "materials", ["user_id"])
    op.create_index("ix_materials_created_at", "materials", ["created_at"])

    # budgets
    op.create_table(
        "budgets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="ARS"),
        sa.Column("kind", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="sol"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_created_at", "budgets", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_budgets_created_at", table_name="budgets")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_table("budgets")

    op.drop_index("ix_materials_created_at", table_name="materials")
    op.drop_index("ix_materials_user_id", table_name="materials")
    op.drop_table("materials")

    op.drop_index("ix_milestones_created_at", table_name="milestones")
    op.drop_index("ix_milestones_user_id", table_name="milestones")
    op.drop_table("milestones")

    op.drop_index("ix_payments_created_at", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")
