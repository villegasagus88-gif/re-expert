"""Cuenta: 2FA (authenticator/email), cambio de email verificado y baja con gracia de 30 días.

Todas las columnas van sobre `profiles`, todas NULLABLE y sin default que
reescriba filas: la migración es puramente aditiva (ALTER TABLE ADD COLUMN
sin rewrite en Postgres). Cero riesgo para los datos existentes.

- twofa_method / twofa_secret / twofa_pending_secret / twofa_recovery:
  doble factor. `method` es 'totp' (app authenticator) o 'email'. El secret
  pendiente vive aparte hasta que el usuario confirma el primer código.
  `twofa_recovery` guarda los códigos de recuperación HASHEADOS (sha256).
- twofa_code_hash / twofa_code_expires_at: código de un solo uso para el
  método email (login) y para confirmar la activación por email.
- pending_email / pending_email_code_hash / pending_email_expires_at:
  cambio de email en dos pasos (el código viaja al correo NUEVO).
- deletion_requested_at: pedido de baja. El login lo cancela; a los 30 días
  el cleanup diario purga la cuenta (FK ondelete CASCADE hace el resto).

Revision ID: 0037_add_account_security
Revises: 0036_add_bug_reports
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0037_add_account_security"
down_revision: str | None = "0036_add_bug_reports"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("twofa_method", sa.String(10), nullable=True))
    op.add_column("profiles", sa.Column("twofa_secret", sa.Text(), nullable=True))
    op.add_column("profiles", sa.Column("twofa_pending_secret", sa.Text(), nullable=True))
    op.add_column("profiles", sa.Column("twofa_recovery", JSONB(), nullable=True))
    op.add_column("profiles", sa.Column("twofa_code_hash", sa.String(64), nullable=True))
    op.add_column("profiles", sa.Column(
        "twofa_code_expires_at", sa.DateTime(timezone=True), nullable=True))
    # Intentos fallidos contra el código vigente. Sin esto el rate limit es solo
    # por IP y un atacante distribuido recorre los 10^6 códigos en la ventana.
    op.add_column("profiles", sa.Column(
        "twofa_code_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("profiles", sa.Column("pending_email", sa.String(255), nullable=True))
    op.add_column("profiles", sa.Column("pending_email_code_hash", sa.String(64), nullable=True))
    op.add_column("profiles", sa.Column(
        "pending_email_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("profiles", sa.Column(
        "deletion_requested_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for col in (
        "deletion_requested_at",
        "pending_email_expires_at",
        "pending_email_code_hash",
        "pending_email",
        "twofa_code_attempts",
        "twofa_code_expires_at",
        "twofa_code_hash",
        "twofa_recovery",
        "twofa_pending_secret",
        "twofa_secret",
        "twofa_method",
    ):
        op.drop_column("profiles", col)
