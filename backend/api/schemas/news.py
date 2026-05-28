"""
Schemas para GET /api/news.

Las noticias viven como archivos Markdown dentro de `knowledge/noticias/`.
Cada archivo puede llevar frontmatter YAML con metadata (title/date/summary/
category/source/impact). Lo que no esté en frontmatter se intenta deducir
del filename y del primer header del cuerpo.
"""
from datetime import date as _date

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """Una noticia individual lista para renderizar como card."""

    slug: str  # filename sin extensión (estable, sirve como id)
    title: str
    date: _date | None = None
    summary: str = ""
    category: str | None = None  # macro | mercado | costos | financiacion | regulacion | ...
    source: str | None = None
    impact: str | None = None  # texto libre tipo "↑ Impacto positivo en..."


class NewsResponse(BaseModel):
    """Página de noticias devuelta por GET /api/news."""

    items: list[NewsItem]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    has_more: bool


# ── Tab "Destacadas" ──────────────────────────────────────────────────
# Contenido editorial curado. Estructura mucho más rica que el feed
# cronológico de Últimas (hero cards con excerpt + impact + chips).

class NewsTakeaway(BaseModel):
    """Bloque de 'lectura rápida' arriba de la tab."""
    icon: str = "⚡"
    title: str
    text: str


class NewsCategoryChip(BaseModel):
    """Chip de filtro por categoría (mostrar/ocultar cards por dataset.cat)."""
    id: str  # ej. "macro", "todas"
    label: str


class NewsHeroCard(BaseModel):
    """Card grande en la sección 'hero'. La primera suele ir featured
    (más grande, con excerpt)."""
    category: str
    title: str
    excerpt: str = ""
    impact: str = ""
    impact_kind: str = "positive"  # positive | high | warning | negative
    source: str = ""
    when: str = ""  # texto libre tipo "Hoy, 09:45" o "Ayer"
    featured: bool = False


class NewsFeedItem(BaseModel):
    """Item numerado del feed 'También importante' (debajo del hero)."""
    category: str
    title: str
    subtitle: str = ""
    meta: str = ""  # ej. "Infobae · Hoy, 11:30"


class SpotlightResponse(BaseModel):
    """GET /api/news/destacadas."""
    updated_at: str
    takeaway: NewsTakeaway
    categories: list[NewsCategoryChip]
    hero: list[NewsHeroCard]
    feed: list[NewsFeedItem]


# ── Tab "Opinión" ─────────────────────────────────────────────────────
# Cards con testimonios de analistas/referentes. Layout distinto al
# del feed: avatar + name + role + quote + date.

class OpinionCard(BaseModel):
    avatar_initials: str = Field(..., min_length=1, max_length=4)
    avatar_class: str = "av1"  # av1/av2/av3/av4 para colorear
    name: str
    role: str = ""
    quote: str
    date: str = ""


class OpinionResponse(BaseModel):
    """GET /api/news/opinion."""
    updated_at: str
    takeaway: NewsTakeaway
    cards: list[OpinionCard]
