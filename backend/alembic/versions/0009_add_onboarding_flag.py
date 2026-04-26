"""add onboarding_completed flag to profiles"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_add_onboarding"
down_revision: str | None = "0008_add_stripe_customer_id"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("profiles", "onboarding_completed")
