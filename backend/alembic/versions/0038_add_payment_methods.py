"""Facturación: tarjetas guardadas y cobros fallidos.

Dos tablas NUEVAS, cero cambios sobre tablas existentes: la migración es
puramente aditiva y no reescribe ni una fila.

`payment_methods` NO guarda datos de tarjeta. Solo los identificadores de la
bóveda de Mercado Pago (`mp_customer_id`, `mp_card_id`) y lo que sirve para que
el usuario reconozca la suya en pantalla (marca, últimos cuatro). El número, el
vencimiento completo y el código de seguridad nunca llegan a nuestro backend.

`billing_issues` registra un cobro rechazado para no cortar el acceso de
inmediato: mientras el issue está abierto y dentro de la gracia, el usuario
conserva el servicio y la app le ofrece pagar con su tarjeta de respaldo.

Revision ID: 0038_add_payment_methods
Revises: 0037_add_account_security
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038_add_payment_methods"
down_revision: str | None = "0037_add_account_security"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Fecha del próximo cobro, que informa Mercado Pago en el preapproval. Se
    # guarda para poder avisar ANTES de cada renovación, que es lo que los
    # Términos prometen (y lo que desactiva el reclamo de "me cobraron sin
    # avisar"). Nullable y sin default: no reescribe ninguna fila.
    op.add_column(
        "profiles", sa.Column("next_charge_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "profiles", sa.Column("charge_notice_sent_for", sa.DateTime(timezone=True), nullable=True)
    )
    # Importe del próximo cobro, como lo informa MP. Los Términos prometen
    # avisar "el importe y la fecha": sin esto el aviso saldría a medias.
    op.add_column(
        "profiles", sa.Column("next_charge_amount", sa.Numeric(12, 2), nullable=True)
    )

    op.create_table(
        "payment_methods",
        sa.Column(
            "id", sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), nullable=False,
        ),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mp_customer_id", sa.String(64), nullable=False),
        sa.Column("mp_card_id", sa.String(64), nullable=False),
        sa.Column("brand", sa.String(30), server_default="", nullable=False),
        sa.Column("last_four", sa.String(4), server_default="", nullable=False),
        sa.Column("exp_month", sa.Integer(), nullable=True),
        sa.Column("exp_year", sa.Integer(), nullable=True),
        sa.Column("holder_name", sa.String(120), server_default="", nullable=False),
        sa.Column("role", sa.String(12), server_default="principal", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Sólo dos roles posibles: la tarjeta con la que se cobra y la alternativa.
        sa.CheckConstraint("role IN ('principal','respaldo')", name="ck_payment_methods_role"),
    )
    op.create_index("ix_payment_methods_user_id", "payment_methods", ["user_id"])
    op.create_index(
        "ix_payment_methods_user_card", "payment_methods",
        ["user_id", "mp_card_id"], unique=True,
    )

    op.create_table(
        "billing_issues",
        sa.Column(
            "id", sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), nullable=False,
        ),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(80), server_default="", nullable=False),
        sa.Column("mp_payment_id", sa.String(64), server_default="", nullable=False),
        sa.Column("resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("grace_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pending_downgrade", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("retry_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_issues_user_id", "billing_issues", ["user_id"])
    op.create_index("ix_billing_issues_user_open", "billing_issues", ["user_id", "resolved"])
    # Un solo cobro pendiente por usuario. Es la red que hace idempotente al
    # webhook aunque MP entregue dos notificaciones en paralelo.
    op.create_index(
        "ix_billing_issues_uno_abierto", "billing_issues", ["user_id"],
        unique=True, postgresql_where=sa.text("resolved = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_billing_issues_uno_abierto", table_name="billing_issues")
    op.drop_index("ix_billing_issues_user_open", table_name="billing_issues")
    op.drop_index("ix_billing_issues_user_id", table_name="billing_issues")
    op.drop_table("billing_issues")
    op.drop_index("ix_payment_methods_user_card", table_name="payment_methods")
    op.drop_index("ix_payment_methods_user_id", table_name="payment_methods")
    op.drop_table("payment_methods")
    op.drop_column("profiles", "next_charge_amount")
    op.drop_column("profiles", "charge_notice_sent_for")
    op.drop_column("profiles", "next_charge_at")
