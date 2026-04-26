"""
Payment CRUD request/response schemas.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from core.sanitize import SanitizedOptStr, SanitizedStr
from pydantic import BaseModel, Field

# ── Requests ──

class CreatePaymentRequest(BaseModel):
    concepto: SanitizedStr = Field(min_length=1, max_length=500)
    proveedor: SanitizedOptStr = Field(default=None, max_length=255)
    monto: Decimal = Field(gt=0, decimal_places=2)
    fecha: date
    estado: str = Field(default="pendiente", pattern="^(pendiente|pagado|cancelado)$")
    categoria: SanitizedOptStr = Field(default=None, max_length=100)
    notas: SanitizedOptStr = Field(default=None, max_length=2000)


class UpdatePaymentRequest(BaseModel):
    concepto: SanitizedOptStr = Field(default=None, min_length=1, max_length=500)
    proveedor: SanitizedOptStr = Field(default=None, max_length=255)
    monto: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    fecha: date | None = None
    estado: str | None = Field(default=None, pattern="^(pendiente|pagado|cancelado)$")
    categoria: SanitizedOptStr = Field(default=None, max_length=100)
    notas: SanitizedOptStr = Field(default=None, max_length=2000)


# ── Responses ──

class PaymentOut(BaseModel):
    id: UUID
    concepto: str
    proveedor: str | None
    monto: Decimal
    fecha: date
    estado: str
    categoria: str | None
    notas: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentsSummary(BaseModel):
    total_pagado: Decimal
    total_pendiente: Decimal
    total_cancelado: Decimal
    grand_total: Decimal
    count_pagado: int
    count_pendiente: int
    count_cancelado: int
    count_total: int


class PaymentsListResponse(BaseModel):
    items: list[PaymentOut]
    summary: PaymentsSummary
    total: int
