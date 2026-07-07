"""
Materials pricing endpoint.

Reads backend/data/materiales-precios.csv from local filesystem (tracked
inside the backend so it ships in the Docker image) and returns
structured pricing data.

CSV columns: categoria, material, unidad, precio_ars, proveedor_ref,
             variacion_mensual_pct, fecha_actualizacion
"""
import csv
from pathlib import Path

from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.base import get_db
from models.material_interest import MaterialInterest
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/materials", tags=["materials"])

# This file lives at backend/api/routes/materials.py
# Backend root is 3 levels up → backend/data/materiales-precios.csv
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_CSV_PATH = _BACKEND_ROOT / "data" / "materiales-precios.csv"


class MaterialItem(BaseModel):
    categoria: str
    material: str
    unidad: str
    precio_ars: int
    proveedor_ref: str
    variacion_mensual_pct: float
    fecha_actualizacion: str


class MaterialsResponse(BaseModel):
    items: list[MaterialItem]
    categories: list[str]
    updated_at: str
    total: int
    # material → cantidad de eventos (search+buy). Ordena el autocompletado
    # "más buscados primero" en el frontend.
    popularity: dict[str, int] = Field(default_factory=dict)


class MaterialInterestRequest(BaseModel):
    material: str = Field(min_length=1, max_length=255)
    action: str = Field(default="search", pattern="^(search|buy)$")


def _load_csv() -> list[dict]:
    if not _CSV_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Archivo de precios no disponible",
        )
    with open(_CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@router.get(
    "",
    response_model=MaterialsResponse,
    summary="Listar precios de materiales de construccion",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de precios no disponible"},
    },
)
async def get_materials(
    categoria: str | None = Query(None, description="Filtrar por categoría"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = _load_csv()

    # Popularidad global (todos los usuarios): eventos de búsqueda + compra.
    try:
        pop_rows = (await db.execute(
            select(MaterialInterest.material, func.count())
            .group_by(MaterialInterest.material))).all()
        popularity = {m: n for m, n in pop_rows}
    except Exception:  # noqa: BLE001 — la popularidad nunca rompe el listado
        popularity = {}

    # Unique categories preserving first-appearance order
    seen: set[str] = set()
    categories: list[str] = []
    for row in rows:
        cat = row.get("categoria", "").strip()
        if cat and cat not in seen:
            seen.add(cat)
            categories.append(cat)

    # Apply filter
    if categoria:
        rows = [r for r in rows if r.get("categoria", "").strip() == categoria]

    # Parse rows into typed items
    items: list[MaterialItem] = []
    for row in rows:
        try:
            items.append(
                MaterialItem(
                    categoria=row["categoria"].strip(),
                    material=row["material"].strip(),
                    unidad=row["unidad"].strip(),
                    precio_ars=int(float(row["precio_ars"])),
                    proveedor_ref=row["proveedor_ref"].strip(),
                    variacion_mensual_pct=float(row["variacion_mensual_pct"]),
                    fecha_actualizacion=row["fecha_actualizacion"].strip(),
                )
            )
        except (KeyError, ValueError):
            continue

    dates = [r.get("fecha_actualizacion", "").strip() for r in rows if r.get("fecha_actualizacion", "").strip()]
    updated_at = max(dates) if dates else ""

    return MaterialsResponse(
        items=items,
        categories=categories,
        updated_at=updated_at,
        total=len(items),
        popularity=popularity,
    )


@router.post(
    "/interest",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Registrar interés en un material (búsqueda o click de compra)",
)
async def record_material_interest(
    body: MaterialInterestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.add(MaterialInterest(user_id=user.id, material=body.material, action=body.action))
    await db.commit()
