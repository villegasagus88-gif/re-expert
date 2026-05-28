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

from api.schemas.academia import CoursesResponse, PathsResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User

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
