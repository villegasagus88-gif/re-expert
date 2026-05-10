"""Pydantic schemas for User Channels API."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ChannelKind = Literal["telegram", "whatsapp", "push", "email", "in_app"]


class ConnectTelegramResponse(BaseModel):
    """Devuelve un token de pairing y el deep link para iniciar el flujo."""
    pairing_token: str
    bot_username: str | None
    deep_link: str
    expires_at: datetime


class SetWhatsAppRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=32, description="Número con código de país, ej: +5491155555555")


class ChannelOut(BaseModel):
    id: UUID
    channel: ChannelKind
    address: str
    verified: bool
    meta: dict | None
    created_at: datetime


class ChannelListResponse(BaseModel):
    items: list[ChannelOut]
