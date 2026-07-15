"""
Stripe helpers — single source of truth for checkout / portal session creation.

Both `api/routes/billing.py` (canonical: POST /api/billing/checkout) and
`api/routes/stripe_routes.py` (legacy alias kept for backward compat with
the frontend) delegate to the functions here. This keeps the Stripe call
sites and error handling in one place.

Stripe SDK calls are synchronous — we run them in a thread-pool executor
to avoid blocking the FastAPI event loop.
"""
from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Any
from uuid import UUID

import stripe
from config.settings import settings
from fastapi import HTTPException
from models.stripe_event import StripeEvent
from models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def stripe_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def require_stripe() -> None:
    """Raise 503 if STRIPE_SECRET_KEY is not set; otherwise prime the SDK."""
    if not stripe_configured():
        raise HTTPException(
            status_code=503,
            detail="Stripe no configurado. Contactá soporte.",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY


async def run_stripe(func, *args, **kwargs) -> Any:
    """Run a synchronous Stripe call off the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


async def create_pro_checkout_session(user: User) -> dict[str, str]:
    """
    Create a Stripe-hosted Checkout Session for the Pro subscription.

    Raises:
        HTTPException(400) if user is already Pro.
        HTTPException(503) if Stripe / Pro price are not configured.
        HTTPException(502) if Stripe call fails.
    """
    require_stripe()

    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="Ya tenés el plan Pro activo.")

    if not settings.STRIPE_PRICE_ID_PRO:
        raise HTTPException(
            status_code=503, detail="Precio Pro no configurado. Contactá soporte."
        )

    # Derivar de FRONTEND_URL (requerido en prod) en vez de un localhost fijo:
    # sin esto, activar Stripe olvidando las URLs redirigía el checkout a
    # localhost en producción (flujo de pago roto en silencio).
    _front = (settings.FRONTEND_URL or "http://localhost:8080").rstrip("/")
    success_url = settings.STRIPE_SUCCESS_URL or f"{_front}/success.html"
    cancel_url = settings.STRIPE_CANCEL_URL or f"{_front}/pricing.html"

    try:
        session = await run_stripe(
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
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error creando sesión de pago: {exc.user_message or str(exc)}",
        ) from exc

    return {"url": session.url, "session_id": session.id}


async def create_billing_portal_session(user: User) -> dict[str, str]:
    """
    Create a Stripe Billing Portal session so the user can manage their
    subscription / payment method / cancellation.

    Raises:
        HTTPException(400) if user is not Pro or has no Stripe customer.
        HTTPException(503) if Stripe is not configured.
        HTTPException(502) if Stripe call fails.
    """
    require_stripe()

    if user.plan != "pro":
        raise HTTPException(status_code=400, detail="Solo disponible para usuarios Pro.")

    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400, detail="No hay cuenta de facturación asociada."
        )

    _front = (settings.FRONTEND_URL or "http://localhost:8080").rstrip("/")
    return_url = settings.STRIPE_SUCCESS_URL or f"{_front}/index.html"

    try:
        session = await run_stripe(
            stripe.billing_portal.Session.create,
            customer=user.stripe_customer_id,
            return_url=return_url,
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error abriendo portal de facturación: {exc.user_message or str(exc)}",
        ) from exc

    return {"url": session.url}


# ----------------------------------------------------------- Webhook --------

async def parse_webhook_event(
    payload: bytes, stripe_signature: str | None
) -> dict[str, Any]:
    """
    Parse a webhook payload — verifying the Stripe signature when
    STRIPE_WEBHOOK_SECRET is configured.

    Returns the event dict. Raises HTTPException(400) on bad signature
    or malformed payload, HTTPException(503) if Stripe is not configured.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no configurado")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            return await run_stripe(
                stripe.Webhook.construct_event,
                payload,
                stripe_signature or "",
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except stripe.error.SignatureVerificationError as exc:
            logger.warning("stripe webhook: invalid signature — %s", exc)
            raise HTTPException(
                status_code=400, detail="Firma de webhook inválida"
            ) from exc
        except Exception as exc:
            logger.warning("stripe webhook: malformed payload — %s", exc)
            raise HTTPException(status_code=400, detail="Payload inválido") from exc

    # No webhook secret configured — only allowed in DEBUG. In production
    # this would let any attacker forge `checkout.session.completed` and
    # upgrade arbitrary users to Pro for free.
    if not settings.DEBUG:
        logger.error(
            "stripe webhook rejected: STRIPE_WEBHOOK_SECRET not configured in production"
        )
        raise HTTPException(
            status_code=503,
            detail="Webhook no configurado (falta STRIPE_WEBHOOK_SECRET)",
        )
    import json
    try:
        return json.loads(payload)
    except Exception as exc:
        logger.warning("stripe webhook: bad json — %s", exc)
        raise HTTPException(status_code=400, detail="Payload inválido") from exc


async def _record_event_for_idempotency(
    db: AsyncSession, event_id: str, event_type: str
) -> bool:
    """
    Atomically record an event_id. Returns True if this is the first time we
    see it (caller should process side-effects), False if already processed
    (caller should skip).
    """
    db.add(StripeEvent(event_id=event_id, event_type=event_type))
    try:
        await db.flush()
        return True
    except IntegrityError:
        await db.rollback()
        logger.info("stripe webhook: duplicate event %s skipped", event_id)
        return False


async def _activate_pro(
    db: AsyncSession, data_obj: dict[str, Any]
) -> str | None:
    """Handle checkout.session.completed → set user.plan='pro'. Returns user_id."""
    user_id_str = (data_obj.get("metadata") or {}).get("user_id")
    customer_id = data_obj.get("customer")
    if not user_id_str:
        logger.warning(
            "stripe webhook: checkout.completed without metadata.user_id"
        )
        return None
    try:
        uid = UUID(user_id_str)
    except ValueError:
        logger.warning("stripe webhook: invalid user_id=%r", user_id_str)
        return None

    db_user = (
        await db.execute(select(User).where(User.id == uid))
    ).scalar_one_or_none()
    if not db_user:
        logger.warning("stripe webhook: user %s not found", uid)
        return None

    db_user.plan = "pro"
    if customer_id and hasattr(db_user, "stripe_customer_id"):
        db_user.stripe_customer_id = customer_id
    logger.info("stripe webhook: activated Pro for user %s", uid)
    return user_id_str


async def _downgrade_to_inactive(
    db: AsyncSession, data_obj: dict[str, Any], reason: str
) -> str | None:
    """
    Handle subscription.deleted / paused / payment_failed → user.plan='inactive'.
    Looked up by stripe_customer_id. Returns user_id if found.
    """
    customer_id = data_obj.get("customer")
    if not customer_id:
        return None
    db_user = (
        await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
    ).scalar_one_or_none()
    if not db_user:
        logger.warning(
            "stripe webhook: customer %s not linked to any user (reason=%s)",
            customer_id,
            reason,
        )
        return None

    db_user.plan = "inactive"
    logger.info(
        "stripe webhook: downgraded user %s to inactive (reason=%s)",
        db_user.id,
        reason,
    )
    return str(db_user.id)


async def handle_webhook_event(
    db: AsyncSession, event: dict[str, Any]
) -> dict[str, str]:
    """
    Dispatch a parsed Stripe event to the appropriate handler with idempotency
    and structured logging. Always commits at the end so a partial failure
    doesn't leave the StripeEvent row without its side-effect.

    Supported event types:
      - checkout.session.completed       → activate Pro
      - customer.subscription.deleted    → downgrade to Free
      - customer.subscription.paused     → downgrade to Free
      - invoice.payment_failed           → downgrade to Free (renewal failed)

    All other event types are logged and ignored (returns status='ignored').
    """
    event_id = event.get("id") or ""
    event_type = event.get("type") or ""
    data_obj = (event.get("data") or {}).get("object") or {}

    if not event_id:
        # Stripe always sends an id; if missing, refuse rather than risk
        # processing the same payload many times without dedup.
        raise HTTPException(status_code=400, detail="Evento sin id")

    is_new = await _record_event_for_idempotency(db, event_id, event_type)
    if not is_new:
        return {"status": "duplicate", "event_id": event_id}

    logger.info("stripe webhook: processing %s (%s)", event_type, event_id)

    if event_type == "checkout.session.completed":
        await _activate_pro(db, data_obj)
    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        await _downgrade_to_inactive(db, data_obj, reason=event_type)
    elif event_type == "invoice.payment_failed":
        await _downgrade_to_inactive(db, data_obj, reason="invoice.payment_failed")
    else:
        logger.info("stripe webhook: ignored event type %s", event_type)
        await db.commit()
        return {"status": "ignored", "event_id": event_id, "event_type": event_type}

    await db.commit()
    return {"status": "ok", "event_id": event_id, "event_type": event_type}
