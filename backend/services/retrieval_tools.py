"""
Retrieval tools — extensión del moat para el chat general.

Capa 1A: el chat usa estas tools cuando le preguntan datos volátiles
(FX, índices, normativa). Reemplaza alucinar números con fetch a fuente
oficial + cita de last_updated.

Cada tool devuelve un dict serializable con campos `source`, `fetched_at`
y los datos. Si la fuente falla, devuelve `{"error": "..."}` — el LLM
decide cómo decírselo al usuario.

Tools incluidas:
  - get_dolar_cotizaciones    → dolarapi.com (oficial/blue/MEP/CCL/cripto/tarjeta)
  - get_indec_serie           → apis.datos.gob.ar series (IPC, ICC, etc.)
  - fetch_official_source     → GET a URL del whitelist + extracción a texto

El chat NO usa todas las tools de SOL (pagos, contactos, recordatorios).
Solo estas tres + un par read-only del proyecto del usuario si tiene.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from config.settings import settings
from services import retrieval_service as rs

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# Schemas (formato Anthropic tool_use)
# ════════════════════════════════════════════════════════════════════
RETRIEVAL_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_dolar_cotizaciones",
        "description": (
            "Devuelve cotizaciones del dólar en Argentina, en tiempo real "
            "(refresca cada 5 min). Tipos disponibles: 'oficial', 'blue', "
            "'bolsa' (MEP), 'contadoconliqui' (CCL), 'mayorista', 'cripto', "
            "'tarjeta'. Si no pasás `tipo`, devuelve TODOS.\n\n"
            "Usalo SIEMPRE que el usuario pregunte 'a cuánto está el dólar', "
            "'cotización MEP/CCL/blue', o necesites convertir ARS↔USD con "
            "tipo de cambio actual. Nunca inventes el valor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": [
                        "oficial",
                        "blue",
                        "bolsa",
                        "contadoconliqui",
                        "mayorista",
                        "cripto",
                        "tarjeta",
                    ],
                    "description": "Tipo de cotización. Omitir para todas.",
                }
            },
        },
    },
    {
        "name": "get_indec_serie",
        "description": (
            "Devuelve los últimos valores de una serie de tiempo oficial AR "
            "(API de datos abiertos del Gobierno: apis.datos.gob.ar). "
            "Útil para IPC, ICC (costo de construcción), salarios, tipo de "
            "cambio promedio, etc.\n\n"
            "IDs frecuentes (pasalas en `serie_id`):\n"
            "  • IPC nivel general nacional (mensual): 148.3_INIVELNAL_DICI_M_26\n"
            "  • IPC variación interanual: 148.3_INIVELNAL_DICI_M_26 (calculá variación)\n"
            "  • ICC nivel general (mensual): 41.4_ICCEEE_2016_M_22\n"
            "  • Tipo de cambio mayorista BCRA promedio mensual: 116.3_TCRMA_0_M_36\n"
            "  • EMAE nivel general: 143.3_NO_PR_2004_A_21\n\n"
            "Si no sabés la ID, usá fetch_official_source con "
            "https://apis.datos.gob.ar/series/api/search/?q=<keyword> primero. "
            "Devuelve `data` con [[fecha, valor], ...] y `meta`."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "serie_id": {
                    "type": "string",
                    "description": "ID de la serie en datos.gob.ar.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 60,
                    "default": 12,
                    "description": "Cantidad de períodos recientes a traer.",
                },
            },
            "required": ["serie_id"],
        },
    },
    {
        "name": "search_web",
        "description": (
            "Búsqueda web en tiempo real vía Tavily. Devuelve los top "
            "snippets relevantes a tu query + un `answer` agregado.\n\n"
            "USAR PARA datos de mercado privado y noticias del rubro que NO "
            "están en fuentes oficiales:\n"
            "  • Precios m² por barrio (Zonaprop, MercadoLibre, RI, Properati)\n"
            "  • Comparables de propiedades\n"
            "  • Tendencias del mercado RE argentino\n"
            "  • Anuncios y movimientos de developers\n"
            "  • Noticias recientes del sector\n"
            "  • Planes de gobierno / cambios regulatorios recientes\n\n"
            "NO USAR PARA datos que ya tienen tool específica:\n"
            "  • Dólar → get_dolar_cotizaciones (más rápida)\n"
            "  • IPC/ICC INDEC → get_indec_serie\n"
            "  • Norma específica en infoleg (con URL conocida) → fetch_official_source\n\n"
            "Citá SIEMPRE título + URL + fecha del snippet en tu respuesta. "
            "Si los resultados se contradicen, decilo explícitamente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 400,
                    "description": "Términos a buscar. Sé específico: 'precio m² palermo capital federal abril 2026' rinde más que 'palermo precio'.",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "default": "basic",
                    "description": "advanced cuesta más créditos pero rinde mejor para preguntas complejas.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_official_source",
        "description": (
            "GET genérico a una URL de FUENTE OFICIAL argentina. Solo acepta "
            "dominios whitelisteados (.gob.ar, BCRA, INDEC, ARBA, AGIP, AFIP, "
            "GCBA, infoleg, BORA, apis.datos.gob.ar). Si pasás un dominio que "
            "no está, devuelve error.\n\n"
            "Devuelve texto plano extraído (truncado a ~8000 chars). Usalo "
            "para:\n"
            "  • Leer una norma específica en infoleg (URL del articulado).\n"
            "  • Consultar el sitio de ARBA/AGIP para una alícuota.\n"
            "  • Buscar en BORA una publicación reciente.\n"
            "  • Datos de Buenos Aires Data (data.buenosaires.gob.ar/api/...).\n\n"
            "NUNCA uses esta tool para sitios privados/portales inmobiliarios. "
            "Solo fuentes oficiales del whitelist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL completa con esquema https://...",
                },
                "max_chars": {
                    "type": "integer",
                    "minimum": 500,
                    "maximum": 12000,
                    "default": 6000,
                    "description": "Cap de caracteres devueltos.",
                },
            },
            "required": ["url"],
        },
    },
]


# ════════════════════════════════════════════════════════════════════
# Implementaciones
# ════════════════════════════════════════════════════════════════════
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_DOLAR_BASE = "https://dolarapi.com/v1/dolares"


async def _tool_get_dolar_cotizaciones(**inputs: Any) -> dict:
    tipo = inputs.get("tipo")
    url = f"{_DOLAR_BASE}/{tipo}" if tipo else _DOLAR_BASE
    try:
        data = await rs.fetch_json(url, ttl_seconds=300)
    except rs.RetrievalError as e:
        return {"error": str(e), "source": url}

    # Normalizamos: si pidió un tipo puntual devolvemos el dict; si pidió todos,
    # devolvemos lista. Le decimos al LLM la fecha de actualización de la fuente.
    return {
        "source": url,
        "fetched_at": _now_iso(),
        "ttl_seconds": 300,
        "data": data,
        "notes": (
            "Datos de dolarapi.com (agregador comunitario). Cada item trae su "
            "propio campo 'fechaActualizacion' con la última actualización real."
        ),
    }


_INDEC_SERIES_BASE = "https://apis.datos.gob.ar/series/api/series"


async def _tool_get_indec_serie(**inputs: Any) -> dict:
    serie_id = (inputs.get("serie_id") or "").strip()
    if not serie_id:
        return {"error": "serie_id vacío"}
    limit = int(inputs.get("limit") or 12)
    limit = max(1, min(60, limit))

    params = {
        "ids": serie_id,
        "limit": limit,
        "sort": "desc",  # más nuevos primero
        "format": "json",
    }
    try:
        data = await rs.fetch_json(
            _INDEC_SERIES_BASE,
            params=params,
            ttl_seconds=21600,  # 6h: estos índices son mensuales/trimestrales
            cache_key_suffix=str(limit),
        )
    except rs.RetrievalError as e:
        return {"error": str(e), "source": _INDEC_SERIES_BASE}

    return {
        "source": _INDEC_SERIES_BASE,
        "fetched_at": _now_iso(),
        "ttl_seconds": 21600,
        "serie_id": serie_id,
        "data": data,
    }


_TAVILY_URL = "https://api.tavily.com/search"
_TAVILY_TIMEOUT = httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=5.0)


async def _tool_search_web(**inputs: Any) -> dict:
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        return {
            "error": (
                "Búsqueda web no configurada (falta TAVILY_API_KEY). "
                "Avisale al usuario que no podés buscar en la web y "
                "fundamentá con lo que tenés (KB + fuentes oficiales)."
            )
        }

    query = (inputs.get("query") or "").strip()
    if not query:
        return {"error": "query vacía"}

    max_results = int(inputs.get("max_results") or 5)
    max_results = max(1, min(10, max_results))
    search_depth = inputs.get("search_depth") or "basic"
    if search_depth not in ("basic", "advanced"):
        search_depth = "basic"

    # Caché 1h. La key NO incluye la api_key (cambiarla no debería invalidar).
    cache_key = f"tavily::{query}::{max_results}::{search_depth}"
    cached = rs._cache_get(cache_key)
    if cached is not None:
        return cached

    body = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
        "topic": "general",
    }

    client = await rs.get_client()
    try:
        resp = await client.post(_TAVILY_URL, json=body, timeout=_TAVILY_TIMEOUT)
    except httpx.RequestError as e:
        return {"error": f"Tavily no respondió: {e}"}

    if resp.status_code == 401:
        return {"error": "Tavily rechazó la API key (401)."}
    if resp.status_code == 429:
        return {"error": "Tavily rate limit (429). Probá de nuevo en unos minutos."}
    if resp.status_code >= 500:
        return {"error": f"Tavily caído ({resp.status_code})."}
    if resp.status_code >= 400:
        return {"error": f"Tavily error {resp.status_code}: {resp.text[:200]}"}

    try:
        data = resp.json()
    except ValueError as e:
        return {"error": f"Tavily devolvió no-JSON: {e}"}

    # Compactar snippets para no inflar tokens: 800 chars por resultado max.
    results = []
    for r in (data.get("results") or [])[:max_results]:
        results.append(
            {
                "title": (r.get("title") or "")[:200],
                "url": r.get("url"),
                "snippet": (r.get("content") or "")[:800],
                "published_date": r.get("published_date"),
                "score": r.get("score"),
            }
        )

    payload = {
        "query": query,
        "answer": (data.get("answer") or "")[:1500] or None,
        "results": results,
        "fetched_at": _now_iso(),
        "ttl_seconds": 3600,
        "source": "tavily.com",
    }
    rs._cache_set(cache_key, payload, ttl_seconds=3600)
    return payload


async def _tool_fetch_official_source(**inputs: Any) -> dict:
    url = (inputs.get("url") or "").strip()
    if not url:
        return {"error": "url vacía"}
    max_chars = int(inputs.get("max_chars") or 6000)
    max_chars = max(500, min(12000, max_chars))

    try:
        text = await rs.fetch_text(url, ttl_seconds=3600, max_chars=max_chars)
    except rs.RetrievalError as e:
        return {"error": str(e), "url": url}

    return {
        "source": url,
        "fetched_at": _now_iso(),
        "ttl_seconds": 3600,
        "char_count": len(text),
        "text": text,
    }


# ════════════════════════════════════════════════════════════════════
# Registry
# ════════════════════════════════════════════════════════════════════
RETRIEVAL_TOOL_IMPLS = {
    "get_dolar_cotizaciones": _tool_get_dolar_cotizaciones,
    "get_indec_serie": _tool_get_indec_serie,
    "search_web": _tool_search_web,
    "fetch_official_source": _tool_fetch_official_source,
}


async def run_retrieval_tool(name: str, inputs: dict[str, Any]) -> dict:
    """Despacha. No necesita db/user (son tools puras de red)."""
    impl = RETRIEVAL_TOOL_IMPLS.get(name)
    if impl is None:
        return {"error": f"Tool desconocida: {name}"}
    try:
        return await impl(**(inputs or {}))
    except Exception as e:
        logger.exception("Retrieval tool %s falló", name)
        return {"error": f"Tool {name} falló: {e}"}
