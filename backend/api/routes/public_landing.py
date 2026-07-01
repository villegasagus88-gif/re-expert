"""
Datos públicos para la landing (sin auth).

La landing (index.html) muestra "Cotización de Materiales" y "Noticias" con la
MISMA información que usa la app, para que se vea viva y al momento. Como la
landing es pública no puede pegarle a /api/materials ni /api/news (requieren
auth + plan), así que este endpoint expone una MUESTRA read-only y cacheada:

  GET /api/public/landing → { materials: {items[≤6], updated_at},
                              news: {items[≤6]} }

Diseño:
  - Sin auth y sin datos de usuario: solo contenido ya público en la app
    (precios del CSV de materiales + titulares del feed de noticias).
  - Cache in-process con TTL 10 min → barato y resistente a abuso; el feed
    de noticias además tiene su propio cache interno (news_live).
  - Best-effort: si una fuente falla devuelve items vacíos, nunca 500 — la
    landing conserva su contenido estático de diseño.
"""
import logging
import time

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public"])

_TTL_SECONDS = 600  # 10 min
_cache: dict = {"ts": 0.0, "data": None}

_MAX_ITEMS = 6


def _materials_sample() -> dict:
    """Muestra de precios (top movimientos) del mismo CSV que /api/materials."""
    try:
        from api.routes.materials import _load_csv
        rows = _load_csv()
    except Exception:  # noqa: BLE001 — best-effort: la landing tiene fallback estático
        logger.exception("public_landing: materiales no disponibles")
        return {"items": [], "updated_at": ""}

    def _abs_var(r: dict) -> float:
        try:
            return abs(float(r.get("variacion_mensual_pct") or 0))
        except (TypeError, ValueError):
            return 0.0

    rows = sorted(rows, key=_abs_var, reverse=True)
    items = []
    for r in rows:
        if len(items) >= _MAX_ITEMS:
            break
        try:
            items.append({
                "material": str(r["material"])[:120],
                "categoria": str(r.get("categoria", ""))[:60],
                "unidad": str(r.get("unidad", ""))[:40],
                "precio_ars": int(float(r["precio_ars"])),
                "proveedor_ref": str(r.get("proveedor_ref", ""))[:80],
                "variacion_mensual_pct": float(r.get("variacion_mensual_pct") or 0),
            })
        except (KeyError, TypeError, ValueError):
            continue
    updated = max((str(r.get("fecha_actualizacion", "")) for r in rows), default="")
    return {"items": items, "updated_at": updated}


async def _news_sample() -> dict:
    """Últimos titulares del feed en vivo (cacheado en news_live); solo campos
    públicos de cada nota. Si el feed falla → lista vacía (la landing no rompe)."""
    try:
        from services.news_live import fetch_feed
        feed = await fetch_feed(category="todas", page=1, per_page=_MAX_ITEMS, refresh=False)
        items = []
        for it in (feed.get("items") or [])[:_MAX_ITEMS]:
            items.append({
                "title": str(it.get("title") or "")[:200],
                "snippet": str(it.get("snippet") or "")[:280],
                "source": str(it.get("source") or "")[:80],
                "category": str(it.get("category") or "")[:24],
                "published": str(it.get("published") or it.get("date") or "")[:40],
                "url": str(it.get("url") or "")[:600],
            })
        return {"items": items}
    except Exception:  # noqa: BLE001 — best-effort
        logger.exception("public_landing: feed de noticias no disponible")
        return {"items": []}


@router.get(
    "/landing",
    summary="Datos públicos para la landing: cotización de materiales + noticias",
)
async def get_landing_data() -> dict:
    now = time.monotonic()
    if _cache["data"] is not None and (now - _cache["ts"]) < _TTL_SECONDS:
        return _cache["data"]
    data = {
        "materials": _materials_sample(),
        "news": await _news_sample(),
    }
    # Cachear solo respuestas con algo de contenido: un arranque en frío con
    # ambas fuentes caídas no debe quedar clavado 10 minutos.
    if data["materials"]["items"] or data["news"]["items"]:
        _cache["ts"] = now
        _cache["data"] = data
    return data
