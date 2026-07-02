"""
Schemas para los endpoints de Academia.

Coinciden con la estructura de `backend/data/academia/cursos.json` y
`rutas.json`. Cualquier cambio en los JSON debe reflejarse acá para
que Pydantic los valide al cargar.
"""
from typing import Literal

from pydantic import BaseModel, Field

# ── Cursos ──────────────────────────────────────────────────────────

class Course(BaseModel):
    id: str
    title: str
    level: Literal["beginner", "intermediate", "advanced"]
    icon: str = ""
    icon_color: str = "dev"
    description: str
    provider: str = ""
    duration_hours: int = Field(default=0, ge=0)
    duration_weeks: int = Field(default=0, ge=0)
    price_ars: int = Field(default=0, ge=0)
    price_label: str = ""
    is_free: bool = False
    # Campos ricos del marketplace educativo premium (defaults → tolerante al JSON).
    topic: str = ""
    provider_short: str = ""
    modality: str = "online"            # online | presencial | hibrida
    certificate: bool = True
    start_date: str = ""
    seats: str = ""
    syllabus: list[str] = Field(default_factory=list)
    audience: str = ""
    problem_solved: str = ""
    career_outcome: str = ""
    provider_reputation: str = ""
    badges: list[str] = Field(default_factory=list)
    enroll_url: str = ""
    image_url: str = ""  # foto temática del curso (loremflickr por keywords, estable por ?lock=)


class CourseCategory(BaseModel):
    id: str
    title: str
    courses: list[Course]


class CoursesResponse(BaseModel):
    updated_at: str  # ISO date
    categories: list[CourseCategory]


# ── Rutas de aprendizaje ───────────────────────────────────────────

class PathStep(BaseModel):
    order: int = Field(ge=1)
    title: str
    subtitle: str = ""
    courses: list[str]  # labels visuales, ej. "📊 Lectura de mercado"


class LearningPath(BaseModel):
    id: str
    title: str
    # Catálogo al que pertenece la ruta (las rutas se agrupan por catálogo en la UI).
    category: str = ""
    category_title: str = ""
    steps: list[PathStep]


class PathsResponse(BaseModel):
    updated_at: str
    intro: str = ""
    paths: list[LearningPath]


# ── Medición de demanda (interés en cursos) ────────────────────────

class RecordInterestRequest(BaseModel):
    course_id: str = Field(min_length=1, max_length=80)
    course_title: str = Field(default="", max_length=255)
    topic: str = Field(default="", max_length=40)
    action: Literal["view", "info", "inscribir"] = "view"


# ── Compra de cursos (Checkout Pro) ────────────────────────────────

class CourseCheckoutRequest(BaseModel):
    course_id: str = Field(min_length=1, max_length=80)


class CourseCheckoutResponse(BaseModel):
    # "redirect" → hay que ir a `url` (curso pago); "enrolled" → gratis, ya inscripto.
    kind: Literal["redirect", "enrolled"]
    url: str = ""
    course_id: str
    status: str


class OwnedCourse(BaseModel):
    course_id: str
    course_title: str
    status: str  # approved | free | pending


class MyCoursesResponse(BaseModel):
    items: list[OwnedCourse]


class TopicDemand(BaseModel):
    topic: str
    count: int


class CourseDemand(BaseModel):
    course_id: str
    course_title: str
    total: int
    inscribir: int
    info: int
    view: int


class DemandResponse(BaseModel):
    total_events: int
    by_topic: list[TopicDemand]
    by_course: list[CourseDemand]
