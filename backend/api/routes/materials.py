"""
Materials pricing endpoint.

Reads knowledge/materiales-precios.csv from local filesystem (tracked in
the repo alongside the backend) and returns structured pricing data.

CSV columns: categoria, material, unidad, precio_ars, proveedor_ref,
             variacion_mensual_pct, fecha_actualizacion
"""
import csv
from pathlib import Path

from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/materials", tags=["materials"])

# This file lives at backend/api/routes/materials.py
# Project root is 4 levels up → knowledge/materiales-precios.csv
_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge"
_CSV_PATH = _KNOWLEDGE_DIR / "materiales-precios.csv"


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
    _user: User = Depends(get_current_user),
):
    rows = _load_csv()

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
    )
