"""
MaterialInterest — eventos de búsqueda/compra de materiales.

Alimenta el orden "más buscados primero" de la lupa inteligente de
Cotización de Materiales, y de paso le dice al dueño qué materiales
le interesan más a los usuarios.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class MaterialInterest(Base):
    __tablename__ = "material_interest"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    material: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False, server_default="search")  # search | buy
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MaterialInterest {self.action}: {self.material[:40]}>"
