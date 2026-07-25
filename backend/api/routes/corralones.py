"""
Corralones cerca del usuario — endpoints de la sección Materiales & Corralones.

  GET  /api/corralones/categorias → rubros para construir de inicio a fin
  POST /api/corralones/geo        → {lat,lon} → zona legible (reverse geocode)
  GET  /api/corralones/buscar     → ?zona=&categoria= | &material= → comercios
"""
import logging

from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from models.base import get_db
from models.user import User
from pydantic import BaseModel, Field
from services import corralones
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/corralones", tags=["corralones"])


class GeoRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


@router.get("/categorias", summary="Rubros de compra para construir de inicio a fin")
async def categorias(_user: User = Depends(get_current_user)):
    return {"categorias": corralones.CATEGORIAS}


@router.post("/geo", summary="Coordenadas del usuario → zona legible")
async def geo(body: GeoRequest, _user: User = Depends(get_current_user)):
    try:
        return await corralones.reverse_geocode(body.lat, body.lon)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Corralones: geo falló")
        raise HTTPException(status_code=502, detail="No se pudo resolver la ubicación") from exc


@router.get("/buscar", summary="Corralones de la zona por rubro o material")
async def buscar(
    zona: str = Query(min_length=2, max_length=120),
    categoria: str | None = Query(default=None, max_length=30),
    material: str | None = Query(default=None, min_length=2, max_length=80),
    force: bool = Query(default=False),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if categoria and not corralones.categoria_valida(categoria):
        raise HTTPException(status_code=422, detail="Rubro desconocido")
    if not categoria and not material:
        categoria = corralones.CATEGORIAS[0]["id"]
    try:
        return await corralones.buscar(db, zona, categoria=categoria,
                                       material=material, force=force)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Corralones: buscar falló")
        raise HTTPException(status_code=502, detail="La búsqueda de corralones falló") from exc
