"""
Opportunity model — analizador de oportunidades inmobiliarias (Opportunity Scanner).

A diferencia de Project (1 por usuario), un usuario tiene MUCHAS oportunidades
(un pipeline / Deal Room). Las columnas escalares son las consultables/filtrables
(Deal Room, comparador); el resto del análisis y los inputs largos viven en JSONB
para flexibilidad y versionado.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, Float, ForeignKey, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Vínculo opcional con el Panel de Proyecto (una oportunidad "ganada" puede,
    # a futuro, convertirse/linkearse a un Project). Nullable: hoy son universos
    # separados, pero la columna queda lista.
    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Escalares consultables (Deal Room / comparador / filtros) ──
    titulo: Mapped[str] = mapped_column(String(255), nullable=False, server_default="Oportunidad")
    zona: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tipo_inmueble: Mapped[str] = mapped_column(String(40), nullable=False, server_default="terreno")
    objetivo: Mapped[str | None] = mapped_column(String(40), nullable=True)

    superficie_terreno_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    m2_vendibles: Mapped[float | None] = mapped_column(Float, nullable=True)
    precio_pedido: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    costo_obra_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    precio_venta_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")

    # Cache del último análisis (para listar/ordenar sin abrir el JSONB)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recomendacion: Mapped[str | None] = mapped_column(String(24), nullable=True)
    estado_pipeline: Mapped[str] = mapped_column(String(24), nullable=False, server_default="nueva")

    # ── JSONB: snapshot de inputs + informe completo ──
    inputs: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    analysis: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Opportunity id={self.id} titulo={self.titulo!r} score={self.score}>"
