"""
Schemas del sistema de Análisis de Planos.

Solo requests: las responses se arman a mano en la ruta (dicts) para nunca
serializar por accidente el BYTEA de plan_files.file_data.
"""
from typing import Literal

from pydantic import BaseModel, Field

OBRA_TYPES = Literal[
    "vivienda_unifamiliar", "vivienda_multifamiliar", "edificio", "local_comercial",
    "desarrollo_inmobiliario", "obra_industrial", "reforma", "otro",
]
STAGES = Literal[
    "idea", "anteproyecto", "ejecutivo", "aprobacion", "presupuesto", "obra", "revision_final",
]
GOALS = Literal[
    "entender", "detectar_errores", "constructibilidad", "comparar_versiones",
    "reunion_tecnica", "presupuestar", "iniciar_obra",
]
ANALYSIS_MODES = Literal["simple", "errores", "desarrollador", "constructor"]
PROFILES = Literal["", "no_tecnico", "constructor", "desarrollador", "jefe_obra", "arquitecto"]
PRIORITIES = Literal["critica", "alta", "media", "baja", "informativa"]
ALERT_STATUSES = Literal["pendiente", "en_revision", "validado", "rechazado", "resuelto", "ignorado"]
TASK_STATUSES = Literal["pendiente", "en_curso", "en_revision", "resuelta", "cancelada"]
CHECK_STATUSES = Literal["pendiente", "en_revision", "validado", "no_aplica", "resuelto"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    obra_type: OBRA_TYPES = "otro"
    location: str = Field(default="", max_length=255)
    estimated_area: str = Field(default="", max_length=60)
    stage: STAGES = "anteproyecto"
    analysis_goal: GOALS = "entender"
    client_name: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=4000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    obra_type: OBRA_TYPES | None = None
    location: str | None = Field(default=None, max_length=255)
    estimated_area: str | None = Field(default=None, max_length=60)
    stage: STAGES | None = None
    analysis_goal: GOALS | None = None
    client_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class PlanUpdate(BaseModel):
    """Edición manual de la clasificación / metadatos del plano."""
    detected_plan_type: str | None = Field(default=None, max_length=60)
    discipline: str | None = Field(default=None, max_length=40)
    sheet_number: str | None = Field(default=None, max_length=60)
    scale: str | None = Field(default=None, max_length=40)
    plan_date: str | None = Field(default=None, max_length=40)
    floor_level: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=30)
    version_notes: str | None = Field(default=None, max_length=2000)


class AnalyzeRequest(BaseModel):
    mode: ANALYSIS_MODES = "errores"
    profile: PROFILES = ""


class CompareRequest(BaseModel):
    plan_a: str = Field(min_length=1)   # UUID como string
    plan_b: str = Field(min_length=1)
    focus: str = Field(default="", max_length=500)


class AlertUpdate(BaseModel):
    status: ALERT_STATUSES | None = None
    priority: PRIORITIES | None = None
    responsible: str | None = Field(default=None, max_length=120)
    due_date: str | None = Field(default=None, max_length=20)
    pin_x: float | None = Field(default=None, ge=0, le=100)
    pin_y: float | None = Field(default=None, ge=0, le=100)
    pin_page: int | None = Field(default=None, ge=1)
    clear_pin: bool = False


class AlertCreate(BaseModel):
    """Observación manual (pin colocado a mano sobre el plano)."""
    analysis_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    category: str = Field(default="manual", max_length=60)
    location: str = Field(default="", max_length=255)
    recommendation: str = Field(default="", max_length=2000)
    priority: PRIORITIES = "media"
    pin_x: float | None = Field(default=None, ge=0, le=100)
    pin_y: float | None = Field(default=None, ge=0, le=100)
    pin_page: int = Field(default=1, ge=1)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    plan_id: str | None = None
    alert_id: str | None = None
    priority: PRIORITIES = "media"
    responsible: str = Field(default="", max_length=120)
    due_date: str = Field(default="", max_length=20)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    priority: PRIORITIES | None = None
    responsible: str | None = Field(default=None, max_length=120)
    status: TASK_STATUSES | None = None
    due_date: str | None = Field(default=None, max_length=20)
    comments: str | None = Field(default=None, max_length=4000)


class ChecklistItemUpdate(BaseModel):
    index: int = Field(ge=0)
    status: CHECK_STATUSES
    comment: str = Field(default="", max_length=1000)
