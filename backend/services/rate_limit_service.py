"""
Per-user rate limiting.

Counts the user's recent messages in the DB (rolling windows: 1h and 24h)
and enforces per-plan caps. On 429, the HTTP response carries a Retry-After
header computed from the oldest message in the exceeded window.

Plan limits:
    free: 5 msgs/hour, 20 msgs/day
    pro:  50 msgs/hour, 200 msgs/day

Response headers (on success AND on 429):
    X-RateLimit-Limit-Hour       total allowed per hour for this plan
    X-RateLimit-Remaining-Hour   how many remain in the current window
    X-RateLimit-Reset-Hour       unix timestamp when the hour window resets
    X-RateLimit-Limit-Day        total allowed per day
    X-RateLimit-Remaining-Day    how many remain today
    X-RateLimit-Reset-Day        unix timestamp when the day window resets
"""
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from models.conversation import Conversation
from models.message import Message
from models.user import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {"per_hour": 5, "per_day": 20},
    "pro": {"per_hour": 50, "per_day": 200},
}


def _limits_for(plan: str) -> dict[str, int]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


async def _oldest_created_at(
    db: AsyncSession, user_id, since: datetime
) -> datetime | None:
    """Earliest user-message timestamp within [since, now] for this user."""
    result = await db.execute(
        select(Message.created_at)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user_id,
            Message.role == "user",
            Message.created_at >= since,
        )
        .order_by(Message.created_at.asc())
        .limit(1)
    )
    return result.scalar()


async def check_user_rate_limit(db: AsyncSession, user: User) -> dict[str, str]:
    """
    Raises HTTPException(429) if the user has exceeded their plan's
    per-hour or per-day limit. Otherwise returns a dict of
    X-RateLimit-* headers to attach to the response.
    """
    limits = _limits_for(user.plan)
    now = datetime.now(UTC)
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    base_count_query = (
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user.id,
            Message.role == "user",
        )
    )

    hour_count = (
        await db.execute(base_count_query.where(Message.created_at >= hour_ago))
    ).scalar() or 0
    day_count = (
        await db.execute(base_count_query.where(Message.created_at >= day_ago))
    ).scalar() or 0

    remaining_hour = max(0, limits["per_hour"] - hour_count)
    remaining_day = max(0, limits["per_day"] - day_count)

    # Reset timestamps (unix epoch seconds): when the OLDEST message in the
    # window rolls out, a slot frees up. If no messages in the window, use
    # "now + window" as a conservative placeholder.
    hour_reset_dt = (
        await _oldest_created_at(db, user.id, hour_ago)
    ) or now
    day_reset_dt = (
        await _oldest_created_at(db, user.id, day_ago)
    ) or now
    hour_reset_ts = int((hour_reset_dt + timedelta(hours=1)).timestamp())
    day_reset_ts = int((day_reset_dt + timedelta(days=1)).timestamp())

    headers = {
        "X-RateLimit-Limit-Hour": str(limits["per_hour"]),
        "X-RateLimit-Remaining-Hour": str(remaining_hour),
        "X-RateLimit-Reset-Hour": str(hour_reset_ts),
        "X-RateLimit-Limit-Day": str(limits["per_day"]),
        "X-RateLimit-Remaining-Day": str(remaining_day),
        "X-RateLimit-Reset-Day": str(day_reset_ts),
    }

    if hour_count >= limits["per_hour"]:
        retry_after = max(1, hour_reset_ts - int(now.timestamp()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Límite horario excedido: {limits['per_hour']} msgs/hora. "
                f"Plan actual: {user.plan}."
            ),
            headers={**headers, "Retry-After": str(retry_after)},
        )
    if day_count >= limits["per_day"]:
        retry_after = max(1, day_reset_ts - int(now.timestamp()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Límite diario excedido: {limits['per_day']} msgs/día. "
                f"Plan actual: {user.plan}."
            ),
            headers={**headers, "Retry-After": str(retry_after)},
        )

    return headers
