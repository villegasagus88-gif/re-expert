"""
UserMaterialList — lista de compra de materiales por usuario.

Antes vivía SOLO en localStorage del navegador → se perdía al cambiar de
dispositivo o limpiar el storage. Ahora se persiste (un blob JSON por usuario:
{material: cantidad}), sincronizado desde el frontend.
"""
from datetime import datetime
from uuid import UUID

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class UserMaterialList(Base):
    __tablename__ = "user_material_list"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # {nombre_material: cantidad}. Blob simple (la lista es chica).
    items: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<UserMaterialList user={self.user_id} n={len(self.items or {})}>"
