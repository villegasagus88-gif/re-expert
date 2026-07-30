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
from uuid import UUID

import stripe
from api.schemas.billing import CardTokenOpcional, CardTokenRequest
from config.settings import settings
from core.auth import get_current_user, is_admin
from core.plan_gate import has_access
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, Header, Request, Response
from models.base import get_db
from models.user import User
from services import cards_service as cards
from services.billing_issues import obtener_issue_abierto, resolver_con_respaldo
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
        "is_admin": is_admin(user),
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

    # Ambas llamadas a Stripe (subscription + invoices) son independientes y ya
    # se offloadan a thread; las lanzamos en PARALELO y bajamos la latencia del
    # endpoint a la del más lento. return_exceptions mantiene el best-effort:
    # si una falla, la otra igual completa.
    subs, inv_list = await asyncio.gather(
        _run_stripe(stripe.Subscription.list, customer=user.stripe_customer_id, limit=1),
        _run_stripe(stripe.Invoice.list, customer=user.stripe_customer_id, limit=12),
        return_exceptions=True,
    )

    # Active subscription (most recent first)
    if isinstance(subs, Exception):
        logger.warning("billing_status: error fetching subscription — %s", subs)
    elif subs.data:
        sub = subs.data[0]
        result["subscription"] = {
            "status": sub.status,
            "current_period_end": _ts(sub.current_period_end),
            "current_period_start": _ts(sub.current_period_start),
            "cancel_at_period_end": sub.cancel_at_period_end,
            "cancel_at": _ts(getattr(sub, "cancel_at", None)),
        }

    # Invoice history (up to 12 most recent)
    if isinstance(inv_list, Exception):
        logger.warning("billing_status: error fetching invoices — %s", inv_list)
    else:
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


# ═══ Tarjetas guardadas ════════════════════════════════════════════════════
# El número de tarjeta NUNCA llega acá: el navegador lo manda directo a Mercado
# Pago con su SDK y nos devuelve un token de un solo uso. Estos endpoints sólo
# manejan ese token y los identificadores de la bóveda de MP.


@router.get("/cards", summary="Tarjetas guardadas del usuario")
async def listar_tarjetas(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tarjetas = await cards.listar(db, user)
    issue = await obtener_issue_abierto(db, user)
    return {
        "cards": [cards.a_dict(t) for t in tarjetas],
        "max": cards.MAX_TARJETAS,
        "mp_enabled": mp_enabled(),
        # Si hay un cobro rechazado sin resolver, el front muestra el aviso y
        # el botón para pagar con la tarjeta de respaldo.
        "billing_issue": issue,
    }


@router.post(
    "/cards",
    status_code=201,
    summary="Guardar una tarjeta (recibe el token que generó el SDK de MP)",
    responses={
        409: {"description": "Ya llegó al máximo de tarjetas"},
        422: {"description": "Falta el token"},
        502: {"description": "Mercado Pago rechazó la tarjeta"},
        503: {"description": "MP no configurado"},
    },
)
@limiter.limit("10/hour")
async def agregar_tarjeta(
    request: Request,
    body: CardTokenRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tarjeta = await cards.agregar(db, user, body.card_token)
    return cards.a_dict(tarjeta)


@router.delete(
    "/cards/{card_id}",
    status_code=204,
    summary="Quitar una tarjeta guardada",
    responses={
        404: {"description": "No es tuya o no existe"},
        409: {"description": "Es la única y la suscripción está activa"},
    },
)
async def quitar_tarjeta(
    card_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await cards.quitar(db, user, card_id)
    return Response(status_code=204)


@router.patch(
    "/cards/{card_id}/principal",
    summary="Usar esta tarjeta para cobrar (la otra pasa a respaldo)",
    responses={
        404: {"description": "No es tuya o no existe"},
        422: {"description": "Con suscripción activa hace falta el token (CVV)"},
        502: {"description": "Mercado Pago rechazó el cambio"},
    },
)
@limiter.limit("10/hour")
async def hacer_principal(
    request: Request,
    card_id: UUID,
    body: CardTokenOpcional | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cambia con qué tarjeta se cobra. Si hay una suscripción viva, el cambio se
    aplica primero en Mercado Pago (por eso pide el token con el código de
    seguridad) y recién ahí se guarda el rol: la pantalla nunca puede decir
    "se cobra con esta" sobre una tarjeta que MP no va a cobrar.
    """
    tarjetas = await cards.marcar_principal(
        db, user, card_id, body.card_token if body else None
    )
    return {"cards": [cards.a_dict(t) for t in tarjetas]}


@router.post(
    "/cards/reintentar",
    summary="Reintentar el cobro con otra tarjeta (requiere el código de seguridad)",
    responses={
        400: {"description": "No hay un cobro pendiente de resolver"},
        502: {"description": "Mercado Pago rechazó el cambio"},
        503: {"description": "MP no configurado"},
    },
)
@limiter.limit("10/hour")
async def reintentar_cobro(
    request: Request,
    body: CardTokenRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Apunta la suscripción a la otra tarjeta y la deja lista para el reintento
    de Mercado Pago.

    Por qué pide el código de seguridad: MP no permite generar un token desde
    una tarjeta guardada sin él. Es un límite de su API, no una decisión
    nuestra — por eso este paso siempre lo confirma la persona.
    """
    return await resolver_con_respaldo(db, user, body.card_token)
