"""
Reminder scheduler.

Background task que arranca con la app (lifespan) y poll cada N segundos
los `reminders` con status='pending' y due_at <= now().

⚠️ ASUME 1 WORKER (Railway). _process_due_reminders hace SELECT status='pending'
y actualiza en loop, SIN claim atómico. Con 2+ workers se DUPLICARÍAN los envíos.
Antes de escalar a multi-worker hay que implementar el claim atómico
(UPDATE … WHERE status='pending' RETURNING / SELECT … FOR UPDATE SKIP LOCKED con
estado 'claiming:<worker_id>' + recovery de claims colgados), o un PG advisory lock.
Todavía NO está implementado.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from config.settings import settings
from models.base import get_session_factory
from models.kv_cache import KVCache
from models.password_reset import PasswordReset
from models.reminder import Reminder
from models.stripe_event import StripeEvent
from models.user import User
from services.notification_dispatcher import dispatch
from sqlalchemy import delete, select
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
                fired += 1
            else:
                _mark_retry_or_fail(r, str(result))
            await db.commit()
        except Exception as e:
            logger.exception("Reminder %s dispatch failed", r.id)
            _mark_retry_or_fail(r, str(e))
            await db.commit()
    return fired


_REMINDER_MAX_RETRIES = 3
_REMINDER_RETRY_DELAY = timedelta(minutes=5)


def _mark_retry_or_fail(r: Reminder, error: str) -> None:
    """Un fallo transitorio de dispatch NO mata el recordatorio: reintenta hasta
    _REMINDER_MAX_RETRIES corriendo due_at 5 min; recién después queda failed.
    El contador vive en meta (JSONB) — sin migración."""
    meta = dict(r.meta or {})
    attempts = int(meta.get("dispatch_attempts", 0)) + 1
    meta["dispatch_attempts"] = attempts
    r.meta = meta
    r.last_error = error[:1000]
    if attempts >= _REMINDER_MAX_RETRIES:
        r.status = "failed"
    else:
        # sigue pending; se re-agarra en un tick futuro
        r.due_at = datetime.now(timezone.utc) + _REMINDER_RETRY_DELAY


# Cleanup tablas con TTL natural — corre 1 vez por día desde el mismo
# scheduler para no agregar otro proceso. Si el backend se restartea,
# el "último run" se pierde (in-memory) y vuelve a correr el cleanup,
# que es idempotente (DELETE WHERE expires_at < now()).
_CLEANUP_PERIOD = timedelta(hours=24)

# ── Daily digest (modo Jarvis de SOL) ─────────────────────────────────
# Los usuarios activan automation_prefs (daily_summary, alert_overruns, …) vía
# SOL; este job las EJECUTA: resumen matutino por Telegram con el estado de
# sus proyectos, pagos por vencer y recordatorios del día.
_DIGEST_HOUR_UTC = settings.DIGEST_HOUR_UTC  # ~08:00 en Argentina (UTC-3)
_last_digest_date: str | None = None  # YYYY-MM-DD (AR) del último envío


async def _run_daily_digest(db: AsyncSession) -> int:
    """Manda el resumen diario a los usuarios que lo pidieron. Devuelve cuántos."""
    from models.user_channel import UserChannel
    from services.agent_service import build_context_pack

    # Solo usuarios con daily_summary activo Y telegram verificado: sin canal
    # push no hay digest (in_app sería spam invisible).
    rows = (
        await db.execute(
            select(User, UserChannel)
            .join(
                UserChannel,
                (UserChannel.user_id == User.id)
                & (UserChannel.channel == "telegram")
                & (UserChannel.verified.is_(True)),
            )
        )
    ).all()
    today_ar = (datetime.now(timezone.utc) - timedelta(hours=3)).date().isoformat()
    sent = 0
    for user, _ch in rows:
        prefs = user.automation_prefs or {}
        if not prefs.get("daily_summary"):
            continue
        # Idempotencia REAL (sobrevive reinicios/deploys y crashes a mitad del
        # loop): marca por usuario en el JSONB de prefs. La marca global
        # in-memory del tick es solo una optimización.
        if prefs.get("_last_digest_date") == today_ar:
            continue
        try:
            pack = await build_context_pack(db, user)
            if not pack:
                continue
            body = (
                "☀️ *Tu resumen de hoy*\n\n"
                + pack
                + "\n\n_Escribime acá si querés el detalle de algo._"
            )
            res = await dispatch(db, user, channel="telegram",
                                 title="", body=body)
            if res.get("ok"):
                sent += 1
                user.automation_prefs = {**prefs, "_last_digest_date": today_ar}
                await db.commit()
        except Exception:  # noqa: BLE001 — un usuario no debe frenar al resto
            logger.exception("Daily digest falló para user %s", user.id)
            await db.rollback()
    return sent
_STRIPE_EVENTS_RETENTION = timedelta(days=30)
_last_cleanup_at: datetime | None = None


async def _run_daily_cleanup(db: AsyncSession) -> dict[str, int]:
    """Borra rows con TTL natural. Devuelve cuentas por tabla.

    - `password_resets` con expires_at < now() — tokens vencidos no sirven.
    - `stripe_events` con received_at < now() - 30d — fuera de ventana
      de re-delivery de Stripe (~3 días). 30d es más que suficiente.
    - `kv_cache` vencidos — el cache persistente borra lazy solo al leer; las
      keys que vencen y nadie re-pide quedarían para siempre (leak).
    - `reminders` ya despachados/cancelados y viejos (>30d) — no se re-envían.
    """
    now = datetime.now(timezone.utc)

    # password_resets vencidos
    res_pr = await db.execute(
        delete(PasswordReset).where(PasswordReset.expires_at < now)
    )
    pr_deleted = res_pr.rowcount or 0

    # stripe_events viejos
    cutoff_stripe = now - _STRIPE_EVENTS_RETENTION
    res_se = await db.execute(
        delete(StripeEvent).where(StripeEvent.received_at < cutoff_stripe)
    )
    se_deleted = res_se.rowcount or 0

    # kv_cache vencidos (usa ix_kv_cache_expires_at → index scan)
    res_kv = await db.execute(delete(KVCache).where(KVCache.expires_at < now))
    kv_deleted = res_kv.rowcount or 0

    # reminders terminales y viejos (los pendientes NO se tocan)
    cutoff_rem = now - timedelta(days=30)
    res_rem = await db.execute(
        delete(Reminder).where(
            Reminder.status.in_(["sent", "failed", "cancelled"]),
            Reminder.due_at < cutoff_rem,
        )
    )
    rem_deleted = res_rem.rowcount or 0

    await db.commit()
    return {
        "password_resets_deleted": pr_deleted,
        "stripe_events_deleted": se_deleted,
        "kv_cache_deleted": kv_deleted,
        "reminders_deleted": rem_deleted,
    }


async def _scheduler_loop():
    """Loop principal. Sale cuando _stop_event se setea."""
    global _last_cleanup_at, _last_digest_date
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

                # Daily digest de SOL: una vez por día a partir de las
                # _DIGEST_HOUR_UTC (≈08:00 AR). La marca es por fecha AR.
                now_utc = datetime.now(timezone.utc)
                today_ar = (now_utc - timedelta(hours=3)).date().isoformat()
                if now_utc.hour >= _DIGEST_HOUR_UTC and _last_digest_date != today_ar:
                    try:
                        n = await _run_daily_digest(db)
                        if n:
                            logger.info("Daily digest enviado a %d usuarios", n)
                        _last_digest_date = today_ar
                    except Exception as e:
                        logger.exception("Daily digest error: %s", e)

                # Cleanup diario: corre si nunca corrió o pasaron 24h.
                now = datetime.now(timezone.utc)
                if (
                    _last_cleanup_at is None
                    or (now - _last_cleanup_at) >= _CLEANUP_PERIOD
                ):
                    try:
                        stats = await _run_daily_cleanup(db)
                        if any(stats.values()):
                            logger.info(
                                "Daily cleanup: %s",
                                ", ".join(f"{k}={v}" for k, v in stats.items()),
                            )
                        _last_cleanup_at = now
                    except Exception as e:
                        logger.exception("Cleanup error: %s", e)
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
    # ⚠️ Multi-worker: HOY asume 1 worker (Railway). NO hay guard de "pid menor"
    # ni claim atómico en _process_due_reminders → con 2+ workers se DUPLICARÍAN
    # recordatorios y el daily digest. Antes de escalar a multi-worker: implementar
    # el claim atómico (SELECT … FOR UPDATE SKIP LOCKED + estado 'claiming' con
    # recovery de filas colgadas). Para apagar el scheduler en un worker: DISABLE_SCHEDULER=1.
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
