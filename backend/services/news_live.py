"""
NewsLive — agregador de noticias REALES en vivo para el rubro real estate AR.

Independiente (cliente httpx + cache propios; NO toca el retrieval de la Capa 2).
Trae noticias vía Tavily (topic=news) cubriendo todo el rubro de punta a punta, y
arma un "digest" transformativo con IA (puntos clave + por qué importa para real
estate) para leer la nota dentro de la plataforma — sin reproducir el artículo
completo (se cita la fuente con su link).
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

_TAVILY_URL = "https://api.tavily.com/search"
_TIMEOUT = httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=5.0)

# Medios argentinos / en español del rubro (economía, inmobiliario, construcción,
# arquitectura). Restringimos a estos para que el feed sea RELEVANTE para AR y en
# español, en vez de traer noticias de EE.UU. Ampliable.
_AR_DOMAINS = [
    "ambito.com", "cronista.com", "infobae.com", "lanacion.com.ar", "clarin.com",
    "iprofesional.com", "perfil.com", "pagina12.com.ar", "baenegocios.com",
    "eleconomista.com.ar", "forbesargentina.com", "reporteinmobiliario.com",
    "mdzol.com", "lavoz.com.ar", "losandes.com.ar", "plataformaarquitectura.cl",
    "areaurbana.com", "elcronista.com", "apertura.com",
]

# Categorías que cubren el rubro de punta a punta. query=None → feed mezclado.
CATEGORIES: dict[str, dict[str, Any]] = {
    "todas": {"label": "Todas", "query": None,
              "mix": ["economia", "inmobiliario", "construccion", "proyectos"]},
    "economia": {"label": "Economía y macro",
                 "query": "economía argentina inflación dólar tasas crédito hipotecario inversión inmobiliaria mercado"},
    "inmobiliario": {"label": "Inmobiliario",
                     "query": "mercado inmobiliario argentina precios m2 alquileres venta propiedades operaciones"},
    "construccion": {"label": "Construcción",
                     "query": "construcción argentina costos materiales obra desarrollo edilicio índice construcción"},
    "proyectos": {"label": "Grandes proyectos",
                  "query": "nuevos desarrollos inmobiliarios argentina grandes proyectos torres barrios privados real estate"},
    "arquitectura": {"label": "Arquitectura",
                     "query": "arquitectura argentina diseño edificios estudios urbanismo premios"},
    "politica": {"label": "Política y normativa",
                 "query": "argentina vivienda blanqueo inmobiliario normativa urbana créditos UVA medidas gobierno real estate"},
}

# ── Cache simple en memoria (TTL) ──
_cache: dict[str, tuple[float, Any]] = {}
_FEED_TTL = 900       # 15 min — un refresh "Actualizar" bypassa el cache
_DIGEST_TTL = 86400   # 24 h — el digest de una nota no cambia
_MAX_AGE_DAYS = 21    # descarta noticias más viejas que esto (feed actual)


def _parse_dt(s: str | None) -> datetime | None:
    """Parsea la fecha de Tavily (RFC822 'Wed, 17 Jun 2026...' o ISO). None si no se puede."""
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _cache_get(key: str) -> Any | None:
    hit = _cache.get(key)
    if not hit:
        return None
    expiry, value = hit
    if time.time() > expiry:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any, ttl: int) -> None:
    _cache[key] = (time.time() + ttl, value)


def _domain(url: str | None) -> str:
    if not url:
        return ""
    try:
        net = urlparse(url).netloc.lower()
        return net[4:] if net.startswith("www.") else net
    except Exception:  # noqa: BLE001
        return ""


def _card(r: dict, category: str) -> dict | None:
    url = r.get("url")
    title = (r.get("title") or "").strip()
    if not url or not title:
        return None
    return {
        "title": title[:240],
        "url": url,
        "source": _domain(url),
        "published_date": r.get("published_date"),
        "snippet": (r.get("content") or "").strip()[:400],
        "category": category,
        "score": r.get("score"),
    }


async def _tavily_news(query: str, max_results: int = 12, days: int = 10) -> list[dict]:
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        logger.warning("NewsLive: falta TAVILY_API_KEY")
        return []
    body = {
        "api_key": api_key, "query": query, "max_results": max(1, min(20, max_results)),
        "search_depth": "basic", "topic": "news", "days": days,
        "include_domains": _AR_DOMAINS,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(_TAVILY_URL, json=body)
        if resp.status_code != 200:
            logger.warning("NewsLive: Tavily %s — %s", resp.status_code, resp.text[:160])
            return []
        return resp.json().get("results") or []
    except Exception as e:  # noqa: BLE001
        logger.warning("NewsLive: Tavily falló — %s", e)
        return []


def _dedupe_sort(cards: list[dict]) -> list[dict]:
    """Dedup + descarta lo que tiene fecha VIEJA (>_MAX_AGE_DAYS) + ordena.

    Tavily a veces no trae published_date (lo deja null), sobre todo en medios AR.
    NO descartamos esas (las dejamos, presumiblemente recientes por la ventana
    days=10 de Tavily) — solo tiramos las que SÍ tienen fecha y es vieja (el caso
    'noticia de marzo 2025'). Orden: primero las fechadas más nuevas, después las
    sin fecha. Así el feed es actual sin quedar vacío."""
    cutoff = datetime.now(UTC) - timedelta(days=_MAX_AGE_DAYS)
    seen: set[str] = set()
    dated: list[dict] = []
    undated: list[dict] = []
    for c in cards:
        key = c["url"]
        if key in seen:
            continue
        dt = _parse_dt(c.get("published_date"))
        if dt is not None and dt < cutoff:
            continue  # tiene fecha y es vieja → fuera
        seen.add(key)
        if dt is not None:
            c["published_date"] = dt.isoformat()
            c["_ts"] = dt.timestamp()
            dated.append(c)
        else:
            c["published_date"] = None
            undated.append(c)
    dated.sort(key=lambda c: c["_ts"], reverse=True)
    for c in dated:
        c.pop("_ts", None)
    return dated + undated


async def fetch_feed(category: str = "todas", limit: int = 24, refresh: bool = False) -> dict:
    """Trae el feed de noticias de una categoría (o mezclado para 'todas')."""
    category = category if category in CATEGORIES else "todas"
    cache_key = f"feed::{category}"
    if not refresh:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    cfg = CATEGORIES[category]
    if cfg["query"] is None:  # 'todas' → mezcla de categorías en paralelo
        mix = cfg["mix"]
        results = await asyncio.gather(*[
            _tavily_news(CATEGORIES[k]["query"], max_results=12) for k in mix
        ])
        cards = [c for k, res in zip(mix, results, strict=False) for r in res if (c := _card(r, k))]
    else:
        res = await _tavily_news(cfg["query"], max_results=min(20, limit))
        cards = [c for r in res if (c := _card(r, category))]

    cards = _dedupe_sort(cards)[:limit]
    payload = {
        "category": category,
        "items": cards,
        "count": len(cards),
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    _cache_set(cache_key, payload, _FEED_TTL)
    return payload


# ── Lectura de la nota: digest transformativo con IA ──

_DIGEST_TOOL = {
    "name": "armar_digest_noticia",
    "description": "Arma un resumen periodístico propio (transformativo) de una noticia para real estate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "lead": {"type": "string", "description": "1-2 frases gancho que resumen la noticia."},
            "puntos_clave": {"type": "array", "items": {"type": "string"},
                             "description": "3-6 bullets con la info relevante de la nota, en palabras propias."},
            "impacto_real_estate": {"type": "string",
                                    "description": "2-4 frases: por qué le importa a alguien del rubro inmobiliario AR."},
            "dato_clave": {"type": "string", "description": "El número/dato más importante, si hay (opcional)."},
        },
        "required": ["lead", "puntos_clave", "impacto_real_estate"],
    },
}

_DIGEST_SYSTEM = (
    "Sos editor de un medio propio de real estate argentino. Te paso el texto de una noticia de otro "
    "medio y armás un resumen PROPIO y TRANSFORMATIVO para nuestros lectores, llamando a la tool. "
    "REGLAS ESTRICTAS: NO copies frases textuales largas ni reproduzcas la nota completa (derechos de "
    "autor) — reescribí con tus palabras, sintético. Quedate con lo relevante para que el lector entienda "
    "todo sin ir a la fuente, pero sin transcribir el artículo. No inventes datos que no estén en el texto. "
    "Agregá el ángulo real estate (qué significa para inversores/desarrolladores/inmobiliarias AR). "
    "Español rioplatense, claro y profesional."
)


async def _fetch_article_text(url: str) -> tuple[str | None, str | None]:
    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RE-Expert-News/1.0)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        image = og.group(1) if og else None
        html = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&#039;", "'").replace("&quot;", '"'))
        text = re.sub(r"\s+", " ", text).strip()
        return image, text[:9000]  # type: ignore[return-value]
    except Exception as e:  # noqa: BLE001
        logger.warning("NewsLive: no se pudo bajar %s — %s", url, e)
        return None, None  # type: ignore[return-value]


async def make_digest(url: str, title: str = "", snippet: str = "",
                      source: str = "", category: str = "") -> dict:
    """Trae el artículo y arma el digest IA. Tolerante: si falla, usa el snippet."""
    cache_key = f"digest::{url}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    image, text = await _fetch_article_text(url)
    content = text or snippet or title
    digest: dict[str, Any] = {}
    parcial = True

    if content and len(content) > 120:
        try:
            from services.anthropic_service import get_client
            client = get_client()
            resp = await client.messages.create(
                model=settings.ANTHROPIC_MODEL_FAST,
                max_tokens=900,
                system=_DIGEST_SYSTEM,
                tools=[_DIGEST_TOOL],
                tool_choice={"type": "tool", "name": "armar_digest_noticia"},
                messages=[{"role": "user", "content": f"Título: {title}\nFuente: {source}\n\nTexto:\n{content}"}],
            )
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use":
                    digest = dict(block.input)
                    parcial = False
                    break
        except Exception as e:  # noqa: BLE001 — la IA no debe tumbar la lectura
            logger.warning("NewsLive: digest IA falló — %s", e)

    if not digest:
        digest = {"lead": snippet or title, "puntos_clave": [], "impacto_real_estate": ""}

    payload = {
        "title": title,
        "url": url,
        "source": source or _domain(url),
        "category": category,
        "image_url": image,
        "lead": digest.get("lead", ""),
        "puntos_clave": digest.get("puntos_clave", []) or [],
        "impacto_real_estate": digest.get("impacto_real_estate", ""),
        "dato_clave": digest.get("dato_clave"),
        "parcial": parcial,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if not parcial:
        _cache_set(cache_key, payload, _DIGEST_TTL)
    return payload
