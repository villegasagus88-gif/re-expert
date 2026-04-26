"""
Stripe payment integration endpoints.
- POST /api/stripe/create-checkout-session  → Stripe-hosted checkout URL
- GET  /api/stripe/status                   → current user subscription status
- POST /api/stripe/webhook                  → Stripe event handler (no auth)
- POST /api/stripe/portal                   → billing portal session URL
"""
import asyncio
from functools import partial
from uuid import UUID

import stripe
from config.settings import settings
from core.auth import get_current_user
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from models.base import get_db
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


def _stripe_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def _require_stripe():
    if not _stripe_configured():
        raise HTTPException(
            status_code=503,
            detail="Stripe no configurado. Contactá soporte.",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY


async def _run_stripe(func, *args, **kwargs):
    """Run synchronous stripe call in thread-pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


@router.get(
    "/status",
    summary="Estado de suscripción del usuario",
)
async def get_status(user: User = Depends(get_current_user)):
    return {"plan": user.plan, "is_pro": user.plan == "pro"}


@router.post(
    "/create-checkout-session",
    summary="Crear sesión de checkout en Stripe",
    responses={
        503: {"description": "Stripe no configurado"},
        401: {"description": "Token inválido"},
    },
)
async def create_checkout_session(
    user: User = Depends(get_current_user),
):
    _require_stripe()

    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="Ya tenés el plan Pro activo.")

    if not settings.STRIPE_PRICE_ID_PRO:
        raise HTTPException(
            status_code=503, detail="Precio Pro no configurado. Contactá soporte."
        )

    success_url = (settings.STRIPE_SUCCESS_URL or "http://localhost:8080/success.html")
    cancel_url = (settings.STRIPE_CANCEL_URL or "http://localhost:8080/pricing.html")

    session = await _run_stripe(
        stripe.checkout.Session.create,
        payment_method_types=["card"],
        mode="subscription",
        customer_email=user.email,
        line_items=[{"price": settings.STRIPE_PRICE_ID_PRO, "quantity": 1}],
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url + "?cancelled=1",
        metadata={"user_id": str(user.id)},
        client_reference_id=str(user.id),
        allow_promotion_codes=True,
    )
    return {"url": session.url, "session_id": session.id}


@router.post(
    "/portal",
    summary="Crear sesión de portal de facturación",
    responses={503: {"description": "Stripe no configurado"}},
)
async def create_portal_session(user: User = Depends(get_current_user)):
    _require_stripe()

    if user.plan != "pro":
        raise HTTPException(status_code=400, detail="Solo disponible para usuarios Pro.")

    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No hay cuenta de facturación asociada.")

    return_url = settings.STRIPE_SUCCESS_URL or "http://localhost:8080/index.html"

    session = await _run_stripe(
        stripe.billing_portal.Session.create,
        customer=user.stripe_customer_id,
        return_url=return_url,
    )
    return {"url": session.url}


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
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no configurado")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()

    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = await _run_stripe(
                stripe.Webhook.construct_event,
                payload,
                stripe_signature or "",
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Firma de webhook inválida")
        except Exception:
            raise HTTPException(status_code=400, detail="Payload inválido")
    else:
        import json
        try:
            event = json.loads(payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Payload inválido")

    event_type = event.get("type", "") if isinstance(event, dict) else event["type"]
    data_obj = event["data"]["object"] if isinstance(event, dict) else event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id_str = data_obj.get("metadata", {}).get("user_id")
        customer_id = data_obj.get("customer")
        if user_id_str:
            try:
                uid = UUID(user_id_str)
            except ValueError:
                return {"status": "invalid_user_id"}
            result = await db.execute(select(User).where(User.id == uid))
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.plan = "pro"
                if customer_id and hasattr(db_user, "stripe_customer_id"):
                    db_user.stripe_customer_id = customer_id
                await db.commit()

    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        customer_id = data_obj.get("customer")
        if customer_id and hasattr(User, "stripe_customer_id"):
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.plan = "free"
                await db.commit()

    return {"status": "ok"}
