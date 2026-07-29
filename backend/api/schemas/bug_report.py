"""
Schemas de reportes de error (Ayuda → Informar un error).

Dos vistas separadas a propósito:
  - `BugReportOut`   → lo que ve el USUARIO (sin admin_note ni datos de otros).
  - `BugReportAdminOut` → lo que ve el ADMIN (suma reporter_email, contexto
    técnico y la nota interna).
"""
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field


# El strip va ANTES de medir la longitud: sin esto, un título de 3 espacios o una
# descripción de 10 espacios pasaban min_length y se guardaban vacíos (la ruta
# hace .strip() recién al construir el modelo).
def _stripped(v: Any) -> Any:
    return v.strip() if isinstance(v, str) else v


Trimmed = Annotated[str, BeforeValidator(_stripped)]
TrimmedOpt = Annotated[str | None, BeforeValidator(_stripped)]

BugStatus = Literal["new", "in_review", "resolved", "dismissed"]
BugSeverity = Literal["low", "normal", "high"]


class CreateBugReportRequest(BaseModel):
    title: Trimmed = Field(min_length=3, max_length=200)
    description: Trimmed = Field(min_length=10, max_length=5000)
    section: TrimmedOpt = Field(default=None, max_length=60)
    notes: TrimmedOpt = Field(default=None, max_length=2000)
    severity: BugSeverity = "normal"
    # Contexto técnico que arma el frontend (user agent, viewport, url…).
    # Se acota server-side en la ruta: es input del cliente, no confiamos en el tamaño.
    context: dict[str, Any] = Field(default_factory=dict)


class BugReportOut(BaseModel):
    """Vista del usuario: su propio reporte, sin nada interno."""
    id: UUID
    ticket: int
    title: str
    description: str
    section: str | None
    notes: str | None
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BugReportsResponse(BaseModel):
    items: list[BugReportOut]
    total: int


class BugReportAdminOut(BugReportOut):
    """Vista del admin: suma quién lo mandó, el contexto y la nota interna."""
    user_id: UUID | None
    reporter_email: str | None
    admin_note: str | None
    context: dict[str, Any]
    attachments_count: int


class BugReportsAdminResponse(BaseModel):
    items: list[BugReportAdminOut]
    total: int
    # Contadores por estado para la bandeja (no re-consulta por cada filtro).
    counts: dict[str, int]


class UpdateBugReportRequest(BaseModel):
    """PATCH del admin: cambiar estado y/o dejar nota interna."""
    status: BugStatus | None = None
    admin_note: str | None = Field(default=None, max_length=4000)


class NewBugsCount(BaseModel):
    """Badge del panel: cuántos reportes están sin abrir."""
    new: int
