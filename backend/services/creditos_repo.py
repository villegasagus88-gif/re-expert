"""
Repositorio de Créditos — Fase 2.

Centraliza el acceso a la tabla `credits`:
  - seed_if_empty: siembra el catálogo desde data/creditos/creditos.json la
    primera vez (idempotente: solo si la tabla está vacía).
  - list_public: lo publicable (approved + active), con filtro por público.
  - meta(): constantes de catálogo (disclaimer, ratio default) desde el JSON.

La fuente de verdad pasa a ser la DB; el JSON queda como semilla + config.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from models.credit import Credit, CreditChangeLog
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "creditos"
_CREDITOS_PATH = _DATA_DIR / "creditos.json"

# Columnas escalares/JSON que sembramos desde el JSON (whitelist defensiva:
# ignora claves extra del JSON como change_history, que no es columna).
_SEED_FIELDS: tuple[str, ...] = (
    "country", "province", "bank_name", "bank_emoji", "credit_name",
    "audience", "credit_type", "rate_type", "interest_rate_tna",
    "interest_rate_note", "max_term_years", "max_financing_percent",
    "min_income_ars", "min_employment_seniority_months", "max_age",
    "property_value_limit_ars", "relacion_cuota_ingreso_max",
    "required_savings_note", "requirements", "documents", "pros", "cons",
    "extra_costs", "official_url", "source_urls", "last_checked_at",
    "last_updated_at", "validation_status", "status",
)


@lru_cache(maxsize=1)
def _load_seed_json() -> dict:
    if not _CREDITOS_PATH.exists():
        logger.warning("creditos.json no encontrado en %s", _CREDITOS_PATH)
        return {}
    with open(_CREDITOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def meta() -> dict:
    """Constantes de catálogo (no per-crédito) desde el JSON semilla."""
    data = _load_seed_json()
    return {
        "updated_at": data.get("updated_at", ""),
        "disclaimer": data.get("disclaimer", ""),
        "relacion_cuota_ingreso_max_default": data.get(
            "relacion_cuota_ingreso_max_default", 25
        ),
    }


def item_to_kwargs(item: dict) -> dict:
    """Mapea un dict-item (JSON o payload de propuesta) a kwargs de Credit."""
    kw: dict[str, Any] = {"id": item["id"]}
    for f in _SEED_FIELDS:
        if f in item and item[f] is not None:
            kw[f] = item[f]
    return kw


async def seed_if_empty(db: AsyncSession) -> int:
    """Si la tabla está vacía, siembra desde el JSON. Devuelve filas insertadas."""
    count = await db.scalar(select(func.count()).select_from(Credit))
    if count and count > 0:
        return 0
    data = _load_seed_json()
    items = data.get("items", []) if isinstance(data, dict) else []
    inserted = 0
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        db.add(Credit(**item_to_kwargs(item)))
        db.add(
            CreditChangeLog(
                credit_id=item["id"],
                field="*",
                old_value=None,
                new_value="(seed inicial)",
                source="data/creditos/creditos.json",
                change_type="seed",
            )
        )
        inserted += 1
    if inserted:
        try:
            await db.commit()
        except IntegrityError:
            # Otro worker sembró primero (carrera en el primer request post-deploy).
            await db.rollback()
            logger.info("Seed de créditos: otro proceso sembró primero; rollback.")
            return 0
        logger.info("Créditos sembrados desde JSON: %d", inserted)
    return inserted


async def list_public(db: AsyncSession, audience: str | None = None) -> list[dict]:
    """Items publicables (approved + active), opcionalmente por público."""
    await seed_if_empty(db)
    stmt = (
        select(Credit)
        .where(Credit.validation_status == "approved", Credit.status == "active")
        .order_by(Credit.audience, Credit.interest_rate_tna.is_(None), Credit.interest_rate_tna)
    )
    if audience:
        stmt = stmt.where(Credit.audience == audience)
    rows = (await db.scalars(stmt)).all()
    return [c.to_item_dict() for c in rows]
