"""
CoursePurchase — compras de cursos de la Academia (pago único vía Mercado Pago
Checkout Pro). El entitlement (acceso al curso) vive en NUESTRA DB: MP es solo
el medio de cobro. Un curso gratis se registra con status='free' (sin MP).

Estados:
  pending   → preference creada, esperando el pago en MP.
  approved  → pago aprobado (webhook) → el usuario tiene acceso.
  rejected  → pago rechazado.
  refunded  → reembolsado.
  free      → curso gratis, inscripción directa sin cobro.
  duplicate → pago aprobado de un curso que el usuario YA tenía (pagó dos
              veces): no da acceso extra, requiere reembolso manual.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class CoursePurchase(Base):
    __tablename__ = "course_purchases"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    course_id: Mapped[str] = mapped_column(String(80), nullable=False)
    course_title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Carrito: las compras de un mismo checkout comparten order_id (la
    # preference de MP lleva external_reference=order_id). Null = compra suelta.
    order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True,
    )
    price_ars: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    mp_preference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mp_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    __table_args__ = (
        Index("ix_course_purchases_user_course", "user_id", "course_id"),
    )

    def __repr__(self) -> str:
        return f"<CoursePurchase user={self.user_id} course={self.course_id} status={self.status}>"
