"""
Notification dispatcher.

Centraliza el envío de notificaciones del usuario a través de cualquiera
de los canales conectados (in_app, email, telegram, whatsapp, push).

Si el canal solicitado no está configurado/verificado para el usuario,
hace fallback a in_app (siempre disponible) y registra el intento.

Uso típico desde scheduler_service o agent_tools.send_message_now:

    await dispatch(
        db, user, channel="telegram",
        title="Recordatorio", body="Llamar al proveedor a las 10."
    )
"""
from __future__ import annotations

import logging
from typing import Any

from models.user import User
from models.user_channel import UserChannel
from services import telegram_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _get_channel(
    db: AsyncSession, user_id, channel: str
) -> UserChannel | None:
    return (
        await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.channel == channel,
                UserChannel.verified.is_(True),
            )
        )
    ).scalar_one_or_none()


async def dispatch(
    db: AsyncSession,
    user: User,
    *,
    channel: str,
    title: str,
    body: str,
    attachment_url: str | None = None,
) -> dict[str, Any]:
    """
    Envía una notificación. Devuelve dict con `{ok, channel, fallback?, detail?}`.
    """
    text = f"*{title}*\n\n{body}" if title else body

    if channel == "in_app":
        # Para "in_app" simplemente registramos — el frontend la consulta vía
        # /api/reminders. No hace falta push real.
        return {"ok": True, "channel": "in_app", "delivered": True}

    if channel == "telegram":
        ch = await _get_channel(db, user.id, "telegram")
        if not ch:
            logger.info("user %s no tiene Telegram verified, fallback a in_app", user.id)
            return {
                "ok": True,
                "channel": "in_app",
                "fallback_from": "telegram",
                "reason": "channel_not_connected",
            }
        result = await telegram_service.send_message(ch.address, text)
        if attachment_url and result.get("ok"):
            await telegram_service.send_document(ch.address, attachment_url, caption=title)
        return {"ok": result.get("ok", False), "channel": "telegram", "detail": result}

    if channel == "email":
        # Stub — implementación cuando se configure RESEND_API_KEY
        return {
            "ok": False,
            "channel": "email",
            "detail": "email_not_implemented_yet",
        }

    if channel == "whatsapp":
        return {
            "ok": False,
            "channel": "whatsapp",
            "detail": "whatsapp_not_implemented_yet",
        }

    if channel == "push":
        return {
            "ok": False,
            "channel": "push",
            "detail": "push_not_implemented_yet",
        }

    return {"ok": False, "error": f"canal desconocido: {channel}"}
