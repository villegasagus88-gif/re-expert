"""
Créditos endpoints — asesor hipotecario digital.

Sirve el catálogo curado de créditos (hipotecarios, construcción, desarrollo)
desde `backend/data/creditos/creditos.json`. Mismo patrón que academia/materials:
data curada versionada, leída on-demand con cache en memoria.

El análisis (cuota, compatibilidad, probabilidad, ranking) lo hace el frontend
de forma instantánea con los datos de cada crédito.

Fase 2 (futuro, ya contemplado en el esquema): monitoreo de fuentes oficiales,
detección de cambios con IA, cola de validación humana (pending_review →
approved) e historial. Por eso sólo exponemos items con validation_status
'approved' y status 'active' al público.

Endpoints:
  GET /api/creditos → catálogo de créditos publicables
"""
import json
from functools import lru_cache
from pathlib import Path

from api.schemas.creditos import CreditosResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.user import User

router = APIRouter(prefix="/api/creditos", tags=["creditos"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "creditos"
_CREDITOS_PATH = _DATA_DIR / "creditos.json"


@lru_cache(maxsize=1)
def _load_json(path: str) -> dict:
    """Cache en memoria — el contenido es estático entre redeploys."""
    p = Path(path)
    if not p.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Archivo de créditos no disponible: {p.name}",
        )
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "",
    response_model=CreditosResponse,
    summary="Catálogo de créditos (asesor hipotecario)",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de créditos no disponible"},
    },
)
async def get_creditos(
    audience: str | None = Query(
        None, description="Filtrar por público: comprador | desarrollador | constructor"
    ),
    _user: User = Depends(get_current_user),
) -> CreditosResponse:
    data = _load_json(str(_CREDITOS_PATH))
    items = data.get("items", [])
    # Solo publicamos lo aprobado y activo (Fase 2 usará el resto del pipeline).
    items = [
        it
        for it in items
        if it.get("validation_status", "approved") == "approved"
        and it.get("status", "active") == "active"
    ]
    if audience:
        items = [it for it in items if it.get("audience") == audience]
    return CreditosResponse(
        updated_at=data.get("updated_at", ""),
        disclaimer=data.get("disclaimer", ""),
        relacion_cuota_ingreso_max_default=data.get("relacion_cuota_ingreso_max_default", 25),
        items=items,
    )
