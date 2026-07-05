"""payments.source: audit trail de pagos creados por el agente SOL.

'sol' = lo registró el agente (vía confirm_action), NULL = carga manual.
milestones y materials YA tienen source desde su migración original; solo
payments carecía de la columna.

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026_add_source_audit"
down_revision: str | None = "0025_add_plan_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("source", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "source")
