"""
NewsLive — diario en vivo del rubro real estate AR vía RSS de medios argentinos.

Independiente (httpx + cache propios; NO toca la Capa 2). Lee feeds RSS reales de
medios AR (Ámbito, Infobae, La Nación, Clarín, Plataforma Arquitectura), filtra a
lo relevante para el rubro (inmobiliario, construcción, economía/macro, proyectos,
arquitectura, política de vivienda), rankea por recencia + impacto, pagina, y arma
un "digest" transformativo con IA para leer la nota adentro de la plataforma.

Por qué RSS y no Tavily: Tavily con include_domains devolvía páginas de archivo
sin fecha (se colaban notas viejas); los RSS traen artículos recientes, con fecha
confiable (pubDate) y en volumen.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
import zlib
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
_UA = {"User-Agent": "Mozilla/5.0 (compatible; RE-Expert-News/1.0)"}
_MAX_AGE_DAYS = 30          # descarta lo más viejo que ~1 mes
_RAW_TTL = 600             # 10 min — cache del fetch crudo de RSS
_FEED_TTL = 600            # 10 min — cache de la lista rankeada por categoría
_DIGEST_TTL = 86400        # 24 h

# Feeds RSS validados (andan y traen fecha). force_cat: feed monotemático.
RSS_FEEDS = [
    # mode 'macro': se distribuye por keyword (default economia). 'section': cat fija, toma todo.
    # 'strict': cat fija, sólo items que matchean las keywords de esa cat (filtra feeds generales).
    {"url": "https://www.ambito.com/rss/economia.xml", "source": "ambito.com", "mode": "macro", "cat": "economia"},
    {"url": "https://www.ambito.com/rss/finanzas.xml", "source": "ambito.com", "mode": "macro", "cat": "economia"},
    {"url": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/?outputType=xml",
     "source": "infobae.com", "mode": "macro", "cat": "economia"},
    {"url": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/economia/?outputType=xml",
     "source": "lanacion.com.ar", "mode": "macro", "cat": "economia"},
    {"url": "https://www.clarin.com/rss/economia/", "source": "clarin.com", "mode": "macro", "cat": "economia"},
    {"url": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/propiedades/?outputType=xml",
     "source": "lanacion.com.ar", "mode": "section", "cat": "inmobiliario"},
    {"url": "https://www.constructiondive.com/feeds/news/", "source": "constructiondive.com",
     "mode": "section", "cat": "construccion", "intl": True},
    {"url": "https://www.archdaily.com/rss/", "source": "archdaily.com",
     "mode": "section", "cat": "proyectos", "intl": True},
    {"url": "https://techcrunch.com/feed/", "source": "techcrunch.com",
     "mode": "strict", "cat": "proyectos", "intl": True},
    {"url": "https://www.plataformaarquitectura.cl/cl/rss/", "source": "plataformaarquitectura.cl",
     "mode": "section", "cat": "arquitectura", "intl": True},
    {"url": "https://www.clarin.com/rss/arq/", "source": "clarin.com", "mode": "section", "cat": "arquitectura"},
    {"url": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/politica/?outputType=xml",
     "source": "lanacion.com.ar", "mode": "strict", "cat": "politica"},
    {"url": "https://www.infobae.com/arc/outboundfeeds/rss/category/politica/?outputType=xml",
     "source": "infobae.com", "mode": "strict", "cat": "politica"},
]

CATEGORIES: dict[str, str] = {
    "todas": "Todas",
    "economia": "Economía y macro",
    "inmobiliario": "Inmobiliario",
    "construccion": "Construcción",
    "proyectos": "Grandes proyectos",
    "arquitectura": "Arquitectura",
    "politica": "Política y normativa",
}

# Keywords SIN acentos (el texto se normaliza). Orden de prioridad al categorizar (modo macro).
_CAT_KW: dict[str, list[str]] = {
    "inmobiliario": ["inmobiliari", "propiedad", "departamento", "alquiler", "alquile", "metro cuadrado",
                     "vivienda", " ph ", "compraventa", "escritura", "tasacion", "casa propia",
                     "credito hipotecario", "hipotecari", "metro2", " m2", "cochera", "usado", "valor del m2"],
    "construccion": ["construccion", "obra ", "cemento", "corralon", "hormigon", "materiales para la construccion",
                     "costo de la construccion", "indice de la construccion", "ladrillos", "albanil",
                     "hierro", "acero", "loma negra", "holcim", "ternium", "constructora", "camara de la construccion",
                     "insumos de la construccion", "metro cuadrado de construccion"],
    "proyectos": ["desarrollo inmobiliario", "emprendimiento", "torre ", "barrio privado", "barrio cerrado",
                  "fideicomiso", "megaproyecto", "en pozo", "desarrollador", "complejo residencial",
                  "nuevo proyecto", "lanzo el proyecto", "invertira"],
    "arquitectura": ["arquitectura", "arquitecto", "urbanismo", "diseno", "estudio de arquitectura"],
    "politica": ["ley de alquiler", "normativa urbana", "codigo urbanistico", "plan de vivienda",
                 "procrear", "regulacion inmobiliaria", "subsidio a la vivienda", "obra publica"],
    "economia": ["dolar", "inflacion", "tasa de interes", " tasas ", "plazo fijo", "bcra", "reservas",
                 "riesgo pais", "uva", "fmi", "blanqueo", "tipo de cambio", "actividad economica",
                 "inversion", "credito", "banco"],
}
_CAT_ORDER = ["inmobiliario", "construccion", "proyectos", "arquitectura", "politica", "economia"]

# Modo 'strict' política: SÓLO normativa/política que toca vivienda, propiedad o crédito del rubro
# (no política general). Términos específicos para no traer toda la rosca política.
_POL_KW = ["blanqueo", "impuesto", "subsidio", "tarifa", "vivienda", "alquiler", "hipotecari", "credito",
           "inmobiliari", "obra publica", "desregulacion", "procrear", "banco nacion", "rigi", "reforma",
           "bienes personales", "retenciones", "ley de alquiler", "reservas", "deuda", "fmi", "presupuesto",
           "ganancias", "coparticipacion", "dolar oficial", "baja de impuesto", "plan economico"]

# Modo 'strict' proyectos (TechCrunch global): SÓLO real estate / construcción / proptech (multi-palabra
# para no matchear 'building their own chips' y similares).
_TC_KW = ["real estate", "real-estate", "proptech", "construction tech", "contech", "housing market",
          "mortgage", "home builder", "homebuilder", "prefab", "modular construction", "building materials",
          "commercial property", "smart building", "construction startup", "construction robot",
          "property management", "rental market", "co-living", "coworking space"]

# Temas claramente NO del rubro: si aparecen, descartamos la nota aunque matchee una keyword
# (ej "Jesica Cirio" matcheaba 'dólar' por una causa de lavado). Texto normalizado, sin acentos.
_BLOCK_KW = [
    "futbol", "seleccion argentina", "river plate", "boca juniors", " messi", "espectaculo", "farandula",
    "gran hermano", "masterchef", "horoscopo", "receta", "cirio", "wanda nara", "icardi", "femicidio",
    "crimen", "asesinat", "narcotrafico", "homicidi", "viral", "tenis", "formula 1", " f1 ", "mundial de",
    "pampita", "telenovela", "celebrities", "farandul", "policiales", "detenido por", "escandalo",
]

# Términos de alto impacto para el rubro (suben en el ranking).
_IMPACT_KW = ["credito hipotecario", "hipotecari", "dolar", "inflacion", "blanqueo", "record", "ley ",
              "uva", "tasa", "reservas", "desarrollo inmobiliario", "alquiler", "vivienda", "milei"]


# ── Cache simple en memoria (TTL) ──
_cache: dict[str, tuple[float, Any]] = {}


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


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _domain(url: str | None) -> str:
    if not url:
        return ""
    try:
        net = urlparse(url).netloc.lower()
        return net[4:] if net.startswith("www.") else net
    except Exception:  # noqa: BLE001
        return ""


def _strip(s: str) -> str:
    s = re.sub(r"(?s)<[^>]+>", " ", s or "")
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#039;", "'")
         .replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&#8230;", "…"))
    return re.sub(r"\s+", " ", s).strip()


def _parse_dt(s: str | None) -> datetime | None:
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


_URL_DMY = re.compile(r"/(20\d{2})[/-](\d{1,2})[/-](\d{1,2})(?:[/-]|$|\.)")


def _date_from_url(url: str | None) -> datetime | None:
    if not url:
        return None
    m = _URL_DMY.search(url)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def _categorize(text_norm: str) -> str | None:
    for cat in _CAT_ORDER:
        if any(kw in text_norm for kw in _CAT_KW[cat]):
            return cat
    return None


def _impact(text_norm: str) -> int:
    return sum(1 for kw in _IMPACT_KW if kw in text_norm)


def _score(text_norm: str, dt: datetime, now: datetime) -> float:
    age_h = (now - dt).total_seconds() / 3600.0
    recency = max(0.0, 1.0 - age_h / (24 * 14))     # 0..1 a lo largo de 14 días
    return recency + 0.12 * min(5, _impact(text_norm))


_MRSS = "{http://search.yahoo.com/mrss/}"
_ATOM = "{http://www.w3.org/2005/Atom}"
_DC = "{http://purl.org/dc/elements/1.1/}"
_CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


def _item_image(item: ET.Element) -> str | None:
    enc = item.find("enclosure")
    if enc is not None and enc.get("url"):
        return enc.get("url")
    for tag in (_MRSS + "content", _MRSS + "thumbnail"):
        m = item.find(tag)
        if m is not None and m.get("url"):
            return m.get("url")
    grp = item.find(_MRSS + "group")
    if grp is not None:
        m = grp.find(_MRSS + "content")
        if m is not None and m.get("url"):
            return m.get("url")
    for txt in (item.findtext("description") or "", item.findtext(_CONTENT) or ""):
        mm = re.search(r'<img[^>]+src=["\']([^"\']+)', txt)
        if mm:
            return mm.group(1)
    return None


async def _fetch_rss(feed: dict) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True, headers=_UA) as client:
            resp = await client.get(feed["url"])
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
    except Exception as e:  # noqa: BLE001
        logger.warning("NewsLive RSS %s falló — %s", feed["url"], e)
        return []

    out: list[dict] = []
    elems = root.findall(".//item")
    is_atom = False
    if not elems:
        elems = root.findall(f".//{_ATOM}entry")
        is_atom = True
    for it in elems:
        if is_atom:
            title = (it.findtext(_ATOM + "title") or "").strip()
            link_el = it.find(_ATOM + "link")
            url = (link_el.get("href") if link_el is not None else "") or ""
            desc = it.findtext(_ATOM + "summary") or it.findtext(_ATOM + "content") or ""
            pd = it.findtext(_ATOM + "published") or it.findtext(_ATOM + "updated")
            img = None
        else:
            title = (it.findtext("title") or "").strip()
            url = (it.findtext("link") or "").strip()
            desc = it.findtext("description") or ""
            pd = it.findtext("pubDate") or it.findtext(_DC + "date")
            img = _item_image(it)
        if not title or not url:
            continue
        out.append({
            "title": re.sub(r"\s+", " ", title).strip()[:240], "url": url, "snippet": _strip(desc)[:400],
            "published_date": pd, "image": img, "source": feed["source"],
            "mode": feed.get("mode", "section"), "cat": feed.get("cat", "economia"),
            "intl": feed.get("intl", False),
        })
    return out


async def _fetch_all_rss(refresh: bool = False) -> list[dict]:
    if not refresh:
        cached = _cache_get("raw_rss")
        if cached is not None:
            return cached
    results = await asyncio.gather(*[_fetch_rss(f) for f in RSS_FEEDS])
    raw = [it for r in results for it in r]
    _cache_set("raw_rss", raw, _RAW_TTL)
    return raw


async def _ranked_items(category: str, refresh: bool = False) -> list[dict]:
    cache_key = f"ranked::{category}"
    if not refresh:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    raw = await _fetch_all_rss(refresh)
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=_MAX_AGE_DAYS)
    seen: set[str] = set()
    items: list[dict] = []
    for it in raw:
        url = it["url"]
        if url in seen:
            continue
        dt = _parse_dt(it.get("published_date")) or _date_from_url(url)
        if dt is None or dt < cutoff:
            continue
        text_norm = _norm(it["title"] + " " + (it.get("snippet") or ""))
        if any(b in text_norm for b in _BLOCK_KW):
            continue  # tema fuera del rubro (espectáculos/policiales/deportes)
        mode = it.get("mode", "section")
        if mode == "macro":
            cat = _categorize(text_norm) or "economia"   # distribuye por keyword; al menos economía
        elif mode == "strict":
            fcat = it.get("cat", "economia")
            kws = _POL_KW if fcat == "politica" else _TC_KW
            if not any(k in text_norm for k in kws):
                continue   # feed general que no toca el rubro → fuera
            cat = fcat
        else:  # section → la categoría del feed
            cat = it.get("cat", "economia")
        if category != "todas" and cat != category:
            continue
        seen.add(url)
        items.append({
            "title": it["title"], "url": url, "source": it["source"], "category": cat,
            "published_date": dt.isoformat(), "snippet": it.get("snippet") or "",
            "image": it.get("image"), "intl": it.get("intl", False),
            "_score": _score(text_norm, dt, now),
        })
    items.sort(key=lambda x: x["_score"], reverse=True)
    for x in items:
        x.pop("_score", None)
    _cache_set(cache_key, items, _FEED_TTL)
    return items


# ── Imagen: garantizar una foto por card (og:image del artículo si el RSS no la trae) ──

async def _fetch_og_image(url: str) -> str | None:
    cache_key = f"og::{url}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached or None
    img = None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True, headers=_UA) as client:
            resp = await client.get(url)
            html = resp.text[:60000]  # el og:image vive en el <head>, al principio
        for pat in (r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)'):
            m = re.search(pat, html, re.I)
            if m:
                img = m.group(1)
                break
    except Exception as e:  # noqa: BLE001 — sin imagen no rompe nada
        logger.warning("NewsLive: og:image falló %s — %s", url, e)
    _cache_set(cache_key, img or "", _DIGEST_TTL)
    return img


# Imagen temática (foto REAL de Flickr por keyword) cuando la nota no trae imagen ni og:image.
# Así toda card tiene una imagen realista que tiene que ver con el tema, no un placeholder.
_TOPIC_IMG = {
    "economia": "argentina,money,finance",
    "inmobiliario": "house,realestate,home",
    "construccion": "construction,building,site",
    "proyectos": "architecture,skyscraper,building",
    "arquitectura": "architecture,design,building",
    "politica": "government,argentina,building",
}
_TOPIC_OVERRIDE = [
    ("dolar", "money,dollar,currency"), ("hipotec", "house,keys,mortgage"),
    ("credito", "house,keys,bank"), ("alquiler", "apartment,rent"),
    ("obra", "construction,site"), ("cemento", "construction,concrete"),
    ("hierro", "steel,construction"), ("torre", "skyscraper,tower"),
    ("barrio", "neighborhood,houses"), ("inversion", "investment,finance"),
    ("inflacion", "market,prices"), ("plazo fijo", "bank,savings"),
    ("banco", "bank,finance"), ("escritura", "documents,house"),
]


def _topic_image(it: dict) -> str:
    tn = _norm(it.get("title", ""))
    kw = _TOPIC_IMG.get(it.get("category", ""), "realestate,building")
    for term, ikw in _TOPIC_OVERRIDE:
        if term in tn:
            kw = ikw
            break
    lock = zlib.crc32(it["url"].encode()) % 100000  # estable por nota
    return f"https://loremflickr.com/400/240/{kw}?lock={lock}"


async def _ensure_images(items: list[dict]) -> None:
    """Toda card termina con imagen: la del RSS, o el og:image del artículo, o —si no hay—
    una foto REAL del tema (Flickr por keyword). Nunca queda sin imagen."""
    missing = [it for it in items if not it.get("image")]
    if not missing:
        return
    imgs = await asyncio.gather(*[_fetch_og_image(it["url"]) for it in missing])
    for it, img in zip(missing, imgs, strict=False):
        it["image"] = img or _topic_image(it)


# ── Traducción de títulos/bajadas de noticias internacionales al español ──

_TR_TOOL = {
    "name": "traducir",
    "description": "Traduce al español los títulos y bajadas de noticias.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "i": {"type": "integer"},
                        "titulo": {"type": "string"},
                        "bajada": {"type": "string"},
                    },
                    "required": ["i", "titulo"],
                },
            },
        },
        "required": ["items"],
    },
}
_TR_SYSTEM = (
    "Traducís al español rioplatense, claro y natural, títulos y bajadas de noticias de real estate, "
    "construcción y arquitectura. Mantené el sentido, los nombres propios y las cifras. No agregues "
    "comentarios. Devolvés la traducción por la tool, respetando el índice 'i' de cada item."
)


async def _translate_intl(items: list[dict]) -> None:
    """Traduce in-place los items internacionales al español (batch, cacheado por URL)."""
    need: list[dict] = []
    for it in items:
        if not it.get("intl"):
            continue
        cached = _cache_get(f"tr::{it['url']}")
        if cached:
            it["title"] = cached["t"]
            it["snippet"] = cached.get("s", it.get("snippet", ""))
        else:
            need.append(it)
    if not need:
        return
    payload = [{"i": i, "titulo": it["title"], "bajada": (it.get("snippet") or "")[:240]}
               for i, it in enumerate(need)]
    try:
        from services.anthropic_service import get_client
        client = get_client()
        resp = await client.messages.create(
            model=settings.ANTHROPIC_MODEL_FAST, max_tokens=2000, system=_TR_SYSTEM,
            tools=[_TR_TOOL], tool_choice={"type": "tool", "name": "traducir"},
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        out: dict = {}
        for b in resp.content:
            if getattr(b, "type", None) == "tool_use":
                out = dict(b.input)
                break
        for r in (out.get("items") or []):
            i = r.get("i")
            if isinstance(i, int) and 0 <= i < len(need):
                it = need[i]
                it["title"] = (r.get("titulo") or it["title"]).strip()[:240]
                it["snippet"] = (r.get("bajada") or it.get("snippet", "")).strip()[:400]
                _cache_set(f"tr::{it['url']}", {"t": it["title"], "s": it["snippet"]}, _DIGEST_TTL)
    except Exception as e:  # noqa: BLE001 — si falla, queda en inglés (no rompe el feed)
        logger.warning("NewsLive: traducción falló — %s", e)


async def fetch_feed(category: str = "todas", page: int = 1, per_page: int = 12,
                     refresh: bool = False) -> dict:
    """Feed paginado y rankeado (recencia + impacto). Lo mejor/más fresco primero;
    al paginar (cargar más) aparece lo más viejo o menos relevante. Las notas
    internacionales se traducen al español."""
    category = category if category in CATEGORIES else "todas"
    page = max(1, page)
    per_page = max(1, min(per_page, 40))
    full = await _ranked_items(category, refresh)
    start, end = (page - 1) * per_page, (page - 1) * per_page + per_page
    page_items = full[start:end]
    await asyncio.gather(_translate_intl(page_items), _ensure_images(page_items))
    return {
        "category": category,
        "items": page_items,
        "page": page,
        "per_page": per_page,
        "total": len(full),
        "has_more": end < len(full),
        "fetched_at": datetime.now(UTC).isoformat(),
    }


# ── Lector: digest transformativo con IA ──

_DIGEST_TOOL = {
    "name": "armar_digest_noticia",
    "description": "Arma un resumen periodístico propio (transformativo) de una noticia para real estate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "lead": {"type": "string", "description": "1-2 frases gancho que resumen la noticia."},
            "puntos_clave": {"type": "array", "items": {"type": "string"},
                             "description": "3-6 bullets con la info relevante, en palabras propias."},
            "impacto_real_estate": {"type": "string",
                                    "description": "2-4 frases: por qué le importa a alguien del rubro AR."},
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
        # Guard anti-SSRF: valida esquema/host, bloquea IPs internas y revalida
        # cada redirect. Una URL no permitida lanza UnsafeUrlError y cae al except.
        from core.safe_fetch import safe_get
        resp = await safe_get(url, timeout=_TIMEOUT, headers=_UA)
        resp.raise_for_status()
        html = resp.text
        og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        image = og.group(1) if og else None
        html = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&#039;", "'").replace("&quot;", '"'))
        text = re.sub(r"\s+", " ", text).strip()
        return image, text[:9000]
    except Exception as e:  # noqa: BLE001
        logger.warning("NewsLive: no se pudo bajar %s — %s", url, e)
        return None, None


async def make_digest(url: str, title: str = "", snippet: str = "",
                      source: str = "", category: str = "", image: str = "") -> dict:
    cache_key = f"digest::{url}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    og_image, text = await _fetch_article_text(url)
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
        except Exception as e:  # noqa: BLE001
            logger.warning("NewsLive: digest IA falló — %s", e)

    if not digest:
        digest = {"lead": snippet or title, "puntos_clave": [], "impacto_real_estate": ""}

    payload = {
        "title": title, "url": url, "source": source or _domain(url), "category": category,
        "image_url": og_image or (image or None),
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
