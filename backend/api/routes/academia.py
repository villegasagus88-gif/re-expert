"""
Academia endpoints.

Sirve cursos y rutas de aprendizaje desde JSONs en `backend/data/academia/`.
Mismo patrón que `materials.py`: data curada (low-churn) en archivos
versionados, leídos on-demand con cache en memoria.

Endpoints:
  GET /api/academia/courses → catálogo de cursos agrupados por categoría
  GET /api/academia/paths   → rutas de aprendizaje (caminos progresivos)
"""
import json
from functools import lru_cache
from pathlib import Path

from api.schemas.academia import (
    CourseDemand,
    CoursesResponse,
    DemandResponse,
    PathsResponse,
    RecordInterestRequest,
    TopicDemand,
)
from core.auth import get_current_user, require_admin
from fastapi import APIRouter, Depends, HTTPException, status
from models.academia import AcademiaInterest
from models.base import get_db
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/academia", tags=["academia"])

# Misma estructura que materials.py: el data vive dentro del backend
# para que viaje con el Docker image. Si en el futuro queremos editar
# sin redeploy, migrar al bucket de Supabase Storage.
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "academia"
_COURSES_PATH = _DATA_DIR / "cursos.json"
_PATHS_PATH = _DATA_DIR / "rutas.json"


@lru_cache(maxsize=2)
def _load_json(path: str) -> dict:
    """Cache en memoria — el contenido es estático, no cambia entre requests."""
    p = Path(path)
    if not p.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Archivo de academia no disponible: {p.name}",
        )
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/courses",
    response_model=CoursesResponse,
    summary="Catálogo de cursos curados",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de cursos no disponible"},
    },
)
async def get_courses(_user: User = Depends(get_current_user)) -> CoursesResponse:
    data = _load_json(str(_COURSES_PATH))
    return CoursesResponse(**data)


@router.get(
    "/paths",
    response_model=PathsResponse,
    summary="Rutas de aprendizaje progresivas",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de rutas no disponible"},
    },
)
async def get_paths(_user: User = Depends(get_current_user)) -> PathsResponse:
    data = _load_json(str(_PATHS_PATH))
    return PathsResponse(**data)


# ── Medición de demanda ──

@router.post(
    "/interest",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registrar interés en un curso (abrir detalle / solicitar info / inscribirse)",
)
async def record_interest(
    body: RecordInterestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.add(AcademiaInterest(
        user_id=user.id, course_id=body.course_id, course_title=body.course_title,
        topic=body.topic, action=body.action,
    ))
    await db.commit()


@router.get(
    "/demand",
    response_model=DemandResponse,
    summary="Demanda agregada por tema y curso (solo admin)",
    responses={403: {"description": "Requiere admin"}},
)
async def get_demand(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DemandResponse:
    rows = list((await db.execute(select(AcademiaInterest))).scalars().all())

    topic_counts: dict[str, int] = {}
    course_agg: dict[str, dict] = {}
    for r in rows:
        topic = r.topic or "sin_tema"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        c = course_agg.setdefault(
            r.course_id,
            {"course_title": r.course_title or r.course_id, "total": 0, "inscribir": 0, "info": 0, "view": 0},
        )
        c["total"] += 1
        if r.action in ("inscribir", "info", "view"):
            c[r.action] += 1
        if r.course_title:
            c["course_title"] = r.course_title

    by_topic = [TopicDemand(topic=t, count=n) for t, n in
                sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)]
    by_course = [CourseDemand(course_id=cid, **agg) for cid, agg in
                 sorted(course_agg.items(), key=lambda x: x[1]["total"], reverse=True)]
    return DemandResponse(total_events=len(rows), by_topic=by_topic, by_course=by_course)
