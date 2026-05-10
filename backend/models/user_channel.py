"""
UserChannel model — canales conectados de cada usuario.

Cada usuario puede tener múltiples canales (Telegram, WhatsApp, Push, Email).
El notification_dispatcher consulta esta tabla para saber a dónde enviar
recordatorios y mensajes proactivos. `verified=True` indica que el usuario
completó el flujo de pairing del canal (ej. mandó /start al bot de Telegram).
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class UserChannel(Base):
    __tablename__ = "user_channels"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # telegram | whatsapp | push | email | in_app
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    # Identificador externo (telegram_chat_id, whatsapp_phone, push_endpoint, email)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    # Datos extra del canal (subscription keys, display name, etc.)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Si el canal completó pairing/opt-in (ej. usuario mandó /start al bot)
    verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    # Token de pairing temporal (one-shot) para flujos como Telegram /start <token>
    pairing_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    pairing_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "channel", "address", name="uq_user_channel_addr"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserChannel user={self.user_id} channel={self.channel} "
            f"verified={self.verified}>"
        )
