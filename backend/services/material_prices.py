"""
Material Prices Live — actualizador automático de precios de materiales.

Disparo: perezoso ("cada vez que el usuario entra"): GET /api/materials
llama a maybe_refresh_prices(); si la última actualización tiene más de
REFRESH_HOURS, se lanza un refresh EN BACKGROUND (el usuario nunca espera:
ve los últimos precios guardados y el refresh actualiza para la próxima).

Pipeline del refresh:
  1. ~7 búsquedas Tavily agrupadas por rubro (precios corralón Argentina).
  2. Un solo llamado a Claude (tool forzado) que matchea los hallazgos
     contra NUESTROS nombres exactos de material y devuelve precio+confianza.
  3. Guardas de sanidad: solo se aplica si confianza >= 70 y el precio nuevo
     está dentro de ±40% del vigente (un scrape malo nunca rompe el catálogo).
  4. Upsert en material_price_override (el CSV curado queda como base).

Si faltan TAVILY_API_KEY o ANTHROPIC_API_KEY, el refresh se saltea en
silencio y la sección sigue funcionando con el CSV.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

REFRESH_HOURS = 20          # "diario": si pasaron >20h, refrescar
MIN_RETRY_MINUTES = 60      # ante fallas, no reintentar antes de 1h
MAX_PRICE_JUMP_PCT = 40.0   # guarda de sanidad vs precio vigente
MIN_CONFIDENCE = 70

_TAVILY_URL = "https://api.tavily.com/search"
_QUERIES = [
    "precio bolsa cemento portland 50kg cal hidraulica corralon argentina",
    "precio hierro construccion 8mm 10mm 12mm barra 12m argentina",
    "precio ladrillo hueco 12x18x33 18x18x33 ladrillo comun bloque cemento argentina",
    "precio arena gruesa piedra partida m3 hormigon elaborado H21 argentina",
    "precio membrana asfaltica caño pvc 110 termofusion cable 2.5mm argentina",
    "precio ceramica porcelanato 60x60 piso flotante pegamento ceramico argentina",
    "precio latex interior 20 litros esmalte sintetico placa durlock argentina",
]

_EXTRACT_TOOL = {
    "name": "reportar_precios",
    "description": "Precios actuales encontrados, matcheados contra el catálogo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "updates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "material": {"type": "string", "description": "Nombre EXACTO del catálogo provisto"},
                        "precio_ars": {"type": "integer", "minimum": 1},
                        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                        "fuente": {"type": "string", "description": "Dominio o medio de donde salió el precio"},
                    },
                    "required": ["material", "precio_ars", "confidence", "fuente"],
                },
            },
        },
        "required": ["updates"],
    },
}

# Estado del disparador perezoso (proceso único de Railway)
_refresh_lock = asyncio.Lock()
# Refs a las tasks de fondo: sin esto el GC puede recolectar la task a mitad de
# I/O y el refresh "no pasa" sin error (data vieja). add_done_callback las suelta.
_bg_tasks: set = set()
_last_attempt: datetime | None = None


async def _tavily_search(client: httpx.AsyncClient, query: str) -> str:
    try:
        resp = await client.post(_TAVILY_URL, json={
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 4,
            "include_answer": False,
            "days": 45,
        }, timeout=25)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return "\n".join(
            f"[{r.get('url', '')}] {r.get('title', '')}: {(r.get('content') or '')[:600]}"
            for r in results
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("MaterialPrices: Tavily falló para '%s': %s", query[:40], exc)
        return ""


async def refresh_prices(current: dict[str, int]) -> int:
    """Corre el pipeline completo. `current` = {material: precio vigente}.

    Devuelve la cantidad de precios actualizados. Abre su propia sesión de DB
    (corre en background, fuera del request).
    """
    if not settings.TAVILY_API_KEY or not settings.ANTHROPIC_API_KEY:
        logger.info("MaterialPrices: sin API keys — refresh salteado")
        return 0

    async with httpx.AsyncClient() as client:
        chunks = await asyncio.gather(*[_tavily_search(client, q) for q in _QUERIES])
    evidence = "\n\n".join(c for c in chunks if c)
    if len(evidence) < 200:
        logger.info("MaterialPrices: Tavily no devolvió evidencia útil")
        return 0

    catalog = "\n".join(f"- {name} (precio vigente: ${price:,})".replace(",", ".")
                        for name, price in current.items())
    from services.anthropic_service import get_client
    resp = await get_client().messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4000,
        system=(
            "Sos un analista de costos de construcción en Argentina. Te paso resultados de "
            "búsqueda web recientes y un catálogo de materiales con sus precios vigentes. "
            "Matcheá SOLO los materiales del catálogo cuyo precio actual encuentres con "
            "claridad en la evidencia (mismo producto y presentación: bolsa/kg/m³/caja). "
            "Precios FINALES en pesos argentinos, sin símbolo. Confianza honesta: si el "
            "precio es de otra presentación, otra medida o es dudoso, confianza baja o no "
            "lo incluyas. NUNCA inventes precios que no estén en la evidencia."
        ),
        messages=[{"role": "user", "content": (
            "CATÁLOGO:\n" + catalog + "\n\nEVIDENCIA WEB:\n" + evidence[:60000]
            + "\n\nDevolvé las actualizaciones con el tool."
        )}],
        tools=[_EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "reportar_precios"},
    )
    updates = []
    for block in resp.content:
        if getattr(block, "type", "") == "tool_use" and block.name == "reportar_precios":
            updates = block.input.get("updates", [])

    # Guardas de sanidad + upsert
    from models.base import get_session_factory
    from models.material_price import MaterialPriceOverride
    from sqlalchemy import select

    applied = 0
    async with get_session_factory()() as db:
        for u in updates:
            name = (u.get("material") or "").strip()
            price = int(u.get("precio_ars") or 0)
            conf = int(u.get("confidence") or 0)
            base = current.get(name)
            if not name or base is None or price <= 0 or conf < MIN_CONFIDENCE:
                continue
            jump = abs(price - base) / base * 100
            if jump > MAX_PRICE_JUMP_PCT:
                logger.info("MaterialPrices: descartado %s (salto %.0f%%)", name[:40], jump)
                continue
            variacion = round((price - base) / base * 100, 1)
            row = (await db.execute(select(MaterialPriceOverride).where(
                MaterialPriceOverride.material == name))).scalar_one_or_none()
            if row:
                # variación acumulada vs CSV base se recalcula contra el precio previo mostrado
                row.precio_ars = price
                row.variacion_mensual_pct = variacion if variacion != 0 else row.variacion_mensual_pct
                row.fuente = (u.get("fuente") or "")[:255]
                row.updated_at = datetime.now(UTC)
            else:
                db.add(MaterialPriceOverride(
                    material=name, precio_ars=price, variacion_mensual_pct=variacion,
                    fuente=(u.get("fuente") or "")[:255],
                ))
            applied += 1
        await db.commit()
    logger.info("MaterialPrices: refresh aplicó %d precios (de %d propuestos)", applied, len(updates))
    return applied


def maybe_refresh_prices(current: dict[str, int], last_update: datetime | None) -> None:
    """Disparador perezoso: si la data está vieja, refresca en background.

    Nunca bloquea el request que lo invoca.
    """
    global _last_attempt
    now = datetime.now(UTC)
    if last_update and (now - last_update) < timedelta(hours=REFRESH_HOURS):
        return
    if _last_attempt and (now - _last_attempt) < timedelta(minutes=MIN_RETRY_MINUTES):
        return
    if _refresh_lock.locked():
        return
    _last_attempt = now

    async def _run():
        async with _refresh_lock:
            try:
                await refresh_prices(current)
            except Exception:  # noqa: BLE001 — el refresh nunca afecta a la app
                logger.exception("MaterialPrices: refresh en background falló")

    _t = asyncio.create_task(_run())
    _bg_tasks.add(_t)
    _t.add_done_callback(_bg_tasks.discard)
