"""
Schemas de la sección Créditos (asesor hipotecario digital).

El esquema es FUTURE-PROOF para la Fase 2 (monitoreo + validación humana):
incluye `validation_status`, `change_history`, `source_urls`, `last_checked_at`,
`status`, etc., aunque la Fase 1 solo lea/renderice. El cálculo de cuota,
compatibilidad y probabilidad lo hace el frontend (instantáneo) a partir de
estos campos.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

Audience = Literal["comprador", "desarrollador", "constructor"]
CreditType = Literal["compra", "construccion", "compra_construccion", "refaccion", "desarrollo"]
RateType = Literal["UVA", "fija", "mixta", "variable"]
ValidationStatus = Literal["approved", "pending_review", "rejected"]
CreditStatus = Literal["active", "paused", "discontinued"]


class ChangeRecord(BaseModel):
    """Un cambio detectado (Fase 2). En Fase 1 la lista viene vacía."""
    date: str
    field: str
    old_value: Any = None
    new_value: Any = None
    source: str = ""
    validation_status: ValidationStatus = "pending_review"


class CreditItem(BaseModel):
    id: str
    country: str = "Argentina"
    province: str = "Nacional"
    bank_name: str
    bank_emoji: str = "🏦"
    credit_name: str
    audience: Audience = "comprador"
    credit_type: CreditType = "compra"
    rate_type: RateType = "UVA"
    # Tasa nominal anual (TNA). Puede ser None para tasas variables (ej BADLAR+x).
    interest_rate_tna: float | None = None
    interest_rate_note: str = ""
    max_term_years: int = Field(default=20, ge=1, le=40)
    max_financing_percent: float = Field(default=75, ge=1, le=100)
    min_income_ars: float = Field(default=0, ge=0)
    min_employment_seniority_months: int = Field(default=0, ge=0)
    max_age: int | None = None
    property_value_limit_ars: float | None = None
    relacion_cuota_ingreso_max: float | None = 25
    required_savings_note: str = ""
    requirements: list[str] = []
    documents: list[str] = []
    pros: list[str] = []
    cons: list[str] = []
    extra_costs: list[str] = []
    official_url: str = ""
    source_urls: list[str] = []
    last_checked_at: str = ""
    last_updated_at: str = ""
    validation_status: ValidationStatus = "approved"
    change_history: list[ChangeRecord] = []
    status: CreditStatus = "active"


class CreditosResponse(BaseModel):
    updated_at: str
    disclaimer: str = ""
    relacion_cuota_ingreso_max_default: float = 25
    items: list[CreditItem]
