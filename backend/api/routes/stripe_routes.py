"""
Stripe payment integration endpoints.

Canonical paths live under /api/billing/* (see api/routes/billing.py).
The /api/stripe/* paths here are kept as thin aliases for backward
compatibility with the deployed frontend.

- GET  /api/stripe/status                   → current user subscription status
- POST /api/stripe/create-checkout-session  → alias of POST /api/billing/checkout
- POST /api/stripe/portal                   → alias of POST /api/billing/portal
- POST /api/stripe/webhook                  → Stripe event handler (no auth)
"""
from core.auth import get_current_user
from fastapi import APIRouter, Depends, Header, Request, status
from models.base import get_db
from models.user import User
from services.mercadopago_service import start_subscription_checkout
from services.stripe_service import (
    create_billing_portal_session,
    handle_webhook_event,
    parse_webhook_event,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


@router.get(
    "/status",
    summary="Estado de suscripción del usuario",
)
async def get_status(user: User = Depends(get_current_user)):
    return {"plan": user.plan, "is_pro": user.plan == "pro"}


@router.post(
    "/create-checkout-session",
    summary="Crear sesión de checkout en Stripe (alias de /api/billing/checkout)",
    responses={
        503: {"description": "Stripe no configurado"},
        401: {"description": "Token inválido"},
    },
)
async def create_checkout_session(user: User = Depends(get_current_user)):
    # Despacha al proveedor activo (Mercado Pago, o Stripe legacy).
    return await start_subscription_checkout(user)


@router.post(
    "/portal",
    summary="Crear sesión de portal de facturación (alias de /api/billing/portal)",
    responses={503: {"description": "Stripe no configurado"}},
)
async def create_portal_session(user: User = Depends(get_current_user)):
    return await create_billing_portal_session(user)


@router.post(
    "/webhook",
    summary="Stripe webhook — sin autenticación JWT",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Recibe eventos de Stripe. Verifica firma cuando STRIPE_WEBHOOK_SECRET
    está configurado, deduplica por event_id en `stripe_events` (Stripe
    reintenta hasta 3 días), y dispara el handler correspondiente.
    """
    payload = await request.body()
    event = await parse_webhook_event(payload, stripe_signature)
    return await handle_webhook_event(db, event)
