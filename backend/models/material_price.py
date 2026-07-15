"""
MaterialPriceOverride — precios vivos de materiales.

El CSV curado es la base; cada actualización automática confiable
(Tavily + Claude) se guarda acá y pisa el precio del CSV en el listado.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class MaterialPriceOverride(Base):
    __tablename__ = "material_price_override"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    material: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    precio_ars: Mapped[int] = mapped_column(Integer, nullable=False)
    variacion_mensual_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    fuente: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MaterialPriceOverride {self.material[:40]} ${self.precio_ars}>"
