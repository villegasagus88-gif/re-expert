"""
Project and Milestone request/response schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from core.sanitize import SanitizedOptStr, SanitizedStr
from pydantic import BaseModel, Field


class CostoRubro(BaseModel):
    nombre: SanitizedStr = Field(min_length=1, max_length=100)
    base: Decimal = Field(ge=0, decimal_places=2)
    real: Decimal = Field(ge=0, decimal_places=2)


class AlertaItem(BaseModel):
    titulo: SanitizedStr = Field(min_length=1, max_length=200)
    descripcion: SanitizedStr = Field(min_length=1, max_length=500)
    severidad: str = Field(pattern="^(high|medium|low)$")


# ── Project requests ──

class CreateProjectRequest(BaseModel):
    nombre: SanitizedStr = Field(default="Mi Proyecto", min_length=1, max_length=255)
    estado: str = Field(default="amarillo", pattern="^(verde|amarillo|rojo)$")
    estado_texto: SanitizedStr = Field(default="Proyecto en curso", min_length=1, max_length=255)
    presupuesto_base: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    costo_real: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    avance_real_pct: float = Field(default=0.0, ge=0, le=100)
    avance_plan_pct: float = Field(default=0.0, ge=0, le=100)
    meses_transcurridos: int = Field(default=0, ge=0)
    meses_total: int = Field(default=0, ge=0)
    fecha_inicio: date | None = None
    fecha_entrega_programada: date | None = None
    fecha_entrega_estimada: date | None = None
    costos_rubros: list[CostoRubro] = Field(default_factory=list)
    alertas: list[AlertaItem] = Field(default_factory=list)
    notas: SanitizedOptStr = Field(default=None, max_length=2000)


class UpdateProjectRequest(BaseModel):
    nombre: SanitizedOptStr = Field(default=None, min_length=1, max_length=255)
    estado: str | None = Field(default=None, pattern="^(verde|amarillo|rojo)$")
    estado_texto: SanitizedOptStr = Field(default=None, min_length=1, max_length=255)
    presupuesto_base: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    costo_real: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    avance_real_pct: float | None = Field(default=None, ge=0, le=100)
    avance_plan_pct: float | None = Field(default=None, ge=0, le=100)
    meses_transcurridos: int | None = Field(default=None, ge=0)
    meses_total: int | None = Field(default=None, ge=0)
    fecha_inicio: date | None = None
    fecha_entrega_programada: date | None = None
    fecha_entrega_estimada: date | None = None
    costos_rubros: list[CostoRubro] | None = None
    alertas: list[AlertaItem] | None = None
    notas: SanitizedOptStr = Field(default=None, max_length=2000)


# ── Milestone requests ──

class CreateMilestoneRequest(BaseModel):
    nombre: SanitizedStr = Field(min_length=1, max_length=255)
    fecha_objetivo: date
    fecha_real: date | None = None
    estado: str = Field(default="pending", pattern="^(done|active|pending|delayed)$")
    detalle: SanitizedOptStr = Field(default=None, max_length=1000)
    orden: int = Field(default=0, ge=0)


class UpdateMilestoneRequest(BaseModel):
    nombre: SanitizedOptStr = Field(default=None, min_length=1, max_length=255)
    fecha_objetivo: date | None = None
    fecha_real: date | None = None
    estado: str | None = Field(default=None, pattern="^(done|active|pending|delayed)$")
    detalle: SanitizedOptStr = Field(default=None, max_length=1000)
    orden: int | None = Field(default=None, ge=0)


# ── Responses ──

class ProjectOut(BaseModel):
    id: UUID
    nombre: str
    estado: str
    estado_texto: str
    presupuesto_base: Decimal
    costo_real: Decimal
    avance_real_pct: float
    avance_plan_pct: float
    meses_transcurridos: int
    meses_total: int
    fecha_inicio: date | None
    fecha_entrega_programada: date | None
    fecha_entrega_estimada: date | None
    costos_rubros: list[Any]
    alertas: list[Any]
    notas: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MilestoneOut(BaseModel):
    id: UUID
    nombre: str
    fecha_objetivo: date
    fecha_real: date | None
    estado: str
    detalle: str | None
    orden: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectIndicators(BaseModel):
    cpi: float | None
    spi: float | None
    eac: Decimal | None
    desvio_proyectado: Decimal | None
    pct_ejecutado: float


class ProjectDashboard(BaseModel):
    project: ProjectOut
    indicators: ProjectIndicators
    milestones: list[MilestoneOut]
