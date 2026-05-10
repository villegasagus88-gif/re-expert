"""
User channels endpoints.

Permite al usuario:
  - Listar canales conectados
  - Iniciar pairing de Telegram (devuelve deep link)
  - Borrar/desconectar un canal
  - Recibir webhook de Telegram (no protegido por auth — usa secret header)
"""
# Nota: evitar `from __future__ import annotations` en archivos de rutas FastAPI
# (los body params quedan como ForwardRef y rompen el OpenAPI).
import logging
from uuid import UUID

from api.schemas.channel import ChannelListResponse, ChannelOut, ConnectTelegramResponse
from config.settings import settings
from core.auth import get_current_user
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from models.base import get_db
from models.user import User
from models.user_channel import UserChannel
from services import telegram_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = list(
        (
            await db.execute(
                select(UserChannel).where(UserChannel.user_id == current_user.id)
            )
        )
        .scalars()
        .all()
    )
    return ChannelListResponse(
        items=[
            ChannelOut(
                id=c.id,
                channel=c.channel,
                address=c.address,
                verified=c.verified,
                meta=c.meta,
                created_at=c.created_at,
            )
            for c in rows
        ]
    )


@router.post("/telegram/connect", response_model=ConnectTelegramResponse)
async def connect_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await telegram_service.create_pairing(db, current_user.id)
    if "error" in res:
        raise HTTPException(503, res)
    if res.get("already_connected"):
        # Ya estaba conectado: devolver una "no-op" con info igual válida
        return ConnectTelegramResponse(
            pairing_token="",
            bot_username=settings.TELEGRAM_BOT_USERNAME or None,
            deep_link=f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}",
            expires_at=None,  # type: ignore[arg-type]
        )
    return ConnectTelegramResponse(
        pairing_token=res["pairing_token"],
        bot_username=res.get("bot_username"),
        deep_link=res["deep_link"],
        expires_at=res["expires_at"],  # type: ignore[arg-type]
    )


@router.delete("/{channel_id}", status_code=204)
async def disconnect_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await db.get(UserChannel, channel_id)
    if not c or c.user_id != current_user.id:
        raise HTTPException(404, "Canal no encontrado")
    await db.delete(c)
    await db.commit()
    return None


# ─── Webhook Telegram (no auth) ───────────────────────────────────────
# Telegram pega aquí. Validamos vía X-Telegram-Bot-Api-Secret-Token igualando
# settings.TELEGRAM_WEBHOOK_SECRET. Si no coincide → 403.
@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    if not telegram_service.is_configured():
        raise HTTPException(503, "telegram_not_configured")
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(403, "bad_secret")
    payload = await request.json()
    return await telegram_service.handle_webhook_update(db, payload)
