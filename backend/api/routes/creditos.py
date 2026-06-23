"""
Créditos endpoints — asesor hipotecario digital.

Sirve el catálogo curado de créditos (hipotecarios, construcción, desarrollo).

Fase 2: el catálogo vive en la DB (`credits`), sembrado desde
`data/creditos/creditos.json` la primera vez. Sólo se exponen items con
validation_status 'approved' y status 'active'; el resto del pipeline
(propuestas + validación humana + historial) vive en los endpoints admin.

El análisis (cuota, compatibilidad, probabilidad, ranking) lo hace el frontend
de forma instantánea con los datos de cada crédito.

Endpoints:
  GET /api/creditos → catálogo de créditos publicables
"""
from api.schemas.creditos import CreditosResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, Query
from models import get_db
from models.user import User
from services import creditos_repo
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/creditos", tags=["creditos"])


@router.get(
    "",
    response_model=CreditosResponse,
    summary="Catálogo de créditos (asesor hipotecario)",
    responses={
        401: {"description": "Token inválido o ausente"},
    },
)
async def get_creditos(
    audience: str | None = Query(
        None, description="Filtrar por público: comprador | desarrollador | constructor"
    ),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreditosResponse:
    items = await creditos_repo.list_public(db, audience)
    m = creditos_repo.meta()
    return CreditosResponse(
        updated_at=m["updated_at"],
        disclaimer=m["disclaimer"],
        relacion_cuota_ingreso_max_default=m["relacion_cuota_ingreso_max_default"],
        items=items,
    )
