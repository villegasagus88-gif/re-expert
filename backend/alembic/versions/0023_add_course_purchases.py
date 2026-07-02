"""course_purchases: compras de cursos de Academia (pago único MP).

Entitlements de cursos en nuestra DB (MP solo cobra). Un índice único PARCIAL
sobre (user_id, course_id) en estados con acceso (approved/free) evita comprar
dos veces el mismo curso, sin bloquear reintentos pending/rejected.

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023_course_purchases"
down_revision: str | None = "0022_add_academia_interest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(80), nullable=False),
        sa.Column("course_title", sa.String(255), nullable=False),
        sa.Column("price_ars", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("mp_preference_id", sa.String(64), nullable=True),
        sa.Column("mp_payment_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_course_purchases_user_id", "course_purchases", ["user_id"])
    op.create_index("ix_course_purchases_user_course", "course_purchases",
                    ["user_id", "course_id"])
    op.create_index("ix_course_purchases_mp_payment_id", "course_purchases",
                    ["mp_payment_id"])
    # Un solo acceso por (user, curso): único parcial sobre estados con acceso.
    op.execute(
        "CREATE UNIQUE INDEX uq_course_purchases_owned "
        "ON course_purchases (user_id, course_id) "
        "WHERE status IN ('approved', 'free')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_course_purchases_owned")
    op.drop_index("ix_course_purchases_mp_payment_id", table_name="course_purchases")
    op.drop_index("ix_course_purchases_user_course", table_name="course_purchases")
    op.drop_index("ix_course_purchases_user_id", table_name="course_purchases")
    op.drop_table("course_purchases")
