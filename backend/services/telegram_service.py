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
from fastapi import HTTPException
from models.user_channel import UserChannel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Dedupe de updates (ver handle_webhook_update). Acotado en memoria; 1 worker.
from collections import deque  # noqa: E402

_SEEN_UPDATES: set[int] = set()
_SEEN_ORDER: deque[int] = deque()
_SEEN_MAX = 2000

# Referencias fuertes a los tasks de fondo del agente (sin esto el GC los mata).
_BG_TASKS: set = set()

# Máximo de mensajes de historial que cargamos para el hilo de Telegram.
_TG_HISTORY_MAX = 14


async def _load_telegram_history(session, user_id):
    """Devuelve (conversation, history) del hilo dedicado de Telegram del usuario.
    Reusa Conversation section='sol_telegram'; la crea si no existe."""
    from models.conversation import Conversation
    from models.message import Message
    from sqlalchemy import select as _select

    conv = (await session.execute(
        _select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.section == "sol_telegram",
        ).order_by(Conversation.created_at).limit(1)
    )).scalars().first()
    if conv is None:
        conv = Conversation(user_id=user_id, title="SOL — Telegram", section="sol_telegram")
        session.add(conv)
        await session.flush()
        return conv, []
    rows = list((await session.execute(
        _select(Message).where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc()).limit(_TG_HISTORY_MAX)
    )).scalars().all())
    # El par user/assistant de un turno comparte created_at (misma transacción,
    # func.now() = transaction_timestamp): desempatamos poniendo user primero.
    rows.sort(key=lambda m: (m.created_at, 0 if m.role == "user" else 1))
    history = [{"role": m.role, "content": m.content} for m in rows if m.content]
    # Anthropic exige que el historial arranque con rol "user".
    while history and history[0]["role"] != "user":
        history.pop(0)
    return conv, history


async def _save_telegram_turn(session, conv, user_text: str, assistant_text: str) -> None:
    """Persiste el par (user, assistant) del turno de Telegram."""
    from models.message import Message

    session.add(Message(conversation_id=conv.id, role="user", content=user_text))
    session.add(Message(conversation_id=conv.id, role="assistant", content=assistant_text))
    try:
        await session.commit()
    except Exception:  # noqa: BLE001 — persistir el historial no debe romper la respuesta
        await session.rollback()
        logger.warning("No se pudo persistir el turno de Telegram (conv %s)", conv.id)


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


