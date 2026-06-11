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
from fastapi import APIRouter, Depends, Header, Request
from models.base import get_db
from models.user import User
from services.mercadopago_service import (
    cancel_subscription as mp_cancel_subscription,
)
from services.mercadopago_service import (
    handle_webhook as mp_handle_webhook,
)
from services.mercadopago_service import (
    mp_enabled,
    mp_public_config,
    start_subscription_checkout,
)
from services.stripe_service import create_billing_portal_session
from sqlalchemy.ext.asyncio import AsyncSession

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
        "mp_enabled": mp_enabled(),
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
    summary="Crear checkout de suscripción (Mercado Pago, o Stripe legacy)",
    responses={
        400: {"description": "Usuario ya tiene suscripción activa"},
        401: {"description": "Token inválido"},
        502: {"description": "Error en el proveedor de pagos"},
        503: {"description": "Proveedor de pagos no configurado"},
    },
)
async def billing_checkout(user: User = Depends(get_current_user)):
    """
    Devuelve `{url, ...}` — redirigir el browser a `url`.

    Despacha al proveedor activo: Mercado Pago si está configurado
    (MP_ACCESS_TOKEN + MP_PLAN_ID), si no cae a Stripe (legacy).
    """
    return await start_subscription_checkout(user)


# ── Mercado Pago ─────────────────────────────────────────────────────────────
@router.get(
    "/mp/config",
    summary="Config pública de Mercado Pago (enabled + public_key)",
)
async def mp_config():
    """Público: `{enabled, public_key}`. La public_key es pública por diseño."""
    return mp_public_config()


@router.post(
    "/mp/cancel",
    summary="Cancelar la suscripción de Mercado Pago (botón de baja)",
    responses={
        400: {"description": "Sin suscripción activa"},
        404: {"description": "MP no tiene una suscripción viva para este usuario"},
        502: {"description": "Error en Mercado Pago"},
        503: {"description": "MP no configurado"},
    },
)
async def mp_cancel(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Baja online (Ley 24.240): cancela el preapproval y corta el acceso."""
    return await mp_cancel_subscription(db, user)


@router.post(
    "/mp/webhook",
    summary="Webhook de Mercado Pago (sin auth JWT — se valida por firma HMAC)",
    status_code=200,
    responses={
        400: {"description": "Firma inválida"},
        503: {"description": "MP no configurado / falta MP_WEBHOOK_SECRET en prod"},
    },
)
async def mp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str | None = Header(default=None, alias="x-signature"),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
):
    """
    Recibe notificaciones de MP. El `data.id` y `type` vienen por query string
    (?data.id=...&type=...) y/o en el body JSON. Verifica firma, consulta el
    preapproval real en MP y aplica el estado al usuario (idempotente).
    """
    data_id = request.query_params.get("data.id") or request.query_params.get("id")
    notif_type = request.query_params.get("type") or request.query_params.get("topic")
    if not data_id or not notif_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict):
            data_id = data_id or (body.get("data") or {}).get("id") or body.get("id")
            notif_type = notif_type or body.get("type") or body.get("topic")
    return await mp_handle_webhook(
        db,
        data_id=data_id,
        notif_type=notif_type,
        x_signature=x_signature,
        x_request_id=x_request_id,
    )


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
