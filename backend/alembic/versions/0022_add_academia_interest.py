"""Add academia_interest table (medición de demanda de cursos)

Revision ID: 0022_add_academia_interest
Revises: 0021_multiproject_panel
Create Date: 2026-06-30 00:00:00.000000

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
Se encadena después de 0021_multiproject_panel (rama de Agustín) para que
`alembic upgrade head` tenga un único head (evita el error de multiple heads).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022_add_academia_interest"
down_revision: str | None = "0021_multiproject_panel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "academia_interest",
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
        sa.Column("course_id", sa.String(80), nullable=False),
        sa.Column("course_title", sa.String(255), nullable=False, server_default=""),
        sa.Column("topic", sa.String(40), nullable=False, server_default=""),
        sa.Column("action", sa.String(20), nullable=False, server_default="view"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_academia_interest_user_id", "academia_interest", ["user_id"])
    op.create_index("ix_academia_interest_course_id", "academia_interest", ["course_id"])
    op.create_index("ix_academia_interest_topic", "academia_interest", ["topic"])


def downgrade() -> None:
    op.drop_index("ix_academia_interest_topic", table_name="academia_interest")
    op.drop_index("ix_academia_interest_course_id", table_name="academia_interest")
    op.drop_index("ix_academia_interest_user_id", table_name="academia_interest")
    op.drop_table("academia_interest")
