"""
Usage endpoint: GET /api/usage.

Devuelve el consumo de tokens y costo en USD del usuario autenticado,
agregado por ventanas temporales (últimas 24h, últimos 30 días, histórico).
"""
from datetime import UTC, datetime, timedelta

from core.auth import get_current_user
from fastapi import APIRouter, Depends
from models.base import get_db
from models.token_usage import TokenUsage
from models.user import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/usage", tags=["usage"])


async def _aggregate(
    db: AsyncSession,
    user_id,
    since: datetime | None,
) -> dict:
    """Aggregate token_usage rows for user_id, optionally filtered by since."""
    stmt = select(
        func.coalesce(func.sum(TokenUsage.input_tokens), 0),
        func.coalesce(func.sum(TokenUsage.output_tokens), 0),
        func.coalesce(func.sum(TokenUsage.total_tokens), 0),
        func.coalesce(func.sum(TokenUsage.cost_usd), 0),
        func.count(TokenUsage.id),
    ).where(TokenUsage.user_id == user_id)
    if since is not None:
        stmt = stmt.where(TokenUsage.created_at >= since)

    result = await db.execute(stmt)
    row = result.one()
    input_tokens, output_tokens, total_tokens, cost_usd, requests = row

    return {
        "requests": int(requests),
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "total_tokens": int(total_tokens),
        "cost_usd": float(cost_usd),
    }


@router.get(
    "",
    summary="Consumo de tokens y costo del usuario actual",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)
    last_30d = now - timedelta(days=30)

    return {
        "user_id": str(current_user.id),
        "plan": current_user.plan,
        "last_24h": await _aggregate(db, current_user.id, last_24h),
        "last_30d": await _aggregate(db, current_user.id, last_30d),
        "all_time": await _aggregate(db, current_user.id, None),
    }
