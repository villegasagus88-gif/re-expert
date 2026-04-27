"""
Schemas para GET /api/news.

Las noticias viven como archivos Markdown dentro de `knowledge/noticias/`.
Cada archivo puede llevar frontmatter YAML con metadata (title/date/summary/
category/source/impact). Lo que no esté en frontmatter se intenta deducir
del filename y del primer header del cuerpo.
"""
from datetime import date

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """Una noticia individual lista para renderizar como card."""

    slug: str  # filename sin extensión (estable, sirve como id)
    title: str
    date: date | None = None
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
