"""
Token usage logging + cost calculation.

Pricing is per 1M tokens, in USD. Update PRICING as Anthropic publishes new
prices or we start using additional models. Unknown models fall back to the
default Sonnet pricing (conservative: same as the configured default model).
"""
from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from models.token_usage import TokenUsage
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Precio por 1M tokens (USD). Fuente: https://www.anthropic.com/pricing
PRICING: dict[str, dict[str, Decimal]] = {
    # Claude Sonnet 4.x family
    "claude-sonnet-4-6-20250514": {
        "input": Decimal("3.00"),
        "output": Decimal("15.00"),
    },
    "claude-sonnet-4-5": {
        "input": Decimal("3.00"),
        "output": Decimal("15.00"),
    },
    # Claude Opus 4.x family
    "claude-opus-4-6": {
        "input": Decimal("15.00"),
        "output": Decimal("75.00"),
    },
    # Claude Haiku 4.x family
    "claude-haiku-4-5-20251001": {
        "input": Decimal("1.00"),
        "output": Decimal("5.00"),
    },
}

# Fallback si el modelo no está en PRICING (usamos Sonnet como conservador).
DEFAULT_PRICING = PRICING["claude-sonnet-4-6-20250514"]

_ONE_MILLION = Decimal("1000000")
_CENT_PRECISION = Decimal("0.000001")  # 6 decimales = $0.000001


def calculate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """
    Calcula el costo en USD de una request dada.

    Devuelve un Decimal con 6 decimales de precisión (suficiente para
    llamadas chicas; una request de 100 tokens output cuesta $0.0015).
    """
    pricing = PRICING.get(model, DEFAULT_PRICING)
    input_cost = (Decimal(input_tokens) * pricing["input"]) / _ONE_MILLION
    output_cost = (Decimal(output_tokens) * pricing["output"]) / _ONE_MILLION
    total = input_cost + output_cost
    return total.quantize(_CENT_PRECISION, rounding=ROUND_HALF_UP)


async def log_token_usage(
    db: AsyncSession,
    *,
    user_id: UUID,
    conversation_id: UUID | None,
    message_id: UUID | None,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> TokenUsage | None:
    """
    Persist a TokenUsage row. Errors are logged and swallowed so they never
    break the chat response — usage logging is best-effort.
    """
    try:
        total = input_tokens + output_tokens
        cost = calculate_cost_usd(model, input_tokens, output_tokens)
        row = TokenUsage(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            cost_usd=cost,
        )
        db.add(row)
        await db.commit()
        return row
    except Exception as e:
        logger.exception("Error guardando token_usage: %s", e)
        try:
            await db.rollback()
        except Exception:
            pass
        return None
