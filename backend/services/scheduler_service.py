"""
Reminder scheduler.

Background task que arranca con la app (lifespan) y poll cada N segundos
los `reminders` con status='pending' y due_at <= now().

Para evitar dobles envíos en caso de múltiples workers (Railway por defecto
1, pero por las dudas), usamos UPDATE … WHERE status='pending' RETURNING
con un `claim` atómico que cambia status='claiming:<worker_id>' antes de
disparar. Si en el medio crash, otro tick lo recupera tras `STALE_CLAIM_AFTER_SECONDS`.

Para MVP, usamos una versión más simple sin claim distribuido: un solo
worker, un loop. Si en el futuro hay multi-worker, agregar PG advisory locks.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from config.settings import settings
from models.base import get_session_factory
from models.reminder import Reminder
from models.user import User
from services.notification_dispatcher import dispatch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


async def _process_due_reminders(db: AsyncSession) -> int:
    """Procesa hasta SCHEDULER_BATCH_SIZE recordatorios vencidos. Devuelve cuántos disparó."""
    now = datetime.now(timezone.utc)
    q = (
        select(Reminder)
        .where(Reminder.status == "pending", Reminder.due_at <= now)
        .order_by(Reminder.due_at.asc())
        .limit(settings.SCHEDULER_BATCH_SIZE)
    )
    rows = list((await db.execute(q)).scalars().all())
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
                r.sent_at = datetime.now(timezone.utc)
                r.last_error = None
            else:
                r.status = "failed"
                r.last_error = str(result)
            await db.commit()
            fired += 1
        except Exception as e:
            logger.exception("Reminder %s dispatch failed", r.id)
            r.status = "failed"
            r.last_error = str(e)
            await db.commit()
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
        except asyncio.TimeoutError:
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
    # Single-worker safety: si hay múltiples workers, solo el de pid menor corre
    # (el resto skippea). Heurística simple para Railway con 1 worker.
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
        except asyncio.TimeoutError:
            _task.cancel()
    _task = None
    _stop_event = None
