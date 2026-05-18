"""
StripeEvent — append-only log of received Stripe webhook events.

Used for **idempotency**: Stripe retries delivery (up to 3 days) on any
non-2xx or timeout > 5s, so the same event_id can arrive multiple times.
On each webhook hit we INSERT the event_id with its UNIQUE constraint;
on conflict we know it was already processed and skip side-effects.

Also serves as an audit trail for billing operations.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    # Stripe event id (e.g. "evt_1NxYz..."). UNIQUE — used for idempotency.
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<StripeEvent {self.event_type} {self.event_id}>"
