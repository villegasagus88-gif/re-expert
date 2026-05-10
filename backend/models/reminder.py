"""
Reminder model — recordatorios programados que SOL dispara hacia el usuario.

Cada recordatorio tiene un `due_at` (cuándo dispararlo), un `channel`
(in_app/email/telegram/whatsapp/push) y un `status` que recorre
pending → sent (o failed/cancelled). El scheduler poll cada N segundos
los recordatorios `pending` con `due_at <= now()` y los entrega vía el
notification_dispatcher al canal configurado del usuario.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Reminder(Base):
    __tablename__ = "reminders"

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
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ISO datetime (UTC) cuando dispararlo.
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # Canal preferido. "in_app" siempre funciona como fallback.
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="in_app"
    )
    # pending | sent | failed | cancelled
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending", index=True
    )
    # Datos opcionales (ej. {"payment_id": "...", "context": "..."})
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Última razón de fallo si status=failed
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Fecha de envío real (cuando status pasa a sent)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_reminders_due_status", "due_at", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Reminder id={self.id} title={self.title!r} "
            f"due_at={self.due_at} status={self.status}>"
        )
