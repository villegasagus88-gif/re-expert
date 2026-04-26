"""
Schemas para POST /api/data/ingest.

El frontend (típicamente SOL) envía un objeto con un campo `type` que
discrimina la forma del payload. Cada tipo se valida con su propio modelo
Pydantic y termina en una tabla diferente.
"""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# -------------------------------------------------------------------- common --

# Las secciones que SOL anuncia en el JSON fence se mapean 1:1 con estos `type`.
IngestType = Literal["payment", "milestone", "material", "budget"]


# ------------------------------------------------------------------ payment --
class PaymentIngest(BaseModel):
    type: Literal["payment"] = "payment"
    amount: Decimal = Field(..., gt=0, max_digits=14, decimal_places=2)
    currency: str = Field("ARS", min_length=2, max_length=8)
    provider: str | None = Field(None, max_length=200)
    concept: str | None = Field(None, max_length=500)
    paid_at: date | None = None
    notes: str | None = Field(None, max_length=2000)


# ---------------------------------------------------------------- milestone --
MilestoneStatus = Literal["planned", "in_progress", "done", "delayed"]


class MilestoneIngest(BaseModel):
    type: Literal["milestone"] = "milestone"
    name: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(None, max_length=2000)
    status: MilestoneStatus = "planned"
    due_date: date | None = None
    completed_at: date | None = None


# ----------------------------------------------------------------- material --
class MaterialIngest(BaseModel):
    type: Literal["material"] = "material"
    name: str = Field(..., min_length=1, max_length=300)
    unit: str = Field(..., min_length=1, max_length=32)
    unit_price: Decimal = Field(..., gt=0, max_digits=14, decimal_places=2)
    currency: str = Field("ARS", min_length=2, max_length=8)
    supplier: str | None = Field(None, max_length=200)
    quoted_at: date | None = None
    notes: str | None = Field(None, max_length=2000)


# ------------------------------------------------------------------- budget --
BudgetKind = Literal["planned", "extra", "actual"]


class BudgetIngest(BaseModel):
    type: Literal["budget"] = "budget"
    category: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=0, max_digits=14, decimal_places=2)
    currency: str = Field("ARS", min_length=2, max_length=8)
    kind: BudgetKind = "planned"
    notes: str | None = Field(None, max_length=2000)


# ------------------------------------------------------------ discriminated --
# Pydantic v2 discriminated union: valida el campo `type` y rutea al modelo
# correspondiente, devolviendo errores 422 claros si falta o no matchea.
IngestRequest = Annotated[
    PaymentIngest | MilestoneIngest | MaterialIngest | BudgetIngest,
    Field(discriminator="type"),
]


# ------------------------------------------------------------------ response --
class IngestResponse(BaseModel):
    """Confirmación devuelta tras persistir el dato."""

    id: UUID
    type: IngestType
    message: str
