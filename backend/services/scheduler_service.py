"""
Reminder scheduler.

Background task que arranca con la app (lifespan) y poll cada N segundos
los `reminders` con status='pending' y due_at <= now().

Para evitar dobles envíos con múltiples workers/réplicas, el claim es ATÓMICO:
un único `UPDATE reminders SET status='sending' WHERE id IN (SELECT ... FOR
UPDATE SKIP LOCKED LIMIT n) RETURNING id`. El SKIP LOCKED hace que workers
concurrentes tomen subconjuntos disjuntos (nadie dispara el mismo recordatorio).
Recién después de claimear, disparamos y pasamos a sent/failed.

Recuperación de crash: si un worker claimea (status='sending') y muere antes de
enviar, el recordatorio quedaría trabado. Por eso el claim también re-toma filas
'sending' cuyo `updated_at` quedó más viejo que STALE_CLAIM_AFTER_SECONDS.

LIMITACIÓN CONOCIDA (entrega at-least-once): si el worker crashea/el commit falla
JUSTO entre el envío externo y el commit de status='sent', la fila queda 'sending'
y la stale-recovery la re-dispara → posible doble envío. Aceptable para
recordatorios (mejor doble que perdido); el fix definitivo (idempotencia: message
id / claimed_by, o rutear stale a needs_review) queda como follow-up.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

from config.settings import settings
from models.base import get_session_factory
from models.reminder import Reminder
from models.user import User
from services.notification_dispatcher import dispatch
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Filas que quedaron 'sending' más tiempo que esto se consideran de un worker
# crasheado y se vuelven a claimear.
STALE_CLAIM_AFTER_SECONDS = 300

_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


def _build_claim_stmt(now: datetime):
    """UPDATE atómico que claimea un batch de recordatorios disparables.

    Toma 'pending' vencidos + 'sending' stale (worker crasheado), los lockea con
    FOR UPDATE SKIP LOCKED (workers concurrentes los saltean) y los pasa a
    'sending'. Devuelve los ids claimeados (RETURNING)."""
    stale_before = now - timedelta(seconds=STALE_CLAIM_AFTER_SECONDS)
    claimable = (
        select(Reminder.id)
        .where(
            Reminder.due_at <= now,
            or_(
                Reminder.status == "pending",
                and_(
                    Reminder.status == "sending",
                    Reminder.updated_at < stale_before,
                ),
            ),
        )
        .order_by(Reminder.due_at.asc())
        .limit(settings.SCHEDULER_BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    return (
        update(Reminder)
        .where(Reminder.id.in_(claimable.scalar_subquery()))
        .values(status="sending", updated_at=now)
        .returning(Reminder.id)
        .execution_options(synchronize_session=False)
    )


async def _claim_due_reminders(db: AsyncSession, now: datetime) -> list[Reminder]:
    """Claimea atómicamente un batch y devuelve las filas Reminder a disparar."""
    ids = [row[0] for row in (await db.execute(_build_claim_stmt(now))).all()]
    await db.commit()
    if not ids:
        return []
    return list(
        (
            await db.execute(
                select(Reminder)
                .where(Reminder.id.in_(ids))
                .order_by(Reminder.due_at.asc())
            )
        )
        .scalars()
        .all()
    )


async def _process_due_reminders(db: AsyncSession) -> int:
    """Procesa hasta SCHEDULER_BATCH_SIZE recordatorios vencidos. Devuelve cuántos disparó."""
    now = datetime.now(UTC)
    rows = await _claim_due_reminders(db, now)
    if not rows:
        return 0

    fired = 0
    for r in rows:
        # Cargar el user (FK)
        user = await db.get(User, r.user_id)
        if not user:
            r.status = "failed"
            r.last_error = "user_not_found"
            await db.commit()
            continue
        try:
            result = await dispatch(
                db,
                user,
                channel=r.channel,
                title=r.title,
                body=r.body or "",
            )
            if result.get("ok"):
                r.status = "sent"
                r.sent_at = datetime.now(UTC)
                r.last_error = None
            else:
                r.status = "failed"
                r.last_error = str(result)
            await db.commit()
            fired += 1
        except Exception as e:
            logger.exception("Reminder %s dispatch failed", r.id)
            # La sesión puede haber quedado en estado fallido (ej. el commit de
            # arriba reventó): rollback primero, re-fetch la fila (quedó expirada)
            # y persistir el fallo en SU PROPIA transacción, para que un row
            # envenenado no aborte el resto del batch (PendingRollbackError).
            try:
                await db.rollback()
                r2 = await db.get(Reminder, r.id)
                if r2 is not None:
                    r2.status = "failed"
                    r2.last_error = str(e)[:1000]
                    await db.commit()
            except Exception:
                logger.exception("No se pudo marcar 'failed' el reminder %s", r.id)
                try:
                    await db.rollback()
                except Exception:
                    pass
    return fired


async def _scheduler_loop():
    """Loop principal. Sale cuando _stop_event se setea."""
    interval = settings.SCHEDULER_POLL_INTERVAL_SECONDS
    SessionLocal = get_session_factory()
    logger.info("Scheduler arrancado (poll cada %ss)", interval)
    assert _stop_event is not None
    while not _stop_event.is_set():
        try:
            async with SessionLocal() as db:
                fired = await _process_due_reminders(db)
                if fired:
                    logger.info("Scheduler disparó %d recordatorios", fired)
        except Exception as e:
            logger.exception("Scheduler tick error: %s", e)
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=interval)
        except TimeoutError:
            pass
    logger.info("Scheduler detenido")


def start_scheduler() -> None:
    """Llamar una vez en el lifespan del app."""
    global _task, _stop_event
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler deshabilitado por settings.SCHEDULER_ENABLED=False")
        return
    # Evitar arranque doble en hot-reload
    if _task and not _task.done():
        return
    # El claim atómico (FOR UPDATE SKIP LOCKED) hace seguro correr el scheduler
    # en varias réplicas a la vez. DISABLE_SCHEDULER=1 es un opt-out manual.
    if os.environ.get("DISABLE_SCHEDULER") == "1":
        logger.info("Scheduler skipped por DISABLE_SCHEDULER=1")
        return
    _stop_event = asyncio.Event()
    _task = asyncio.create_task(_scheduler_loop(), name="reminder_scheduler")


async def stop_scheduler() -> None:
    """Llamar al shutdown."""
    global _task, _stop_event
    if _stop_event:
        _stop_event.set()
    if _task:
        try:
            await asyncio.wait_for(_task, timeout=5)
        except TimeoutError:
            _task.cancel()
    _task = None
    _stop_event = None
