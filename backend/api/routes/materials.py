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

from core.auth import get_current_user, require_admin
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.base import get_db
from models.material_interest import MaterialInterest
from models.material_price import MaterialPriceOverride
from models.user import User
from pydantic import BaseModel, Field
from services.material_prices import maybe_refresh_prices
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
    live: bool = False       # True si el precio viene del actualizador automático
    fuente: str = ""


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

    # Overrides de precios vivos (actualizador automático)
    try:
        ov_rows = list((await db.execute(select(MaterialPriceOverride))).scalars().all())
        overrides = {o.material: o for o in ov_rows}
        last_live = max((o.updated_at for o in ov_rows), default=None)
    except Exception:  # noqa: BLE001
        overrides, last_live = {}, None

    # Parse rows into typed items (override pisa al CSV)
    items: list[MaterialItem] = []
    for row in rows:
        try:
            name = row["material"].strip()
            ov = overrides.get(name)
            items.append(
                MaterialItem(
                    categoria=row["categoria"].strip(),
                    material=name,
                    unidad=row["unidad"].strip(),
                    precio_ars=ov.precio_ars if ov else int(float(row["precio_ars"])),
                    proveedor_ref=row["proveedor_ref"].strip(),
                    variacion_mensual_pct=ov.variacion_mensual_pct if ov else float(row["variacion_mensual_pct"]),
                    fecha_actualizacion=ov.updated_at.date().isoformat() if ov else row["fecha_actualizacion"].strip(),
                    live=bool(ov),
                    fuente=(ov.fuente if ov else ""),
                )
            )
        except (KeyError, ValueError):
            continue

    dates = [i.fecha_actualizacion for i in items if i.fecha_actualizacion]
    updated_at = max(dates) if dates else ""

    # "Cada vez que el usuario entra": si la data vieja, refresh en background.
    maybe_refresh_prices({i.material: i.precio_ars for i in items}, last_live)

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


@router.get(
    "/demand",
    summary="Materiales más buscados y comprados (solo admin)",
    responses={403: {"description": "Requiere admin"}},
)
async def materials_demand(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    rows = (await db.execute(
        select(MaterialInterest.material, MaterialInterest.action, func.count())
        .group_by(MaterialInterest.material, MaterialInterest.action))).all()
    agg: dict[str, dict] = {}
    for material, action, n in rows:
        item = agg.setdefault(material, {"material": material, "search": 0, "buy": 0, "total": 0})
        if action in ("search", "buy"):
            item[action] += n
        item["total"] += n
    items = sorted(agg.values(), key=lambda x: x["total"], reverse=True)
    return {"items": items, "total_events": sum(i["total"] for i in items)}
