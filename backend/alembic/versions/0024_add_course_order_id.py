"""course_purchases.order_id: carrito — varias compras en un solo pago de MP.

Las compras de un mismo carrito comparten order_id; la preference de MP lleva
external_reference=order_id y el webhook aplica el pago a toda la orden.
Nullable: las compras individuales (pre-carrito) siguen sin orden.

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024_course_order_id"
down_revision: str | None = "0023_course_purchases"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "course_purchases",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_course_purchases_order_id", "course_purchases", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_course_purchases_order_id", table_name="course_purchases")
    op.drop_column("course_purchases", "order_id")
