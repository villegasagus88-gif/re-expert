"""
Project and Milestone models.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, server_default="Mi Proyecto")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="amarillo")
    estado_texto: Mapped[str] = mapped_column(String(255), nullable=False, server_default="Proyecto en curso")
    presupuesto_base: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    costo_real: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    avance_real_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    avance_plan_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    meses_transcurridos: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    meses_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_entrega_programada: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_entrega_estimada: Mapped[date | None] = mapped_column(Date, nullable=True)
    costos_rubros: Mapped[Any] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    alertas: Mapped[Any] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="projects")
    milestones: Mapped[list["ProjectMilestone"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectMilestone.orden"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} nombre={self.nombre!r}>"


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_objetivo: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_real: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="milestones")



    def __repr__(self) -> str:
        return f"<Milestone id={self.id} nombre={self.nombre!r} estado={self.estado}>"


from models.user import User  # noqa: E402
