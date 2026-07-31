"""Botón de Arrepentimiento: pedidos de revocación.

Una tabla nueva, cero cambios sobre tablas existentes: la migración es
puramente aditiva y no reescribe ni una fila.

Existe porque la Resolución 424/2020 obliga a atender el pedido, y un pedido que
sólo viaja por email desaparece si el proveedor de mail está caído o sin
configurar. Acá queda la constancia, con `processed_at` y `admin_note` como
trazabilidad de que se atendió.

Revision ID: 0039_add_revocation_requests
Revises: 0038_add_payment_methods
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039_add_revocation_requests"
down_revision: str | None = "0038_add_payment_methods"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Cuándo el usuario aceptó los Términos y la Política al registrarse. Sin
    # esto la aceptación vive sólo en el navegador y no tiene valor probatorio,
    # que es exactamente el riesgo R18. Nullable y sin default: las cuentas que
    # ya existen quedan en NULL (no podemos inventarles una fecha que no hubo),
    # y la migración no reescribe ninguna fila.
    op.add_column(
        "profiles", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        "revocation_requests",
        sa.Column(
            "id", sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), nullable=False,
        ),
        # Arranca en 100 para que se lea como número de caso y no como "1".
        sa.Column(
            "numero", sa.Integer(),
            sa.Identity(always=False, start=100, increment=1), nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        # SET NULL, no CASCADE: el pedido es la constancia de que alguien ejerció
        # su derecho; tiene que sobrevivir a la baja de la cuenta.
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nombre", sa.String(120), server_default="", nullable=False),
        sa.Column("motivo", sa.Text(), server_default="", nullable=False),
        sa.Column("processed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("admin_note", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero", name="uq_revocation_requests_numero"),
    )
    op.create_index("ix_revocation_requests_email", "revocation_requests", ["email"])
    op.create_index(
        "ix_revocation_requests_pendientes", "revocation_requests", ["processed", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_revocation_requests_pendientes", table_name="revocation_requests")
    op.drop_index("ix_revocation_requests_email", table_name="revocation_requests")
    op.drop_table("revocation_requests")
    op.drop_column("profiles", "terms_accepted_at")
