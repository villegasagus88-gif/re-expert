"""
Billing endpoints — canonical for plan / subscription operations.

GET  /api/billing/status   — plan + Stripe subscription details + invoices
POST /api/billing/checkout — create Stripe-hosted Checkout for the Pro plan
POST /api/billing/portal   — open Stripe Billing Portal (manage / cancel)

Stripe calls in /status are best-effort: if STRIPE_SECRET_KEY is not
configured or the user has no stripe_customer_id, /status returns plan-only
info without raising. /checkout and /portal raise 503 if Stripe is missing.
"""
import asyncio
import logging
from datetime import UTC, datetime
from functools import partial

import stripe
from config.settings import settings
from core.auth import get_current_user
from core.plan_gate import has_access
from fastapi import APIRouter, Depends
from models.user import User
from services.stripe_service import (
    create_billing_portal_session,
    create_pro_checkout_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


async def _run_stripe(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


def _ts(unix_ts: int | None) -> str | None:
    if not unix_ts:
        return None
    return datetime.fromtimestamp(unix_ts, tz=UTC).isoformat()


@router.get("/status", summary="Estado de cuenta y suscripción")
async def billing_status(user: User = Depends(get_current_user)):
    result: dict = {
        "plan": user.plan,
        "is_pro": user.plan == "pro",
        "is_trial": user.plan == "trial",
        "has_access": has_access(user),
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "email": user.email,
        "full_name": user.full_name,
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
        "has_customer": bool(user.stripe_customer_id),
        "subscription": None,
        "invoices": [],
    }

    if not (user.plan == "pro" and user.stripe_customer_id and settings.STRIPE_SECRET_KEY):
        return result

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Active subscription (most recent first)
    try:
        subs = await _run_stripe(
            stripe.Subscription.list,
            customer=user.stripe_customer_id,
            limit=1,
        )
        if subs.data:
            sub = subs.data[0]
            result["subscription"] = {
                "status": sub.status,
                "current_period_end": _ts(sub.current_period_end),
                "current_period_start": _ts(sub.current_period_start),
                "cancel_at_period_end": sub.cancel_at_period_end,
                "cancel_at": _ts(getattr(sub, "cancel_at", None)),
            }
    except Exception as exc:
        logger.warning("billing_status: error fetching subscription — %s", exc)

    # Invoice history (up to 12 most recent)
    try:
        inv_list = await _run_stripe(
            stripe.Invoice.list,
            customer=user.stripe_customer_id,
            limit=12,
        )
        result["invoices"] = [
            {
                "id": inv.id,
                "amount_paid": inv.amount_paid / 100,
                "currency": inv.currency.upper(),
                "status": inv.status,
                "created": _ts(inv.created),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": getattr(inv, "hosted_invoice_url", None),
                "description": inv.description or "RE Expert Pro — Suscripción mensual",
                "period_start": _ts(inv.period_start),
                "period_end": _ts(inv.period_end),
            }
            for inv in inv_list.data
        ]
    except Exception as exc:
        logger.warning("billing_status: error fetching invoices — %s", exc)

    return result


@router.post(
    "/checkout",
    summary="Crear sesión de checkout de Stripe para el plan Pro",
    responses={
        400: {"description": "Usuario ya es Pro"},
        401: {"description": "Token inválido"},
        502: {"description": "Error en Stripe"},
        503: {"description": "Stripe no configurado"},
    },
)
async def billing_checkout(user: User = Depends(get_current_user)):
    """Returns `{url, session_id}` — redirigir el browser a `url`."""
    return await create_pro_checkout_session(user)


@router.post(
    "/portal",
    summary="Abrir el portal de facturación de Stripe",
    responses={
        400: {"description": "Usuario no Pro o sin customer asociado"},
        502: {"description": "Error en Stripe"},
        503: {"description": "Stripe no configurado"},
    },
)
async def billing_portal(user: User = Depends(get_current_user)):
    return await create_billing_portal_session(user)
