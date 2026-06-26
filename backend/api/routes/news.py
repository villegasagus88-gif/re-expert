"""
News endpoints.

Tres fuentes de noticias, cada una con su tab en el frontend:

  GET /api/news              → "Últimas" (feed cronológico desde
                                Supabase Storage bucket knowledge/noticias/).
                                Real-time, low-churn pero actualizable
                                sin redeploy.
  GET /api/news/destacadas   → "Destacadas" (hero + cards curadas).
                                Servido desde backend/data/news/destacadas.json.
                                Cambia con releases (curación editorial).
  GET /api/news/opinion      → "Opinión" (testimonios de analistas).
                                Servido desde backend/data/news/opinion.json.
                                Curación trimestral típica.

La separación es por TIPO DE CONTENIDO: "Últimas" requiere refresco
frecuente y muchos ítems → bucket. "Destacadas" y "Opinión" son
contenido editorial fijo → JSON versionado.
"""
import json
from functools import lru_cache
from pathlib import Path

from api.schemas.news import NewsResponse, OpinionResponse, SpotlightResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.user import User
from services.news_live import CATEGORIES, fetch_feed, make_digest
from services.news_service import list_news

router = APIRouter(prefix="/api/news", tags=["news"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "news"
_DESTACADAS_PATH = _DATA_DIR / "destacadas.json"
_OPINION_PATH = _DATA_DIR / "opinion.json"


@lru_cache(maxsize=2)
def _load_json(path: str) -> dict:
    """Cache en memoria — el contenido es estático entre deploys."""
    p = Path(path)
    if not p.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Archivo de noticias no disponible: {p.name}",
        )
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "",
    response_model=NewsResponse,
    summary="Tab 'Últimas': feed cronológico desde Supabase Storage",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def get_news(
    page: int = Query(1, ge=1, description="Página (1-indexed)"),
    per_page: int = Query(10, ge=1, le=50, description="Items por página (máx 50)"),
    category: str | None = Query(
        None, description="Filtrar por categoría (macro/mercado/costos/...)"
    ),
    _user: User = Depends(get_current_user),
) -> NewsResponse:
    return await list_news(page=page, per_page=per_page, category=category)


@router.get(
    "/destacadas",
    response_model=SpotlightResponse,
    summary="Tab 'Destacadas': hero + cards + feed curados editorialmente",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de destacadas no disponible"},
    },
)
async def get_destacadas(_user: User = Depends(get_current_user)) -> SpotlightResponse:
    data = _load_json(str(_DESTACADAS_PATH))
    return SpotlightResponse(**data)


@router.get(
    "/opinion",
    response_model=OpinionResponse,
    summary="Tab 'Opinión': testimonios de analistas y referentes",
    responses={
        401: {"description": "Token inválido o ausente"},
        503: {"description": "Archivo de opinión no disponible"},
    },
)
async def get_opinion(_user: User = Depends(get_current_user)) -> OpinionResponse:
    data = _load_json(str(_OPINION_PATH))
    return OpinionResponse(**data)


# ── Noticias EN VIVO (Tavily) + lector con digest IA ──

@router.get(
    "/categories",
    summary="Categorías disponibles del feed en vivo",
)
async def get_news_categories(_user: User = Depends(get_current_user)) -> dict:
    return {"categories": [{"key": k, "label": v["label"]} for k, v in CATEGORIES.items()]}


@router.get(
    "/live",
    summary="Feed de noticias reales en vivo del rubro (Tavily), por categoría",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def get_news_live(
    category: str = Query("todas", max_length=24, description="Categoría del feed"),
    refresh: bool = Query(False, description="Bypassa el cache y trae noticias nuevas"),
    _user: User = Depends(get_current_user),
) -> dict:
    return await fetch_feed(category=category, refresh=refresh)


@router.get(
    "/digest",
    summary="Lector: digest IA (transformativo) de una nota, para leer dentro de la plataforma",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def get_news_digest(
    url: str = Query(..., max_length=2000, description="URL de la nota original"),
    title: str = Query("", max_length=300),
    source: str = Query("", max_length=120),
    category: str = Query("", max_length=24),
    snippet: str = Query("", max_length=600),
    _user: User = Depends(get_current_user),
) -> dict:
    return await make_digest(url=url, title=title, snippet=snippet, source=source, category=category)
