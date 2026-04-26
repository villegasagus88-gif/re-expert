"""
Payment model - maps to the public.payments table.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concepto: Mapped[str] = mapped_column(Text, nullable=False)
    proveedor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pendiente"
    )
    categoria: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} concepto={self.concepto!r} estado={self.estado}>"


from models.user import User  # noqa: E402
