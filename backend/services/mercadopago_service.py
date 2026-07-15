"""
Mercado Pago — suscripciones (preapproval) para el modelo pago-only en ARS.

Reemplaza a Stripe para Argentina. El flujo es:

  1. El usuario toca "Suscribirse" → `create_subscription()` crea un preapproval
     en MP (atado al plan `MP_PLAN_ID`, con período de prueba de 7 días
     configurado en el plan) y devuelve el `init_point` (checkout hosteado por
     MP). El frontend redirige ahí.
  2. El usuario carga su tarjeta en MP y autoriza. MP nos pega un webhook.
  3. `handle_webhook()` verifica la firma (HMAC-SHA256), consulta el preapproval
     por su id, y mapea el estado → plan del usuario (authorized → pro,
     cancelled/paused → inactive). El `external_reference` del preapproval es el
     user_id, así sabemos a quién actualizar (sin columnas nuevas en la DB).

TODO el módulo es INERTE si no están `MP_ACCESS_TOKEN` + `MP_PLAN_ID`
(mp_enabled() == False). Hasta que Agustín cargue las credenciales en Railway,
el backend se comporta exactamente como antes (cae a Stripe / trial sin tarjeta).

NOTA: el detalle exacto de creación del preapproval (init_point vs card_token
con MP.js) puede necesitar ajuste fino contra el SANDBOX de MP cuando tengamos
credenciales. Lo que está cubierto por tests y NO depende de la red es lo
crítico de seguridad: verificación de firma del webhook + mapeo de estados.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from uuid import UUID

import httpx
from config.settings import settings
from fastapi import HTTPException
from models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

MP_API = "https://api.mercadopago.com"
_TIMEOUT = 20.0


# ── Estado de configuración ──────────────────────────────────────────────────
def mp_enabled() -> bool:
    """True si MP está configurado (token + plan). Si no, el módulo es inerte."""
    return bool(settings.MP_ACCESS_TOKEN and settings.MP_PLAN_ID)


def mp_public_config() -> dict:
    """Config NO sensible para el frontend (public_key es pública por diseño)."""
    return {"enabled": mp_enabled(), "public_key": settings.MP_PUBLIC_KEY or ""}


def _require_mp() -> None:
    if not mp_enabled():
        raise HTTPException(status_code=503, detail="Mercado Pago no configurado.")


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}"}


def _back_url() -> str:
    if settings.MP_BACK_URL:
        return settings.MP_BACK_URL
    base = (settings.FRONTEND_URL or "https://re-expert.netlify.app").rstrip("/")
    return f"{base}/app.html"


# ── Mapeo estado de preapproval → plan ───────────────────────────────────────
# Estados de un preapproval de MP:
#   pending    → todavía no autorizado (no tocar el plan).
#   authorized → suscripción activa (incluye período de prueba) → acceso.
#   paused     → suspendida (falló el cobro / pausada) → sin acceso.
#   cancelled  → cancelada → sin acceso.
_STATUS_TO_PLAN = {
    "authorized": "pro",
    "paused": "inactive",
    "cancelled": "inactive",
}


def plan_for_status(status: str | None) -> str | None:
    """Plan a setear para un estado de preapproval, o None si no requiere acción."""
    if not status:
        return None
    return _STATUS_TO_PLAN.get(status.lower())


# ── Checkout (crear suscripción) ─────────────────────────────────────────────
async def create_subscription(user: User) -> dict[str, str]:
    """
    Crea un preapproval (suscripción) para el usuario y devuelve
    `{url, preapproval_id}`. El frontend redirige el browser a `url`.

    Raises:
        HTTPException(400) si el usuario ya es pro.
        HTTPException(503) si MP no está configurado.
        HTTPException(502) si MP falla / no devuelve init_point.
    """
    _require_mp()
    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="Ya tenés una suscripción activa.")

    # Anti-doble-débito: si el user ya tiene un preapproval vivo en MP (dos
    # tabs, reintento tras un webhook demorado), NO crear otro. authorized →
    # ya está suscripto; pending → reutilizar el link de pago existente.
    # Best-effort: si el search falla, seguimos con la creación normal.
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            s = await client.get(
                f"{MP_API}/preapproval/search",
                params={"external_reference": str(user.id)},
                headers=_auth_headers(),
            )
        if s.status_code < 300:
            for r in (s.json() or {}).get("results") or []:
                st = (r.get("status") or "").lower()
                if st in ("authorized", "paused"):
                    raise HTTPException(
                        status_code=400,
                        detail="Ya tenés una suscripción activa en Mercado Pago. "
                               "Si no ves el acceso, esperá un minuto y recargá.",
                    )
                if st == "pending":
                    prev_url = r.get("init_point") or r.get("sandbox_init_point")
                    if prev_url:
                        logger.info("MP create_subscription: reutilizo preapproval pending %s", r.get("id"))
                        return {"url": prev_url, "preapproval_id": str(r.get("id", ""))}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — el guard nunca bloquea el checkout
        logger.warning("MP create_subscription: search previo falló — %s", exc)

    payload = {
        "preapproval_plan_id": settings.MP_PLAN_ID,
        "payer_email": user.email,
        "external_reference": str(user.id),  # ← así matcheamos el webhook al user
        "back_url": _back_url(),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{MP_API}/preapproval", json=payload, headers=_auth_headers()
            )
    except httpx.HTTPError as exc:
        logger.warning("MP create_subscription: error de red — %s", exc)
        raise HTTPException(
            status_code=502, detail="No se pudo contactar a Mercado Pago."
        ) from exc

    if resp.status_code >= 300:
        logger.warning(
            "MP create_subscription falló %s — %s", resp.status_code, resp.text[:500]
        )
        raise HTTPException(
            status_code=502,
            detail="No se pudo iniciar la suscripción en Mercado Pago.",
        )

    data = resp.json()
    url = data.get("init_point") or data.get("sandbox_init_point")
    if not url:
        logger.error("MP create_subscription: respuesta sin init_point — %s", str(data)[:300])
        raise HTTPException(
            status_code=502, detail="Mercado Pago no devolvió un link de pago."
        )
    return {"url": url, "preapproval_id": str(data.get("id", ""))}


async def start_subscription_checkout(user: User) -> dict[str, str]:
    """
    Dispatcher de checkout: usa Mercado Pago si está configurado; si no, cae a
    Stripe (legacy). Permite que el frontend siga llamando a /api/billing/checkout
    sin cambios: cuando Agustín cargue las credenciales de MP, se activa solo.
    """
    if mp_enabled():
        return await create_subscription(user)
    # Import lazy para evitar ciclos y no exigir Stripe si no hace falta.
    from services.stripe_service import create_pro_checkout_session

    return await create_pro_checkout_session(user)


# ── Cursos (pago único — Checkout Pro) ───────────────────────────────────────
async def create_course_preference(
    user: User, *, purchase_id: str, title: str, price_ars: float
) -> dict[str, str]:
    """Crea una preference de Checkout Pro para la compra de un curso y devuelve
    `{url, preference_id}`. `external_reference` = purchase_id (así el webhook
    matchea el pago con la compra). El precio SIEMPRE viene del backend."""
    _require_mp()
    base = _back_url()
    payload = {
        "items": [{
            "title": title[:250], "quantity": 1,
            "unit_price": float(price_ars), "currency_id": "ARS",
        }],
        "external_reference": str(purchase_id),
        "payer": {"email": user.email},
        "back_urls": {"success": base, "failure": base, "pending": base},
        "auto_return": "approved",
        "metadata": {"kind": "course", "purchase_id": str(purchase_id), "user_id": str(user.id)},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{MP_API}/checkout/preferences", json=payload, headers=_auth_headers()
            )
    except httpx.HTTPError as exc:
        logger.warning("MP create_course_preference: error de red — %s", exc)
        raise HTTPException(status_code=502, detail="No se pudo contactar a Mercado Pago.") from exc
    if resp.status_code >= 300:
        logger.warning("MP create_course_preference falló %s — %s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=502, detail="No se pudo iniciar el pago en Mercado Pago.")
    data = resp.json()
    url = data.get("init_point") or data.get("sandbox_init_point")
    if not url:
        logger.error("MP create_course_preference: sin init_point — %s", str(data)[:300])
        raise HTTPException(status_code=502, detail="Mercado Pago no devolvió un link de pago.")
    return {"url": url, "preference_id": str(data.get("id", ""))}


async def create_cart_preference(
    user: User, *, order_id: str, items: list[dict]
) -> dict[str, str]:
    """Crea UNA preference de Checkout Pro con varios cursos (carrito) y devuelve
    `{url, preference_id}`. `items` = [{"title": ..., "price_ars": ...}, ...] con
    precios que SIEMPRE salen del catálogo del backend. `external_reference` =
    order_id: el webhook aplica el pago a todas las compras de la orden."""
    _require_mp()
    base = _back_url()
    payload = {
        "items": [
            {
                "title": str(it["title"])[:250], "quantity": 1,
                "unit_price": float(it["price_ars"]), "currency_id": "ARS",
            }
            for it in items
        ],
        "external_reference": str(order_id),
        "payer": {"email": user.email},
        "back_urls": {"success": base, "failure": base, "pending": base},
        "auto_return": "approved",
        "metadata": {"kind": "course_cart", "order_id": str(order_id), "user_id": str(user.id)},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{MP_API}/checkout/preferences", json=payload, headers=_auth_headers()
            )
    except httpx.HTTPError as exc:
        logger.warning("MP create_cart_preference: error de red — %s", exc)
        raise HTTPException(status_code=502, detail="No se pudo contactar a Mercado Pago.") from exc
    if resp.status_code >= 300:
        logger.warning("MP create_cart_preference falló %s — %s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=502, detail="No se pudo iniciar el pago en Mercado Pago.")
    data = resp.json()
    url = data.get("init_point") or data.get("sandbox_init_point")
    if not url:
        logger.error("MP create_cart_preference: sin init_point — %s", str(data)[:300])
        raise HTTPException(status_code=502, detail="Mercado Pago no devolvió un link de pago.")
    return {"url": url, "preference_id": str(data.get("id", ""))}


async def fetch_payment(payment_id: str) -> dict:
    """Consulta un pago por id en MP. Raises 502 si MP falla."""
    _require_mp()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{MP_API}/v1/payments/{payment_id}", headers=_auth_headers()
            )
    except httpx.HTTPError as exc:
        logger.warning("MP fetch_payment: error de red — %s", exc)
        raise HTTPException(status_code=502, detail="No se pudo consultar Mercado Pago.") from exc
    if resp.status_code >= 300:
        logger.warning("MP fetch_payment %s falló %s — %s", payment_id, resp.status_code, resp.text[:300])
        raise HTTPException(status_code=502, detail="Mercado Pago devolvió un error.")
    return resp.json()


# Estado del pago (MP) → estado de la compra del curso.
_PAYMENT_STATUS_TO_PURCHASE = {
    "approved": "approved",
    "rejected": "rejected",
    "cancelled": "rejected",
    "refunded": "refunded",
    "charged_back": "refunded",
}


async def _apply_status_to_row(db: AsyncSession, purchase, new_status: str, payment_id) -> None:
    """Aplica el estado de un pago a UNA fila de CoursePurchase. Idempotente
    (no degrada un approved salvo refund) y anti-duplicado: si OTRA fila del
    mismo (user, curso) ya tiene acceso, aprobar esta violaría el unique
    parcial (uq_course_purchases_owned) y el webhook quedaría en 500 con MP
    reintentando — se marca "duplicate" para conciliar/reembolsar a mano."""
    from models.course_purchase import CoursePurchase

    if purchase.status == "approved" and new_status != "refunded":
        return
    if new_status == "approved":
        other = (
            await db.execute(
                select(CoursePurchase).where(
                    CoursePurchase.user_id == purchase.user_id,
                    CoursePurchase.course_id == purchase.course_id,
                    CoursePurchase.status.in_(("approved", "free")),
                    CoursePurchase.id != purchase.id,
                )
            )
        ).scalars().first()
        if other is not None:
            purchase.status = "duplicate"
            if payment_id is not None:
                purchase.mp_payment_id = str(payment_id)
            logger.warning(
                "MP webhook payment: pago DUPLICADO del curso %s (user %s, pago %s) — "
                "requiere reembolso manual",
                purchase.course_id, purchase.user_id, payment_id,
            )
            return
    purchase.status = new_status
    if payment_id is not None:
        purchase.mp_payment_id = str(payment_id)
    logger.info("MP webhook payment: compra %s → %s", purchase.id, new_status)


async def _apply_payment_to_purchase(db: AsyncSession, payment: dict) -> str | None:
    """Aplica el estado de un pago de MP a su/s CoursePurchase. El
    external_reference es un purchase_id (compra suelta) o un order_id
    (carrito: se aplica a TODAS las compras de la orden)."""
    from models.course_purchase import CoursePurchase

    ext_ref = payment.get("external_reference") or ""
    new_status = _PAYMENT_STATUS_TO_PURCHASE.get((payment.get("status") or "").lower())
    if new_status is None:
        logger.info("MP webhook payment: estado %r sin acción", payment.get("status"))
        return None
    try:
        pid = UUID(str(ext_ref))
    except (ValueError, TypeError):
        logger.warning("MP webhook payment: external_reference inválido=%r", ext_ref)
        return None
    payment_id = payment.get("id")

    purchase = (
        await db.execute(select(CoursePurchase).where(CoursePurchase.id == pid))
    ).scalar_one_or_none()
    if purchase is not None:
        await _apply_status_to_row(db, purchase, new_status, payment_id)
        return str(pid)

    # Carrito: external_reference = order_id → todas las compras de la orden.
    rows = list((
        await db.execute(select(CoursePurchase).where(CoursePurchase.order_id == pid))
    ).scalars().all())
    if not rows:
        logger.warning("MP webhook payment: compra/orden %s no encontrada", pid)
        return None
    for row in rows:
        await _apply_status_to_row(db, row, new_status, payment_id)
    return str(pid)


# ── Webhook ──────────────────────────────────────────────────────────────────
def verify_webhook_signature(
    x_signature: str | None,
    x_request_id: str | None,
    data_id: str | None,
    secret: str | None,
) -> bool:
    """
    Verifica la firma HMAC-SHA256 del webhook de MP (comparación en tiempo
    constante).

    MP manda el header `x-signature: ts=<ts>,v1=<hash>`. El string firmado
    (manifest) es: `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`
    donde `data.id` viene del query string (?data.id=...). Devuelve False ante
    cualquier dato faltante o firma que no matchea.
    """
    if not secret or not x_signature:
        return False
    parts: dict[str, str] = {}
    for piece in x_signature.split(","):
        if "=" in piece:
            k, v = piece.split("=", 1)
            parts[k.strip()] = v.strip()
    ts = parts.get("ts")
    v1 = parts.get("v1")
    if not ts or not v1:
        return False
    manifest = f"id:{data_id or ''};request-id:{x_request_id or ''};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


async def fetch_preapproval(preapproval_id: str) -> dict:
    """Consulta un preapproval por id en MP. Raises 502 si MP falla."""
    _require_mp()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{MP_API}/preapproval/{preapproval_id}", headers=_auth_headers()
            )
    except httpx.HTTPError as exc:
        logger.warning("MP fetch_preapproval: error de red — %s", exc)
        raise HTTPException(
            status_code=502, detail="No se pudo consultar Mercado Pago."
        ) from exc
    if resp.status_code >= 300:
        logger.warning(
            "MP fetch_preapproval %s falló %s — %s",
            preapproval_id,
            resp.status_code,
            resp.text[:300],
        )
        raise HTTPException(status_code=502, detail="Mercado Pago devolvió un error.")
    return resp.json()


async def cancel_subscription(db: AsyncSession, user: User) -> dict:
    """
    Botón de baja (Ley 24.240 — Defensa del Consumidor exige poder darse de
    baja online): cancela la suscripción de MP del usuario.

    Busca el preapproval por `external_reference` (= user_id), lo cancela en MP
    y corta el acceso localmente (plan → inactive). El webhook de MP confirma
    después (idempotente: re-setear inactive es no-op).

    Raises:
        HTTPException(503) si MP no está configurado.
        HTTPException(400) si el usuario no tiene plan pro.
        HTTPException(404) si MP no tiene una suscripción viva para ese user.
        HTTPException(502) si MP falla.
    """
    _require_mp()
    if user.plan != "pro":
        raise HTTPException(
            status_code=400, detail="No tenés una suscripción activa para cancelar."
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{MP_API}/preapproval/search",
                params={"external_reference": str(user.id)},
                headers=_auth_headers(),
            )
    except httpx.HTTPError as exc:
        logger.warning("MP cancel: error de red buscando preapproval — %s", exc)
        raise HTTPException(
            status_code=502, detail="No se pudo contactar a Mercado Pago."
        ) from exc
    if resp.status_code >= 300:
        logger.warning("MP cancel: search falló %s — %s", resp.status_code, resp.text[:300])
        raise HTTPException(status_code=502, detail="Mercado Pago devolvió un error.")

    results = (resp.json() or {}).get("results") or []
    vivos = [
        r for r in results
        if (r.get("status") or "").lower() in ("authorized", "paused")
    ]
    if not vivos:
        raise HTTPException(
            status_code=404,
            detail="No encontramos una suscripción activa en Mercado Pago para tu cuenta.",
        )
    # Cancelar TODOS los preapprovals vivos, no solo el primero: si por un edge
    # de anti-doble-débito o creación concurrente el usuario terminó con >1
    # preapproval authorized/paused, cancelar uno solo lo dejaría siendo cobrado
    # por los demás tras "darse de baja".
    pre_ids = [str(r.get("id")) for r in vivos if r.get("id")]
    for pre_id in pre_ids:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.put(
                    f"{MP_API}/preapproval/{pre_id}",
                    json={"status": "cancelled"},
                    headers=_auth_headers(),
                )
        except httpx.HTTPError as exc:
            logger.warning("MP cancel: error de red cancelando %s — %s", pre_id, exc)
            raise HTTPException(
                status_code=502, detail="No se pudo contactar a Mercado Pago."
            ) from exc
        if resp.status_code >= 300:
            logger.warning(
                "MP cancel: PUT %s falló %s — %s", pre_id, resp.status_code, resp.text[:300]
            )
            raise HTTPException(
                status_code=502, detail="Mercado Pago no pudo cancelar la suscripción."
            )

    pre_id = pre_ids[0]  # para el log/respuesta (ya se cancelaron todos)
    # Corte local inmediato; el webhook (cancelled → inactive) lo confirma.
    db_user = (
        await db.execute(select(User).where(User.id == user.id))
    ).scalar_one_or_none()
    if db_user:
        db_user.plan = "inactive"
        await db.commit()
    logger.info("MP cancel: user %s canceló preapproval %s", user.id, pre_id)
    return {
        "ok": True,
        "message": "Suscripción cancelada. No se te realizarán más cobros.",
        "preapproval_id": pre_id,
    }


async def _apply_status_to_user(
    db: AsyncSession, external_reference: str, status: str | None
) -> str | None:
    """Mapea el estado del preapproval → plan del user (external_reference=user_id)."""
    new_plan = plan_for_status(status)
    if new_plan is None:
        logger.info("MP webhook: estado %r sin acción", status)
        return None
    try:
        uid = UUID(external_reference)
    except (ValueError, TypeError):
        logger.warning("MP webhook: external_reference inválido=%r", external_reference)
        return None
    db_user = (
        await db.execute(select(User).where(User.id == uid))
    ).scalar_one_or_none()
    if not db_user:
        logger.warning("MP webhook: usuario %s no encontrado", uid)
        return None
    db_user.plan = new_plan
    if new_plan == "pro":
        # Ya tiene tarjeta/sub activa (o trial gestionado por MP): el gate
        # de acceso usa plan=='pro' directo, sin trial_ends_at.
        db_user.trial_ends_at = None
    logger.info("MP webhook: user %s → plan %s (status=%s)", uid, new_plan, status)
    return str(uid)


async def _record_mp_event(
    db: AsyncSession, request_id: str, data_id: str | None, notif_type: str | None
) -> bool:
    """Registra la entrega (x-request-id). Devuelve True si es nueva (procesar),
    False si ya se había recibido esa misma entrega (saltar). También sirve de
    audit trail de webhooks de billing."""
    from models.mp_event import MpEvent

    db.add(MpEvent(request_id=request_id, data_id=data_id, notif_type=notif_type))
    try:
        await db.flush()
        return True
    except IntegrityError:
        await db.rollback()
        logger.info("MP webhook: entrega duplicada %s saltada", request_id)
        return False


async def handle_webhook(
    db: AsyncSession,
    *,
    data_id: str | None,
    notif_type: str | None,
    x_signature: str | None,
    x_request_id: str | None,
) -> dict:
    """
    Procesa una notificación de webhook de MP.

    1. Verifica la firma (en prod sin MP_WEBHOOK_SECRET → 503; en DEBUG la
       permite, igual que el webhook de Stripe).
    2. Si el tipo es de suscripción (preapproval), consulta el estado real en
       MP y lo aplica al usuario.
    3. Idempotente: re-setear el mismo plan es un no-op natural.

    Raises HTTPException(400) ante firma inválida, (503) si MP no está
    configurado, (502) si la consulta a MP falla.
    """
    _require_mp()

    # 1. Firma
    if settings.MP_WEBHOOK_SECRET:
        if not verify_webhook_signature(
            x_signature, x_request_id, data_id, settings.MP_WEBHOOK_SECRET
        ):
            logger.warning("MP webhook: firma inválida")
            raise HTTPException(status_code=400, detail="Firma de webhook inválida")
    elif not settings.DEBUG:
        logger.error("MP webhook rechazado: falta MP_WEBHOOK_SECRET en producción")
        raise HTTPException(
            status_code=503,
            detail="Webhook no configurado (falta MP_WEBHOOK_SECRET)",
        )

    # 1.b Idempotencia de ENTREGA: si ya procesamos esta misma entrega
    #     (x-request-id único por delivery), saltamos. Los reintentos de MP con
    #     otro request_id NO se saltan: re-consultan el estado vivo y se aplican
    #     idempotentemente, así que nunca se descarta una transición legítima.
    if x_request_id and not await _record_mp_event(db, x_request_id, data_id, notif_type):
        return {"status": "duplicate", "request_id": x_request_id}

    # 2. Dispatch por tipo, con MATCH EXACTO. MP manda más topics de los que
    #    manejamos: "subscription_authorized_payment" (cada cobro recurrente)
    #    contiene "payment" y "subscription_preapproval_plan" contiene
    #    "preapproval" — un match por substring los mandaría al endpoint
    #    equivocado (404 → 502 → MP reintenta en loop). Se ignoran a propósito:
    #    el estado de la suscripción lo gobierna subscription_preapproval.
    if not data_id:
        return {"status": "ignored", "reason": "sin data.id"}
    t = (notif_type or "").lower()

    if t == "payment":  # pago único de curso (Checkout Pro)
        payment = await fetch_payment(data_id)
        updated = await _apply_payment_to_purchase(db, payment)
        await db.commit()
        return {"status": "ok" if updated else "noop", "payment_status": payment.get("status")}

    if t in ("preapproval", "subscription_preapproval"):  # suscripción
        pre = await fetch_preapproval(data_id)
        status = pre.get("status")
        ext_ref = pre.get("external_reference") or ""
        updated = await _apply_status_to_user(db, ext_ref, status)
        await db.commit()
        return {"status": "ok" if updated else "noop", "preapproval_status": status}

    logger.info("MP webhook: tipo %r ignorado", notif_type)
    return {"status": "ignored", "type": notif_type}
