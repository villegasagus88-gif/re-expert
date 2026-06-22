"""
Telegram Bot integration.

Flujo de pairing:
  1. Usuario clickea "Conectar Telegram" en el frontend → POST /api/channels/telegram/connect
  2. Backend crea un UserChannel (channel='telegram', verified=False, pairing_token=<random>)
     y devuelve deep link: https://t.me/<bot_username>?start=<pairing_token>
  3. Usuario abre el link → Telegram lanza el bot con /start <pairing_token>
  4. Telegram pega el webhook (POST /api/telegram/webhook) con el message
  5. handle_webhook_update() matchea el pairing_token, marca verified=True,
     guarda chat_id en address, borra el token.
  6. SOL ya puede mandarle mensajes vía send_message().

Si TELEGRAM_BOT_TOKEN no está configurado, todas las funciones devuelven
{"error": "telegram_not_configured"} de forma controlada.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from config.settings import settings
from models.user_channel import UserChannel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


def is_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


def webhook_url() -> str | None:
    """URL pública del webhook, o None si falta TELEGRAM_WEBHOOK_BASE_URL."""
    base = (settings.TELEGRAM_WEBHOOK_BASE_URL or "").rstrip("/")
    if not base:
        return None
    return f"{base}/api/channels/telegram/webhook"


async def set_webhook() -> dict[str, Any]:
    """
    Registra el webhook del bot apuntando a nuestro endpoint público.

    Se llama en el arranque (lifespan de FastAPI). Sin esto, Telegram nunca
    pega el webhook y el pairing no funciona en un deploy nuevo. Best-effort:
    si falta TELEGRAM_BOT_TOKEN o TELEGRAM_WEBHOOK_BASE_URL, no hace nada.
    Pasa el secret (X-Telegram-Bot-Api-Secret-Token) que valida channels.py.
    """
    if not is_configured():
        return {"skipped": "telegram_not_configured"}
    url = webhook_url()
    if not url:
        return {"skipped": "no_webhook_base_url"}
    body: dict[str, Any] = {"url": url, "allowed_updates": ["message"]}
    if settings.TELEGRAM_WEBHOOK_SECRET:
        body["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            r = await cli.post(_api_url("setWebhook"), json=body)
            data = r.json()
        if not data.get("ok"):
            logger.error("Telegram setWebhook falló: %s", data)
            return {"error": "setwebhook_failed", "detail": data}
        logger.info("Telegram webhook registrado en %s", url)
        return {"ok": True, "url": url}
    except Exception as e:
        logger.exception("Telegram setWebhook exception")
        return {"error": str(e)}


async def send_message(chat_id: str, text: str) -> dict[str, Any]:
    if not is_configured():
        return {"error": "telegram_not_configured"}
    try:
        async with httpx.AsyncClient(timeout=10) as cli:
            r = await cli.post(
                _api_url("sendMessage"),
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
            )
            data = r.json()
            if not data.get("ok"):
                return {"error": "telegram_send_failed", "detail": data}
            return {"ok": True, "message_id": data["result"]["message_id"]}
    except Exception as e:
        logger.exception("Telegram send_message failed")
        return {"error": str(e)}


async def send_document(chat_id: str, file_url: str, caption: str | None = None) -> dict[str, Any]:
    if not is_configured():
        return {"error": "telegram_not_configured"}
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                _api_url("sendDocument"),
                json={
                    "chat_id": chat_id,
                    "document": file_url,
                    "caption": caption,
                },
            )
            data = r.json()
            if not data.get("ok"):
                return {"error": "telegram_send_failed", "detail": data}
            return {"ok": True}
    except Exception as e:
        logger.exception("Telegram send_document failed")
        return {"error": str(e)}


async def create_pairing(db: AsyncSession, user_id) -> dict[str, Any]:
    """
    Crea un token de pairing (1h) y devuelve el deep link.

    Si ya hay un canal Telegram verified=True para este user, devolvemos
    info de ese canal (no se hace re-pairing automático).
    """
    if not is_configured() or not settings.TELEGRAM_BOT_USERNAME:
        return {
            "error": "telegram_not_configured",
            "hint": "Falta configurar TELEGRAM_BOT_TOKEN y TELEGRAM_BOT_USERNAME en backend/.env",
        }

    # ¿Hay ya un canal verified?
    existing = (
        await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.channel == "telegram",
                UserChannel.verified.is_(True),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {
            "ok": True,
            "already_connected": True,
            "address": existing.address,
        }

    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Crear (o actualizar) un placeholder pending
    placeholder = (
        await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.channel == "telegram",
                UserChannel.verified.is_(False),
            )
        )
    ).scalar_one_or_none()
    if placeholder:
        placeholder.pairing_token = token
        placeholder.pairing_token_expires_at = expires_at
        placeholder.address = f"pending:{token[:8]}"
    else:
        placeholder = UserChannel(
            user_id=user_id,
            channel="telegram",
            address=f"pending:{token[:8]}",
            pairing_token=token,
            pairing_token_expires_at=expires_at,
            verified=False,
        )
        db.add(placeholder)
    await db.commit()

    deep_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"
    return {
        "ok": True,
        "pairing_token": token,
        "bot_username": settings.TELEGRAM_BOT_USERNAME,
        "deep_link": deep_link,
        "expires_at": expires_at.isoformat(),
    }


async def handle_webhook_update(db: AsyncSession, payload: dict) -> dict:
    """
    Procesa un update del webhook de Telegram.

    Soportamos los casos:
      - /start <pairing_token>  → matchear y verificar canal
      - mensaje libre del usuario → eco simple "Hola, soy SOL. Te avisaré por aquí."
        (No procesamos comandos arbitrarios todavía; eso vendría en Fase 2.)
    """
    msg = payload.get("message") or payload.get("edited_message")
    if not msg:
        return {"ok": True, "skipped": "no_message"}
    chat = msg.get("chat") or {}
    chat_id = str(chat.get("id"))
    text = (msg.get("text") or "").strip()

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            token = parts[1].strip()
            row = (
                await db.execute(
                    select(UserChannel).where(UserChannel.pairing_token == token)
                )
            ).scalar_one_or_none()
            if not row:
                await send_message(
                    chat_id, "❌ Token de vinculación inválido o expirado."
                )
                return {"ok": True, "matched": False}
            if (
                row.pairing_token_expires_at
                and row.pairing_token_expires_at < datetime.now(timezone.utc)
            ):
                await send_message(chat_id, "⌛ Token expirado. Pedí un link nuevo desde la app.")
                return {"ok": True, "matched": False, "expired": True}
            row.address = chat_id
            row.verified = True
            row.pairing_token = None
            row.pairing_token_expires_at = None
            display_name = chat.get("first_name") or chat.get("username") or ""
            row.meta = {
                "telegram_username": chat.get("username"),
                "telegram_first_name": chat.get("first_name"),
            }
            await db.commit()
            await send_message(
                chat_id,
                (
                    f"✅ Listo {display_name}! Quedaste conectado a *RE Expert*.\n"
                    "Te voy a avisar por acá tus recordatorios y novedades del proyecto."
                ),
            )
            return {"ok": True, "matched": True, "user_id": str(row.user_id)}
        else:
            await send_message(
                chat_id,
                "Hola! Para conectarte, abrí RE Expert y clickeá *Conectar Telegram*.",
            )
            return {"ok": True, "no_token": True}

    # Mensaje libre — saludo amable
    await send_message(
        chat_id,
        "Soy SOL 👋 Acá te aviso recordatorios y resúmenes. Para chatear largo, entrá a la app web.",
    )
    return {"ok": True, "echoed": True}
