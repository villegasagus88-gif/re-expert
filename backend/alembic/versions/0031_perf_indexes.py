"""Índices compuestos de performance para messages y token_usage

- ix_messages_conv_created (conversation_id, created_at): sirve el historial de
  una conversación ordenado por fecha y el MAX(created_at) por conversación de
  la lista de conversaciones (messages es la tabla más caliente).
- ix_token_usage_user_created (user_id, created_at): sirve las agregaciones de
  uso por usuario y ventana de tiempo (GET /api/usage, 24h/30d).

Solo AGREGA índices (no dropea nada) → seguro, ninguna query se rompe.

NOTA de escala: si algún día `messages` tiene millones de filas y mucho write
concurrente, conviene recrear estos índices con CREATE INDEX CONCURRENTLY (fuera
de transacción) para no bloquear inserts durante el deploy. Al tamaño actual, el
CREATE INDEX normal es sub-segundo y no molesta.

Revision ID: 0031_perf_indexes
Revises: 0030_add_kv_cache

NOTA: revision id <= 32 chars (alembic_version.version_num es VARCHAR(32)).
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0031_perf_indexes"
down_revision: str | None = "0030_add_kv_cache"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_conv_created", "messages", ["conversation_id", "created_at"]
    )
    op.create_index(
        "ix_token_usage_user_created", "token_usage", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_token_usage_user_created", table_name="token_usage")
    op.drop_index("ix_messages_conv_created", table_name="messages")
