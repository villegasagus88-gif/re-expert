"""Add mp_events table for Mercado Pago webhook idempotency + audit

Append-only log de webhooks de MP. request_id (x-request-id, único por entrega)
con UNIQUE → deduplica entregas exactas repetidas sin descartar reintentos
legítimos (esos re-consultan el estado vivo en MP).

Revision ID: 0032_add_mp_events
Revises: 0031_perf_indexes
Create Date: 2026-07-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0032_add_mp_events"
down_revision: str | None = "0031_perf_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mp_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("data_id", sa.String(255), nullable=True),
        sa.Column("notif_type", sa.String(100), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("request_id", name="uq_mp_events_request_id"),
    )
    op.create_index("ix_mp_events_request_id", "mp_events", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_mp_events_request_id", table_name="mp_events")
    op.drop_table("mp_events")