def is_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


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

    now = datetime.now(timezone.utc)

    # Buscar el placeholder pending (no verificado) de este user.
    placeholder = (
        await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.channel == "telegram",
                UserChannel.verified.is_(False),
            )
        )
    ).scalar_one_or_none()

    # Si ya hay un token pending VIVO, reusarlo en vez de rotarlo. Así los dos
    # puntos de generación (el botón "📲 Telegram" del front y la tool
    # connect_telegram de SOL) devuelven el MISMO link mientras siga válido: sin
    # esto, generar de nuevo invalidaba el link anterior y el usuario que tocaba
    # el viejo veía "token inválido o expirado".
    if (
        placeholder
        and placeholder.pairing_token
        and placeholder.pairing_token_expires_at
        and placeholder.pairing_token_expires_at > now
    ):
        token = placeholder.pairing_token
        expires_at = placeholder.pairing_token_expires_at
    else:
        token = secrets.token_urlsafe(24)
        expires_at = now + timedelta(hours=1)
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
      - /start <pairing_token>  → matchear y verificar canal.
      - mensaje libre de un usuario PAIREADO → si TELEGRAM_AGENT_ENABLED, corre
        el agente SOL completo en un task de fondo; si está apagado (default),
        responde un texto fijo indicando usar la app.
      - mensaje de un chat NO paireado → instrucciones para conectar la cuenta.
    """
    # Dedupe: Telegram re-entrega el mismo update si el webhook devolvió error o
    # tardó. Sin esto, un update reprocesado = doble ejecución del agente. Cache
    # en memoria acotado (Railway = 1 worker; multi-worker requeriría Redis).
    update_id = payload.get("update_id")
    if update_id is not None:
        if update_id in _SEEN_UPDATES:
            return {"ok": True, "skipped": "duplicate_update"}
        _SEEN_UPDATES.add(update_id)
        _SEEN_ORDER.append(update_id)
        if len(_SEEN_ORDER) > _SEEN_MAX:
            _SEEN_UPDATES.discard(_SEEN_ORDER.popleft())

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

    # ── Mensaje libre → SOL agente completo (modo Jarvis) ──
    # El webhook debe responder RÁPIDO (Telegram reintenta si tarda), así que
    # el agente corre en un task de fondo con sesión de DB propia y responde
    # por sendMessage cuando termina.
    if not text:
        return {"ok": True, "skipped": "empty_text"}

    row = (
        await db.execute(
            select(UserChannel).where(
                UserChannel.channel == "telegram",
                UserChannel.address == chat_id,
                UserChannel.verified.is_(True),
            )
        )
    ).scalars().first()
    if not row:
        await send_message(
            chat_id,
            "Hola! Soy SOL 👋 Para hablar conmigo, primero conectá tu cuenta: "
            "abrí RE Expert y tocá *Conectar Telegram* en la sección SOL.",
        )
        return {"ok": True, "unpaired": True}

    # Flag: el agente por Telegram está apagado por decisión de producto hasta
    # nuevo aviso (TELEGRAM_AGENT_ENABLED). El pairing de arriba y los envíos
    # salientes (recordatorios/digest) NO dependen de esto. Solo los usuarios
    # YA paireados reciben este aviso (a los demás no les prometemos nada).
    if not settings.TELEGRAM_AGENT_ENABLED:
        await send_message(
            chat_id,
            "Soy SOL 👋 Por acá te aviso recordatorios y resúmenes. "
            "Para chatear conmigo, entrá a RE Expert → sección SOL.",
        )
        return {"ok": True, "agent_disabled": True}

    if len(text) > 1500:
        await send_message(chat_id, "Uy, ese mensaje es muy largo. ¿Me lo resumís en menos palabras?")
        return {"ok": True, "too_long": True}

    import asyncio

    task = asyncio.create_task(_agent_reply(chat_id, row.user_id, text))
    _BG_TASKS.add(task)  # guardar referencia: sin esto el GC puede matar el task
    task.add_done_callback(_BG_TASKS.discard)
    return {"ok": True, "agent_dispatched": True}


async def _agent_reply(chat_id: str, user_id, text: str) -> None:
    """Corre el agente SOL con sesión propia y responde por Telegram.
    Nunca lanza: cualquier error termina en un mensaje amable al usuario."""
    from core.plan_gate import has_access
    from models.base import get_session_factory
    from models.user import User
    from services.rate_limit_service import check_user_rate_limit

    try:
        # "escribiendo…" mientras piensa (best-effort)
        if is_configured():
            try:
                async with httpx.AsyncClient(timeout=5) as cli:
                    await cli.post(_api_url("sendChatAction"),
                                   json={"chat_id": chat_id, "action": "typing"})
            except Exception:  # noqa: BLE001
                pass

        SessionLocal = get_session_factory()
        async with SessionLocal() as session:
            user = (await session.execute(
                select(User).where(User.id == user_id)
            )).scalars().first()
            if not user:
                await send_message(chat_id, "No encontré tu cuenta. Reconectá desde la app.")
                return
            if not has_access(user):
                await send_message(
                    chat_id,
                    "Tu plan no está activo 😕 Entrá a RE Expert para reactivar tu "
                    "suscripción y seguimos por acá.",
                )
                return

            # Mismo cupo que el chat in-app: un mensaje por Telegram cuesta lo
            # mismo (hasta 8 iteraciones de LLM). Sin esto, spam = gasto ilimitado.
            try:
                await check_user_rate_limit(session, user)
            except HTTPException:
                await send_message(
                    chat_id,
                    "Llegaste al límite de mensajes por ahora 😅 Probá de nuevo más tarde.",
                )
                return

            from services.agent_service import run_agent

            # Historial persistente: la confirmación de acciones necesita que el
            # token del turno anterior siga en el hilo. Reusamos una conversación
            # dedicada de Telegram por usuario.
            conv, history = await _load_telegram_history(session, user_id)

            final_text = ""
            pending_confirms: list = []
            async for ev in run_agent(session, user, history=history, user_message=text):
                if ev.get("type") == "done":
                    final_text = ev.get("final_text") or final_text
                    pending_confirms = ev.get("pending_confirmations") or []
                elif ev.get("type") == "error":
                    final_text = ""
                    break

            # Persistir el turno. Al content del assistant le anexamos el
            # marcador oculto de confirmaciones pendientes (igual que in-app);
            # lo que se ENVÍA por Telegram es final_text limpio, sin marcador.
            if final_text:
                from services.agent_service import append_confirm_marker
                await _save_telegram_turn(
                    session, conv, text,
                    append_confirm_marker(final_text, pending_confirms),
                )

        if not final_text:
            await send_message(
                chat_id,
                "No pude procesar eso ahora 😕 Probá de nuevo en un momento, "
                "o escribime desde la app.",
            )
            return
        # Telegram corta en 4096 chars por mensaje
        for i in range(0, len(final_text), 3900):
            await send_message(chat_id, final_text[i:i + 3900])
    except Exception:  # noqa: BLE001 — un task de fondo no debe morir en silencio
        logger.exception("Telegram agent_reply falló (chat %s)", chat_id)
        try:
            await send_message(chat_id, "Algo salió mal de mi lado 😕 Probá de nuevo en un rato.")
        except Exception:  # noqa: BLE001
            pass
