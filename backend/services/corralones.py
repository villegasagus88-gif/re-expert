"""
Corralones cerca de la obra — el reemplazo del "cotizador de materiales".

El que construye no compra en marketplaces: compra en corralones cerca del
proyecto para evitar fletes. Esta capa arma, por zona del usuario:
  - reverse geocoding de su ubicación (Nominatim/OSM, sin API key),
  - los comercios por rubro (áridos por un lado, hierro por otro…) vía
    búsqueda web (Tavily) estructurada por el modelo rápido de Anthropic,
  - comparación de precios publicados cuando existen.

Todo con caché por zona en DB (los corralones de una zona no cambian a
diario) para que la sección abra al instante y no gastar búsquedas.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import unicodedata
from datetime import UTC, datetime, timedelta

import httpx
from config.settings import settings
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
_TAVILY = "https://api.tavily.com/search"
_UA = {"User-Agent": "RE-Expert/1.0 (plataforma real estate AR; contacto@re-expert.app)"}

# TTL del caché: los corralones de una zona son estables; los precios menos.
_TTL_CATEGORIA = timedelta(days=7)
_TTL_MATERIAL = timedelta(days=2)

# Rubros necesarios para construir de inicio a fin: no se compra todo en el
# mismo corralón — áridos por un lado, hierro por otro, y así.
CATEGORIAS = [
    {"id": "corralon", "label": "Corralón general", "icon": "🧱",
     "desc": "Cemento, cal, ladrillos, bloques",
     "q": '"corralón de materiales" OR "venta de materiales de construcción"'},
    {"id": "aridos", "label": "Áridos y hormigón", "icon": "⛰️",
     "desc": "Arena, piedra, tosca, hormigón elaborado",
     "q": 'venta de áridos OR "hormigón elaborado" OR arenera'},
    {"id": "hierros", "label": "Hierros y aceros", "icon": "🏗️",
     "desc": "Hierro para construcción, mallas, perfiles",
     "q": '"hierros para la construcción" OR "aceros" distribuidor'},
    {"id": "maderas", "label": "Maderas", "icon": "🪵",
     "desc": "Maderera: tirantes, fenólicos, machimbre",
     "q": "maderera OR \"venta de maderas\" construcción"},
    {"id": "sanitarios", "label": "Sanitarios y plomería", "icon": "🚿",
     "desc": "Caños, griferías, termotanques, sanitarios",
     "q": '"sanitarios" OR "materiales de plomería" casa venta'},
    {"id": "electricidad", "label": "Electricidad", "icon": "💡",
     "desc": "Cables, térmicas, cajas, iluminación",
     "q": '"materiales eléctricos" venta OR distribuidora eléctrica'},
    {"id": "pinturas", "label": "Pinturería", "icon": "🎨",
     "desc": "Pinturas, revestimientos, impermeabilizantes",
     "q": "pinturería venta pinturas"},
    {"id": "aberturas", "label": "Aberturas y vidrios", "icon": "🚪",
     "desc": "Puertas, ventanas, vidriería",
     "q": '"aberturas" fábrica OR venta puertas ventanas'},
    {"id": "techos", "label": "Techos y aislaciones", "icon": "🏠",
     "desc": "Chapas, tejas, membranas, aislantes",
     "q": "venta chapas OR tejas OR membranas techos"},
    {"id": "pisos", "label": "Pisos y revestimientos", "icon": "🔲",
     "desc": "Cerámicos, porcelanatos, adhesivos",
     "q": "cerámicos OR porcelanatos venta pisos revestimientos"},
]
_CAT_IDS = {c["id"] for c in CATEGORIAS}


def categoria_valida(cat_id: str) -> bool:
    return cat_id in _CAT_IDS


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or "").lower().strip())
    return re.sub(r"[^a-z0-9 ]", "", s)[:80]


async def reverse_geocode(lat: float, lon: float) -> dict:
    """Coordenadas → zona legible ("Godoy Cruz, Mendoza").

    Minimización de datos: se redondea a 3 decimales (~110 m) ANTES de salir
    hacia un tercero. Con `zoom=13` sólo se resuelve la ciudad/partido, así que
    la precisión de GPS crudo no aporta nada al resultado y sí expone de más
    (el domicilio exacto del usuario). Art. 4 Ley 25.326: los datos deben ser
    adecuados y no excesivos respecto de la finalidad.
    """
    lat, lon = round(float(lat), 3), round(float(lon), 3)
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=6.0)) as client:
        resp = await client.get(_NOMINATIM, params={
            "format": "jsonv2", "lat": lat, "lon": lon,
            "accept-language": "es", "zoom": 13,
        }, headers=_UA)
    if resp.status_code != 200:
        raise RuntimeError("No se pudo resolver la ubicación")
    addr = (resp.json() or {}).get("address") or {}
    ciudad = (addr.get("city") or addr.get("town") or addr.get("village")
              or addr.get("municipality") or addr.get("county") or "")
    provincia = addr.get("state") or ""
    zona = ", ".join(p for p in (ciudad, provincia) if p) or "Argentina"
    return {"zona": zona, "ciudad": ciudad, "provincia": provincia}


_STRUCT_PROMPT = (
    "Sos el curador de comercios de construcción de una plataforma argentina de "
    "real estate. Recibís resultados de búsqueda web y devolvés SOLO un JSON "
    "válido (sin markdown) con este formato exacto:\n"
    '{"comercios":[{"nombre":str,"direccion":str|null,"telefono":str|null,'
    '"sitio_web":str|null,"rating":number|null,"resumen":str,'
    '"info":{"web":bool,"telefono":bool,"direccion":bool,"precios_online":bool}}],'
    '"precios":[{"comercio":str,"material":str,"precio":str,"detalle":str|null}]}\n'
    "Reglas:\n"
    "- SOLO comercios físicos reales del rubro pedido con presencia en la zona "
    "pedida. NADA de MercadoLibre ni marketplaces: los constructores compran en "
    "corralones cerca de la obra.\n"
    "- Si un directorio (Páginas Amarillas, guías) menciona comercios concretos "
    "con datos, extraé LOS COMERCIOS, nunca el directorio como comercio.\n"
    "- Máximo 6, ordenados por calidad de información disponible (dirección + "
    "teléfono + web + precios) y reputación si aparece.\n"
    "- rating SOLO si aparece explícito en los resultados (ej: '4,6 estrellas'); "
    "jamás lo inventes. Lo mismo con teléfonos y direcciones: null si no están.\n"
    "- 'precios' solo con precios PUBLICADOS que aparezcan en los resultados, "
    "con su comercio; si no hay, lista vacía.\n"
    "- 'resumen': una línea útil para un constructor (qué venden, qué destaca).\n"
    "- Si no hay comercios reales, devolvé {\"comercios\":[],\"precios\":[]}."
)


async def _estructurar(zona: str, pedido: str, resultados: list[dict]) -> dict:
    from services.anthropic_service import get_client  # lazy: evita ciclos

    client = get_client()
    src = "\n\n".join(
        f"[{i+1}] {r.get('title','')}\nURL: {r.get('url','')}\n{(r.get('content') or '')[:700]}"
        for i, r in enumerate(resultados[:8])
    )
    user = f"Zona: {zona}\nPedido: {pedido}\n\nResultados de búsqueda:\n{src}"
    last: Exception | None = None
    for model in (settings.ANTHROPIC_MODEL_FAST, settings.ANTHROPIC_MODEL):
        try:
            msg = await asyncio.wait_for(client.messages.create(
                model=model, max_tokens=1400, system=_STRUCT_PROMPT,
                messages=[{"role": "user", "content": user}],
            ), timeout=25.0)
            raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
            data = json.loads(raw)
            if isinstance(data, dict) and isinstance(data.get("comercios"), list):
                return {"comercios": data["comercios"][:6],
                        "precios": data.get("precios") or []}
        except Exception as exc:  # noqa: BLE001 — probamos el siguiente modelo
            last = exc
    raise RuntimeError("No se pudo estructurar la búsqueda") from last


async def _tavily(query: str) -> list[dict]:
    if not settings.TAVILY_API_KEY:
        raise RuntimeError("La búsqueda de corralones no está configurada")
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=8.0)) as client:
        resp = await client.post(_TAVILY, json={
            "api_key": settings.TAVILY_API_KEY,
            "query": query, "search_depth": "basic", "max_results": 8,
        })
    if resp.status_code != 200:
        logger.warning("Corralones tavily %s: %s", resp.status_code, resp.text[:200])
        raise RuntimeError("La búsqueda falló, probá de nuevo")
    return (resp.json() or {}).get("results") or []


async def _cache_get(db: AsyncSession, key: str, ttl: timedelta) -> dict | None:
    row = (await db.execute(sql_text(
        "SELECT payload, updated_at FROM corralon_cache WHERE cache_key = :k"
    ), {"k": key})).first()
    if not row:
        return None
    updated = row[1]
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=UTC)
    if datetime.now(UTC) - updated > ttl:
        return None
    payload = row[0]
    return payload if isinstance(payload, dict) else json.loads(payload)


async def _cache_set(db: AsyncSession, key: str, payload: dict) -> None:
    await db.execute(sql_text(
        "INSERT INTO corralon_cache (cache_key, payload, updated_at) "
        "VALUES (:k, CAST(:p AS jsonb), now()) "
        "ON CONFLICT (cache_key) DO UPDATE SET payload = CAST(:p AS jsonb), updated_at = now()"
    ), {"k": key, "p": json.dumps(payload)})
    await db.commit()


async def buscar(db: AsyncSession, zona: str, categoria: str | None = None,
                 material: str | None = None, force: bool = False) -> dict:
    """Corralones de la zona por rubro, o dónde comprar un material puntual."""
    zona = zona.strip()
    if material:
        key = f"m:{_norm(zona)}:{_norm(material)}"
        ttl = _TTL_MATERIAL
        query = f"donde comprar {material} en {zona} corralón precio"
        pedido = f"comercios donde comprar: {material}"
    else:
        cat = next((c for c in CATEGORIAS if c["id"] == categoria), CATEGORIAS[0])
        key = f"c:{_norm(zona)}:{cat['id']}"
        ttl = _TTL_CATEGORIA
        query = f"{cat['q']} en {zona} dirección teléfono"
        pedido = f"rubro: {cat['label']} ({cat['desc']})"

    if not force:
        cached = await _cache_get(db, key, ttl)
        if cached is not None:
            cached["cache"] = True
            return cached

    resultados = await _tavily(query)
    data = await _estructurar(zona, pedido, resultados)
    payload = {
        "zona": zona,
        "categoria": None if material else (categoria or CATEGORIAS[0]["id"]),
        "material": material,
        "comercios": data["comercios"],
        "precios": data["precios"],
        "actualizado": datetime.now(UTC).isoformat(),
    }
    try:
        await _cache_set(db, key, payload)
    except Exception:  # noqa: BLE001 — el caché nunca rompe la respuesta
        logger.exception("Corralones: no se pudo cachear %s", key)
    return payload
