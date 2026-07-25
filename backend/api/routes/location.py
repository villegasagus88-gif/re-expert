"""
Location endpoints — capacidad de geolocalización de plataforma.

  GET    /api/location/consent      → estado de consentimiento del usuario
  PUT    /api/location/consent      → otorgar/negar + precisión (exact|coarse)
  POST   /api/location/fix          → reportar un fix (requiere consent granted)
  GET    /api/location/me           → última ubicación conocida
  GET    /api/location/history      → historial paginado (máx 200 por página)
  DELETE /api/location/me           → purga total de fixes (self-service)

Seguridad:
  - Todo scoped al usuario autenticado; no existen endpoints cross-user.
  - Consent-first: POST /fix devuelve 403 hasta que el usuario otorgue.
  - Rate limits en escrituras (el watch del frontend ya throttlea, esto es
    la barrera server-side).
  - Las coordenadas nunca se loguean (ver también __repr__ del modelo).
"""
from datetime import datetime

from api.schemas.location import (
    ConsentOut,
    ConsentUpdateRequest,
    LatestLocationOut,
    LocationFixOut,
    LocationFixRequest,
    LocationHistoryResponse,
    PurgeResponse,
)
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from models.base import get_db
from models.user import User
from models.user_location import UserLocation
from services import location_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/location", tags=["location"])


def _fix_out(f: UserLocation) -> LocationFixOut:
    return LocationFixOut(
        id=f.id,
        lat=f.lat,
        lon=f.lon,
        accuracy_m=f.accuracy_m,
        source=f.source,
        geohash=f.geohash,
        captured_at=f.captured_at,
        created_at=f.created_at,
    )


@router.get("/consent", response_model=ConsentOut)
async def get_consent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await location_service.get_settings(db, current_user.id)
    if row is None:
        return ConsentOut(consent="unset", precision="exact", consent_updated_at=None)
    return ConsentOut(
        consent=row.consent,  # type: ignore[arg-type]
        precision=row.precision,  # type: ignore[arg-type]
        consent_updated_at=row.consent_updated_at,
    )


@router.put("/consent", response_model=ConsentOut)
@limiter.limit("30/minute")
async def update_consent(
    request: Request,
    body: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await location_service.set_consent(
        db, current_user.id, consent=body.consent, precision=body.precision
    )
    return ConsentOut(
        consent=row.consent,  # type: ignore[arg-type]
        precision=row.precision,  # type: ignore[arg-type]
        consent_updated_at=row.consent_updated_at,
    )


@router.post(
    "/fix",
    response_model=LocationFixOut,
    status_code=201,
    responses={
        403: {"description": "Consentimiento de ubicación no otorgado"},
        422: {"description": "Coordenadas inválidas"},
    },
)
@limiter.limit("12/minute")
async def report_fix(
    request: Request,
    body: LocationFixRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        fix = await location_service.record_fix(
            db,
            current_user.id,
            lat=body.lat,
            lon=body.lon,
            accuracy_m=body.accuracy_m,
            altitude_m=body.altitude_m,
            heading_deg=body.heading_deg,
            speed_mps=body.speed_mps,
            source=body.source,
            captured_at=body.captured_at,
        )
    except location_service.ConsentRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Tenés que habilitar compartir ubicación primero.",
                "consent_endpoint": "/api/location/consent",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _fix_out(fix)


@router.get("/me", response_model=LatestLocationOut)
async def get_my_location(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fix = await location_service.get_latest(db, current_user.id)
    if fix is None:
        return LatestLocationOut(found=False, fix=None)
    return LatestLocationOut(found=True, fix=_fix_out(fix))


@router.get("/history", response_model=LocationHistoryResponse)
async def get_my_history(
    limit: int = Query(50, ge=1, le=200),
    before: datetime | None = Query(
        None, description="Devolver fixes anteriores a este timestamp (paginación)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await location_service.get_history(
        db, current_user.id, limit=limit, before=before
    )
    return LocationHistoryResponse(items=[_fix_out(f) for f in rows], total=len(rows))


@router.delete("/me", response_model=PurgeResponse)
@limiter.limit("5/hour")
async def purge_my_locations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await location_service.purge(db, current_user.id)
    return PurgeResponse(deleted=deleted)
