"""
Track C (b) — atomic reminder claim (C2).

No hay Postgres en local (greenlet roto), así que verificamos el CLAIM a nivel
SQL: que el statement compile al dialecto Postgres emitiendo FOR UPDATE SKIP
LOCKED + RETURNING (lo que garantiza que dos réplicas no disparen el mismo
recordatorio). También chequeamos que toma 'pending' y 'sending' stale.
"""
from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from services.scheduler_service import STALE_CLAIM_AFTER_SECONDS, _build_claim_stmt


def _compiled_sql() -> str:
    stmt = _build_claim_stmt(datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc))
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )


def test_claim_uses_skip_locked():
    sql = _compiled_sql().upper()
    assert "FOR UPDATE SKIP LOCKED" in sql


def test_claim_returns_ids():
    sql = _compiled_sql().upper()
    assert "RETURNING" in sql
    assert "REMINDERS.ID" in sql


def test_claim_sets_sending_status():
    sql = _compiled_sql()
    assert "UPDATE reminders SET status=" in sql


def test_claim_targets_pending_and_stale_sending():
    stmt = _build_claim_stmt(datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc))
    compiled = stmt.compile(dialect=postgresql.dialect())
    # Los status van como bind params (no inline en el SQL): los chequeamos ahí.
    values = {str(v).lower() for v in compiled.params.values()}
    assert "pending" in values
    assert "sending" in values
    assert "due_at" in str(compiled).lower()


def test_stale_threshold_is_positive():
    assert STALE_CLAIM_AFTER_SECONDS > 0
