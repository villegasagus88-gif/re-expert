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
import asyncio
import logging
from datetime import UTC, datetime

from api.schemas.creditos import CreditosResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, Query
from models import get_db, get_session_factory
from models.user import User
from services import creditos_repo
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/creditos", tags=["creditos"])

# Refresco diario (por proceso): "YYYY-MM-DD" del último disparo.
_last_refresh_date: str | None = None


async def _run_daily_refresh() -> None:
    """Corre el monitor IA en background y deja propuestas en la cola para
    aprobar. Best-effort: cualquier error se loguea y NO afecta al usuario
    (no publica nada solo; el gate humano sigue intacto)."""
    from services.creditos_monitor import run_monitor
    try:
        async with get_session_factory()() as db:
            await creditos_repo.seed_if_empty(db)
            summary = await run_monitor(db)
        logger.info("Refresco diario de créditos: %s", summary)
    except Exception:  # noqa: BLE001
        logger.exception("Refresco diario de créditos falló")


def _schedule_daily_refresh() -> None:
    """Dispara el refresco a lo sumo una vez por día, sin bloquear el request."""
    global _last_refresh_date
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    if _last_refresh_date == today:
        return
    _last_refresh_date = today  # marcar ANTES de crear la task evita duplicados
    try:
        asyncio.create_task(_run_daily_refresh())
    except RuntimeError:
        _last_refresh_date = None  # sin loop activo: reintentar en el próximo request


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
    _schedule_daily_refresh()  # refresco diario con IA → propuestas (no bloquea)
    m = creditos_repo.meta()
    return CreditosResponse(
        updated_at=m["updated_at"],
        disclaimer=m["disclaimer"],
        relacion_cuota_ingreso_max_default=m["relacion_cuota_ingreso_max_default"],
        items=items,
    )
