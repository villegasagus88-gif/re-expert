"""
Retrieval service: fetcher de fuentes oficiales argentinas con caché in-memory.

Capa 1A del moat: el chat tiene que poder buscar datos volátiles (FX, índices,
normativa) en vez de inventarlos. Esta capa expone un cliente HTTP único con:

  - Whitelist estricta de hosts (.gob.ar / .gov.ar + APIs públicas conocidas).
    Bloquea SSRF y evita que el LLM tire fetches a cualquier URL.
  - Caché in-memory por (URL, params) con TTL por categoría.
  - Timeouts cortos (5s) — si una fuente está caída, falla rápido y el LLM
    avisa al usuario en vez de bloquear el stream.

NO persiste nada: si el server reinicia, el caché se vacía. Aceptable porque
Railway tiene 1 instancia y los TTL son cortos.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ─── Whitelist de hosts ────────────────────────────────────────────────
# Solo se puede fetchear desde estos dominios. Cualquier otra cosa = error.
# Para agregar uno nuevo, sumalo acá explícitamente.
ALLOWED_HOSTS: set[str] = {
    # APIs de cotizaciones (tercero comunitario, pero estable)
    "dolarapi.com",
    "api.bluelytics.com.ar",
    # BCRA
    "www.bcra.gob.ar",
    "api.bcra.gob.ar",
    # INDEC
    "www.indec.gob.ar",
    "apis.datos.gob.ar",  # ckan datos abiertos AR (incluye series INDEC)
    # Infoleg (normativa nacional)
    "www.infoleg.gob.ar",
    "servicios.infoleg.gob.ar",
    # Boletín Oficial
    "www.boletinoficial.gob.ar",
    # GCBA (CABA)
    "www.buenosaires.gob.ar",
    "data.buenosaires.gob.ar",
    "boletinoficial.buenosaires.gob.ar",
    # ARBA (PBA)
    "www.arba.gov.ar",
    # AGIP (CABA tributario)
    "www.agip.gob.ar",
    # AFIP / ARCA
    "www.afip.gob.ar",
    "www.argentina.gob.ar",
    # Portales con normativa indexada
    "norma.servicios.gob.ar",
}

DEFAULT_TIMEOUT = httpx.Timeout(connect=3.0, read=5.0, write=3.0, pool=5.0)
MAX_BODY_BYTES = 1_500_000  # 1.5 MB por response; corta scrapes salvajes.
MAX_TEXT_CHARS = 8000  # devolvemos como mucho 8K chars de texto al LLM.

# ─── Cliente HTTP único ────────────────────────────────────────────────
_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                _client = httpx.AsyncClient(
                    timeout=DEFAULT_TIMEOUT,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "RE-Expert/1.0 (+https://re-expert.app)",
                        "Accept-Language": "es-AR,es;q=0.9",
                    },
                    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# ─── Caché TTL in-memory ───────────────────────────────────────────────
# key → (expires_at_epoch, value)
_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = asyncio.Lock()


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    _cache[key] = (time.time() + ttl_seconds, value)


# ─── Validación de host ────────────────────────────────────────────────
def _host_allowed(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host.lower() in ALLOWED_HOSTS


# ─── Limpieza HTML → texto ─────────────────────────────────────────────
_SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def html_to_text(html: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    """Extracción minimalista HTML → texto plano. No usa BS4 (no en deps)."""
    text = _SCRIPT_STYLE_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "… [truncado]"
    return text


# ─── Fetch público ─────────────────────────────────────────────────────
class RetrievalError(Exception):
    """Error en una llamada a fuente externa (no whitelist, timeout, 5xx, etc.)."""


async def fetch_json(
    url: str,
    *,
    params: dict | None = None,
    ttl_seconds: int = 300,
    cache_key_suffix: str = "",
) -> Any:
    """GET a una URL whitelisteada, parsea JSON, cachea TTL."""
    if not _host_allowed(url):
        raise RetrievalError(f"Host no permitido: {urlparse(url).hostname}")

    key = f"json::{url}::{sorted((params or {}).items())}::{cache_key_suffix}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    client = await get_client()
    try:
        resp = await client.get(url, params=params)
    except httpx.RequestError as e:
        raise RetrievalError(f"No se pudo conectar a {url}: {e}") from e

    if resp.status_code >= 500:
        raise RetrievalError(f"Fuente {url} respondió {resp.status_code}")
    if resp.status_code >= 400:
        raise RetrievalError(f"Fuente {url} rechazó la consulta ({resp.status_code})")

    try:
        data = resp.json()
    except ValueError as e:
        raise RetrievalError(f"Respuesta no-JSON de {url}: {e}") from e

    _cache_set(key, data, ttl_seconds)
    return data


async def fetch_text(
    url: str,
    *,
    params: dict | None = None,
    ttl_seconds: int = 3600,
    max_chars: int = MAX_TEXT_CHARS,
) -> str:
    """GET a una URL whitelisteada, extrae texto plano si es HTML, cachea TTL."""
    if not _host_allowed(url):
        raise RetrievalError(f"Host no permitido: {urlparse(url).hostname}")

    key = f"text::{url}::{sorted((params or {}).items())}::{max_chars}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    client = await get_client()
    try:
        resp = await client.get(url, params=params)
    except httpx.RequestError as e:
        raise RetrievalError(f"No se pudo conectar a {url}: {e}") from e

    if resp.status_code >= 500:
        raise RetrievalError(f"Fuente {url} respondió {resp.status_code}")
    if resp.status_code >= 400:
        raise RetrievalError(f"Fuente {url} rechazó la consulta ({resp.status_code})")

    raw = resp.content[:MAX_BODY_BYTES]
    try:
        body = raw.decode(resp.encoding or "utf-8", errors="replace")
    except LookupError:
        body = raw.decode("utf-8", errors="replace")

    ctype = (resp.headers.get("content-type") or "").lower()
    if "html" in ctype:
        text = html_to_text(body, max_chars=max_chars)
    else:
        text = body[:max_chars]

    _cache_set(key, text, ttl_seconds)
    return text


# ─── Diagnóstico ───────────────────────────────────────────────────────
def cache_stats() -> dict[str, int]:
    """Para debug/observabilidad básica."""
    now = time.time()
    live = sum(1 for exp, _ in _cache.values() if exp > now)
    return {"entries_total": len(_cache), "entries_live": live}
