"""
Cotización del dólar (blue + oficial) desde dolarapi.com, cacheada.

La usa la calculadora hipotecaria del frontend para prefill de la conversión
USD→ARS (antes hardcodeada en 1460, quedaba vieja). El usuario elige con qué
dólar trabajar (blue u oficial).

Cache in-memory con TTL corto: el dólar no cambia intra-hora y no queremos
pegarle al API externo en cada request. Best-effort: si el fetch falla y hay
cache, devuelve el último valor marcado `stale`; si no hay nada, rates vacíos.
El fetch sale por core.safe_get (guard anti-SSRF).
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from core.safe_fetch import safe_get

logger = logging.getLogger(__name__)

_DOLAR_API = "https://dolarapi.com/v1/dolares"
_TTL_SECONDS = 600  # 10 min
_CASAS = ("blue", "oficial")

_cache: dict[str, Any] | None = None
_cache_at: datetime | None = None


async def get_dolar_rates() -> dict[str, Any]:
    """Devuelve {"rates": {"blue": {compra, venta, nombre}, "oficial": {...}},
    "updated_at": iso|None, "stale": bool}. Cacheado por _TTL_SECONDS."""
    global _cache, _cache_at
    now = datetime.now(UTC)
    if (
        _cache is not None
        and _cache_at is not None
        and (now - _cache_at).total_seconds() < _TTL_SECONDS
    ):
        return _cache
    try:
        resp = await safe_get(_DOLAR_API, timeout=8.0)
        if resp.status_code >= 300:
            raise ValueError(f"dolarapi status {resp.status_code}")
        data = resp.json()
        rates: dict[str, Any] = {}
        for row in data or []:
            casa = (row.get("casa") or "").lower()
            if casa in _CASAS:
                rates[casa] = {
                    "compra": row.get("compra"),
                    "venta": row.get("venta"),
                    "nombre": row.get("nombre") or casa.capitalize(),
                }
        if not rates:
            raise ValueError("respuesta sin casas blue/oficial")
        _cache = {"rates": rates, "updated_at": now.isoformat(), "stale": False}
        _cache_at = now
        return _cache
    except Exception as e:  # noqa: BLE001 — nunca romper la calculadora por el dólar
        logger.warning("dolar_service: fetch falló (%s); devuelvo cache/stub", e)
        if _cache is not None:
            return {**_cache, "stale": True}
        return {"rates": {}, "updated_at": None, "stale": True}
