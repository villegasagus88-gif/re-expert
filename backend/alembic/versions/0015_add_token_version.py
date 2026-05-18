"""Add token_version to profiles for JWT invalidation

Cuando un usuario cambia su contraseña vía forgot-password (o, en el
futuro, cierra sesión globalmente), bumpeamos `token_version` y todos
los JWTs viejos del usuario quedan inválidos. El JWT incluye el `tv`
del momento de creación; `get_current_user` lo compara contra el actual.

Revision ID: 0015_add_token_version
Revises: 0014_add_password_resets
Create Date: 2026-05-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_add_token_version"
down_revision: str | None = "0014_add_password_resets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("profiles", "token_version")
