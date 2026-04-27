"""
NewsService - lee noticias del bucket Supabase Storage `knowledge/noticias/`.

Convención de los archivos `.md`:

    ---
    title: El BCRA reduce la tasa de política monetaria al 29%
    date: 2026-04-25
    summary: La decisión del Banco Central de bajar 200 puntos genera...
    category: macro
    source: Ámbito Financiero
    impact: ↑ Impacto positivo en financiación y demanda
    ---

    # Cuerpo opcional en Markdown

Si no hay frontmatter:
- el `slug` se deriva del filename (sin extensión).
- el `title` toma el primer H1 (`# ...`) del cuerpo, o el slug humanizado.
- la `date` se intenta parsear del prefijo `YYYY-MM-DD-...` del filename.
- el `summary` toma el primer párrafo no-vacío del cuerpo (truncado a 280 chars).
"""
import asyncio
import logging
import re
from datetime import date, datetime

from api.schemas.news import NewsItem, NewsResponse
from services.knowledge_storage import knowledge_storage

logger = logging.getLogger(__name__)

NEWS_FOLDER = "noticias"
SUMMARY_MAX_LEN = 280

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[-_ ]?(.*)$")
_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """
    Parser minimalista de frontmatter YAML (key: value por línea, sin nesting).
    Devuelve (metadata, body). Si no hay frontmatter, (vacío, texto entero).
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta_raw, body = m.group(1), m.group(2)
    meta: dict[str, str] = {}
    for line in meta_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, body


def _humanize_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").strip().capitalize()


def _first_paragraph(body: str, max_len: int = SUMMARY_MAX_LEN) -> str:
    for raw in body.split("\n\n"):
        p = raw.strip()
        if not p or p.startswith("#"):
            continue
        # Quitar markdown básico para que el resumen se lea limpio.
        p = re.sub(r"[*_`>]+", "", p)
        if len(p) > max_len:
            p = p[: max_len - 1].rstrip() + "…"
        return p
    return ""


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _build_item(filename: str, content: str) -> NewsItem | None:
    """
    Construye un NewsItem a partir de un .md. Devuelve None si el archivo
    no parece una noticia válida (vacío, sin título derivable).
    """
    if not filename.lower().endswith(".md"):
        return None
    slug = filename.rsplit("/", 1)[-1]
    slug = slug[:-3]  # drop .md

    meta, body = _parse_frontmatter(content)

    # Date: prioridad frontmatter > prefijo del filename.
    fm_date = _parse_date(meta.get("date"))
    if fm_date is None:
        prefix = _DATE_PREFIX_RE.match(slug)
        if prefix:
            fm_date = _parse_date(prefix.group(1))
            slug_human = prefix.group(2) or slug
        else:
            slug_human = slug
    else:
        slug_human = slug

    # Title: frontmatter > primer H1 > slug humanizado.
    title = meta.get("title")
    if not title:
        h1 = _H1_RE.search(body)
        title = h1.group(1).strip() if h1 else _humanize_slug(slug_human)

    summary = meta.get("summary") or _first_paragraph(body)

    return NewsItem(
        slug=slug,
        title=title,
        date=fm_date,
        summary=summary,
        category=(meta.get("category") or None),
        source=(meta.get("source") or None),
        impact=(meta.get("impact") or None),
    )


async def _load_one(path: str, name: str) -> NewsItem | None:
    try:
        text = await asyncio.wait_for(
            knowledge_storage.get_text_content(path), timeout=5
        )
    except Exception as e:
        logger.warning("No se pudo leer noticia %s: %s", path, e)
        return None
    return _build_item(name, text)


async def list_news(
    page: int = 1,
    per_page: int = 10,
    category: str | None = None,
) -> NewsResponse:
    """
    Lista noticias del bucket, ordenadas por fecha desc, con paginación.

    Args:
        page: 1-indexed.
        per_page: cap a 50 para no devolver respuestas gigantes.
        category: filtra por categoría (case-insensitive). None = todas.
    """
    page = max(1, page)
    per_page = max(1, min(per_page, 50))

    try:
        files = await asyncio.wait_for(
            knowledge_storage.list_files(NEWS_FOLDER), timeout=5
        )
    except Exception as e:
        logger.warning("No se pudo listar noticias: %s", e)
        files = []

    md_files = [f for f in files if f["name"].lower().endswith(".md")]

    items_raw = await asyncio.gather(
        *[_load_one(f["path"], f["name"]) for f in md_files]
    )
    items: list[NewsItem] = [i for i in items_raw if i is not None]

    if category:
        cat = category.lower()
        items = [i for i in items if (i.category or "").lower() == cat]

    # Sort: fecha desc; los que no tienen fecha al final.
    items.sort(key=lambda i: (i.date is None, -(i.date.toordinal() if i.date else 0)))

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return NewsResponse(
        items=page_items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=end < total,
    )
