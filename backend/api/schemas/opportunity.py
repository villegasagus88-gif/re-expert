"""
Opportunity Scanner — request/response schemas (Pydantic v2).

Las columnas escalares se validan acá; el resto de los inputs largos
(comisiones, impuestos, plazos, capital, frente/fondo, etc.) viajan en `inputs`
(dict flexible). El informe que produce el servicio se modela con los sub-modelos
de análisis (FinancialScenario, SensitivityResult, RiskItem, Recommendation, ...).
"""
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from core.sanitize import SanitizedOptStr, SanitizedStr
from pydantic import BaseModel, Field

_TIPO = "^(terreno|departamento|ph|casa|local|oficina|galpon|edificio|pozo|otro)$"
_OBJETIVO = "^(vivir|invertir|renta|desarrollar|vender|tasar|comparar)$"
_PIPELINE = "^(nueva|en_analisis|shortlist|descartada|cerrada)$"
_MONEDA = "^(USD|ARS)$"


# ── Requests ──

class CreateOpportunityRequest(BaseModel):
    titulo: SanitizedStr = Field(default="Oportunidad", min_length=1, max_length=255)
    zona: SanitizedOptStr = Field(default=None, max_length=160)
    ciudad: SanitizedOptStr = Field(default=None, max_length=120)
    tipo_inmueble: str = Field(default="terreno", pattern=_TIPO)
    objetivo: str | None = Field(default=None, pattern=_OBJETIVO)
    superficie_terreno_m2: float | None = Field(default=None, ge=0, le=1_000_000)
    m2_vendibles: float | None = Field(default=None, ge=0, le=1_000_000)
    precio_pedido: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    costo_obra_m2: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    precio_venta_m2: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    moneda: str = Field(default="USD", pattern=_MONEDA)
    estado_pipeline: str = Field(default="nueva", pattern=_PIPELINE)
    # Inputs adicionales (comisión, impuestos, honorarios, plazos, preventa,
    # capital propio, financiación, frente/fondo, contingencia, etc.).
    inputs: dict[str, Any] = Field(default_factory=dict)


class UpdateOpportunityRequest(BaseModel):
    titulo: SanitizedOptStr = Field(default=None, min_length=1, max_length=255)
    zona: SanitizedOptStr = Field(default=None, max_length=160)
    ciudad: SanitizedOptStr = Field(default=None, max_length=120)
    tipo_inmueble: str | None = Field(default=None, pattern=_TIPO)
    objetivo: str | None = Field(default=None, pattern=_OBJETIVO)
    superficie_terreno_m2: float | None = Field(default=None, ge=0, le=1_000_000)
    m2_vendibles: float | None = Field(default=None, ge=0, le=1_000_000)
    precio_pedido: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    costo_obra_m2: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    precio_venta_m2: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    moneda: str | None = Field(default=None, pattern=_MONEDA)
    estado_pipeline: str | None = Field(default=None, pattern=_PIPELINE)
    inputs: dict[str, Any] | None = None


class ExtractRequest(BaseModel):
    """Pegar una URL de publicación o texto libre para que la IA extraiga inputs."""
    texto: SanitizedOptStr = Field(default=None, max_length=8000)
    url: str | None = Field(default=None, max_length=2000)


# ── Sub-modelos del análisis (estructura del JSONB analysis) ──

class FinancialScenario(BaseModel):
    nombre: str                      # base | optimista | pesimista
    probabilidad: float              # %, los 3 suman 100
    precio_venta_m2: float | None = None
    costo_obra_m2: float | None = None
    margen_neto_pct: float | None = None
    roi_pct: float | None = None
    tir_pct: float | None = None
    comentario: str = ""


class SensitivityPoint(BaseModel):
    variacion_pct: float
    margen_neto_pct: float | None = None
    roi_pct: float | None = None
    decision: str = ""


class SensitivityResult(BaseModel):
    variable: str                    # costo_obra | precio_venta | precio_entrada | ...
    puntos: list[SensitivityPoint] = Field(default_factory=list)


class RiskItem(BaseModel):
    tipo: str                        # mercado | legal | financiero | tecnico | regulatorio | dato_faltante
    severidad: str                   # alta | media | baja
    descripcion: str
    mitigacion: str = ""


class SourceCitation(BaseModel):
    nombre: str
    url: str | None = None
    fecha_consulta: str | None = None
    confianza: float = 0.0
    estado: str = "no_conectada"     # conectada | no_conectada | estimacion | dato_usuario


class Recommendation(BaseModel):
    veredicto: str                   # avanzar | due_diligence | negociar | esperar | reformular | descartar | mas_info
    score: int
    resumen: str
    precio_max_compra: float | None = None
    rango_venta_viable: str | None = None
    condicion_minima: str | None = None
    riesgo_principal: str | None = None
    proximos_pasos: list[str] = Field(default_factory=list)


class OpportunityAnalysis(BaseModel):
    score: int
    recomendacion: Recommendation | None = None
    finanzas: dict[str, Any] = Field(default_factory=dict)   # inversión total, márgenes, ROI, TIR, break-even...
    escenarios: list[FinancialScenario] = Field(default_factory=list)
    sensibilidad: list[SensitivityResult] = Field(default_factory=list)
    riesgos: list[RiskItem] = Field(default_factory=list)
    checklist_faltantes: list[str] = Field(default_factory=list)
    lectura_mercado: str | None = None
    supuestos: list[str] = Field(default_factory=list)
    fuentes: list[SourceCitation] = Field(default_factory=list)
    parcial: bool = False            # true si la capa LLM o un data service falló
    generated_at: str | None = None


# ── Responses ──

class OpportunityOut(BaseModel):
    id: UUID
    project_id: UUID | None
    titulo: str
    zona: str | None
    ciudad: str | None
    tipo_inmueble: str
    objetivo: str | None
    superficie_terreno_m2: float | None
    m2_vendibles: float | None
    precio_pedido: Decimal | None
    costo_obra_m2: Decimal | None
    precio_venta_m2: Decimal | None
    moneda: str
    score: float | None
    recomendacion: str | None
    estado_pipeline: str
    inputs: dict[str, Any]
    analysis: dict[str, Any]
    last_analyzed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OpportunitiesSummary(BaseModel):
    count_total: int
    count_shortlist: int
    count_descartada: int
    avg_score: float | None


class OpportunitiesListResponse(BaseModel):
    items: list[OpportunityOut]
    summary: OpportunitiesSummary
    total: int


class ExtractResponse(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    fuentes: list[SourceCitation] = Field(default_factory=list)
    nota: str = ""
    parcial: bool = False
