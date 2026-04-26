"""
Material model - maps to public.materials.

Cotización o precio actualizado de un material (carga típica vía SOL).
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)  # m2, m3, kg, ud, bolsa, etc.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="ARS")
    supplier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quoted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default="sol")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<Material id={self.id} name={self.name!r} "
            f"price={self.unit_price} {self.currency}/{self.unit}>"
        )
