"""Add trial_ends_at + paid-only plan model (no free tier)

Modelo pago-only: el plan 'free' deja de existir. Estados: trial / pro / inactive.
  - Agrega profiles.trial_ends_at (timestamptz, nullable).
  - Cambia el server_default de profiles.plan de 'free' a 'trial'.
  - Backfill: usuarios 'free' existentes (pre-launch) pasan a 'trial' con 7 días
    desde el deploy. Los 'pro' quedan intactos (trial_ends_at NULL).

Revision ID: 0017_add_trial_and_paid_model
Revises: 0016_add_workspaces_and_memory
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_add_trial_and_paid_model"
down_revision: str | None = "0016_add_workspaces_and_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("profiles", "plan", server_default="trial")
    # Pre-launch: los 'free' existentes pasan a trial con 7 días desde el deploy.
    op.execute(
        "UPDATE profiles SET plan = 'trial', "
        "trial_ends_at = now() + interval '7 days' "
        "WHERE plan = 'free'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE profiles SET plan = 'free' WHERE plan IN ('trial', 'inactive')"
    )
    op.alter_column("profiles", "plan", server_default="free")
    op.drop_column("profiles", "trial_ends_at")
