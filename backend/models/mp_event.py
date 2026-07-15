"""
MpEvent — log append-only de webhooks de Mercado Pago recibidos.

Doble propósito (igual que StripeEvent):
  - Idempotencia a nivel ENTREGA: `request_id` (header x-request-id de MP) es
    único por entrega HTTP. Insertamos con UNIQUE; si ya existe, es una entrega
    exacta repetida y saltamos los side-effects. NO deduplica reintentos de MP
    con distinto request_id (esos re-consultan el estado vivo en MP y se aplican
    idempotentemente), así que NUNCA se descarta una transición legítima.
  - Audit trail de las notificaciones de billing (data_id, tipo, cuándo).

request_id es nullable: si MP no manda el header, se registra con NULL (Postgres
permite múltiples NULL en un UNIQUE) y esa notificación no se deduplica.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class MpEvent(Base):
    __tablename__ = "mp_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    # x-request-id de MP: único por entrega. UNIQUE → idempotencia de entrega.
    request_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    data_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notif_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MpEvent {self.notif_type} req={self.request_id}>"
