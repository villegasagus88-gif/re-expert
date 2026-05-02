"""Add stripe_events table for webhook idempotency

Append-only log of received Stripe events. Used to detect retries and
skip already-processed events (Stripe redelivers up to 3 days).

Revision ID: 0011_add_stripe_events
Revises: 0010_add_ingest_tables
Create Date: 2026-04-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_add_stripe_events"
down_revision: str | None = "0010_add_ingest_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stripe_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("event_id", name="uq_stripe_events_event_id"),
    )
    op.create_index("ix_stripe_events_event_id", "stripe_events", ["event_id"])
    op.create_index("ix_stripe_events_event_type", "stripe_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_stripe_events_event_type", table_name="stripe_events")
    op.drop_index("ix_stripe_events_event_id", table_name="stripe_events")
    op.drop_table("stripe_events")
