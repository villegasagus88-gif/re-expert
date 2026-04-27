"""
News endpoint: GET /api/news.

Lee noticias del bucket Supabase Storage `knowledge/noticias/` y las
devuelve paginadas y ordenadas por fecha desc. La autenticación se
exige (mismas credenciales que el resto de la app) para que no sea
público; el contenido es curado y se sirve únicamente a usuarios
autenticados.
"""
from api.schemas.news import NewsResponse
from core.auth import get_current_user
from fastapi import APIRouter, Depends, Query
from models.user import User
from services.news_service import list_news

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get(
    "",
    response_model=NewsResponse,
    summary="Listar noticias del knowledge base",
    responses={
        401: {"description": "Token inválido o ausente"},
    },
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
