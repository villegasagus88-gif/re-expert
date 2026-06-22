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

import html as _html
import logging
from typing import Any

from models.user import User
from models.user_channel import UserChannel
from services import email_service, telegram_service, whatsapp_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _get_channel(
    db: AsyncSession, user_id, channel: str
) -> UserChannel | None:
    # .first() (no scalar_one_or_none): si por algún motivo hay 2 canales
    # verified del mismo tipo, no queremos MultipleResultsFound — tomamos el
    # más reciente de forma determinística.
    return (
        await db.execute(
            select(UserChannel)
            .where(
                UserChannel.user_id == user_id,
                UserChannel.channel == channel,
                UserChannel.verified.is_(True),
            )
            .order_by(UserChannel.created_at.desc())
        )
    ).scalars().first()


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
        if not result.get("ok"):
            # Telegram conectado pero el envío falló → fallback a in_app (igual que
            # email/whatsapp). Sin esto, el scheduler marcaba el reminder 'failed'
            # y se perdía, aunque in_app siempre está disponible.
            logger.info(
                "telegram a %s falló (%s), fallback a in_app",
                user.id,
                result.get("error") or result.get("detail"),
            )
            return {"ok": True, "channel": "in_app", "fallback_from": "telegram",
                    "reason": result.get("error") or result.get("detail")}
        if attachment_url:
            doc = await telegram_service.send_document(ch.address, attachment_url, caption=title)
            if not doc.get("ok"):
                logger.warning("telegram send_document a %s falló: %s", user.id, doc)
        return {"ok": True, "channel": "telegram", "detail": result}

    if channel == "email":
        if not user.email:
            return {"ok": True, "channel": "in_app", "fallback_from": "email",
                    "reason": "no_email_on_file"}
        safe_body = _html.escape(body).replace("\n", "<br>")
        html_body = (
            "<div style=\"font-family:Inter,Arial,sans-serif;color:#1f2937\">"
            + (f"<h3 style=\"color:#4f46e5\">{_html.escape(title)}</h3>" if title else "")
            + f"<div>{safe_body}</div>"
            + (
                f"<p><a href=\"{attachment_url}\">Ver adjunto</a></p>"
                if attachment_url
                else ""
            )
            + "</div>"
        )
        result = await email_service.send_email(
            to=user.email,
            subject=title or "Notificación — RE Expert",
            html=html_body,
            text=body,
        )
        if not result.get("ok"):
            logger.info(
                "email a %s falló (%s), fallback a in_app",
                user.email,
                result.get("detail"),
            )
            return {"ok": True, "channel": "in_app", "fallback_from": "email",
                    "reason": result.get("detail")}
        return {"ok": True, "channel": "email", "detail": result}

    if channel == "whatsapp":
        if not user.phone:
            return {"ok": True, "channel": "in_app", "fallback_from": "whatsapp",
                    "reason": "no_phone_on_file"}
        result = await whatsapp_service.send_whatsapp(user.phone, text)
        if not result.get("ok"):
            logger.info(
                "whatsapp a %s falló (%s), fallback a in_app",
                user.phone,
                result.get("detail"),
            )
            return {"ok": True, "channel": "in_app", "fallback_from": "whatsapp",
                    "reason": result.get("detail")}
        return {"ok": True, "channel": "whatsapp", "detail": result}

    if channel == "push":
        # Push (FCM) no está implementado todavía — degradamos a in_app en vez
        # de fallar en silencio (el usuario igual lo ve en la app).
        return {"ok": True, "channel": "in_app", "fallback_from": "push",
                "reason": "push_not_implemented"}

    return {"ok": False, "error": f"canal desconocido: {channel}"}
