"""add stripe_customer_id to profiles

Revision ID: 0008_add_stripe_customer_id
Revises: 0007_add_project
Create Date: 2026-04-26
"""
import sqlalchemy as sa
from alembic import op

revision: str = "0008_add_stripe_customer_id"
down_revision: str | None = "0007_add_project"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("profiles", "stripe_customer_id")
