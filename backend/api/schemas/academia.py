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
    duration_hours: int = Field(ge=0)
    duration_weeks: int = Field(ge=0)
    price_ars: int = Field(ge=0)
    price_label: str = ""
    is_free: bool = False


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
    steps: list[PathStep]


class PathsResponse(BaseModel):
    updated_at: str
    intro: str = ""
    paths: list[LearningPath]
