"""
Tarjetas guardadas — API de Customers & Cards de Mercado Pago.

Cómo entra una tarjeta (el número NUNCA toca este servidor):
  1. El navegador carga el SDK de MP y muestra su formulario embebido.
  2. El usuario tipea la tarjeta; los campos son del SDK, no nuestros.
  3. El SDK manda los datos directo a MP y devuelve un `card_token` de un solo uso.
  4. El front nos manda SOLO ese token.
  5. Acá se lo pasamos a MP para que guarde la tarjeta en su bóveda, y nos
     devuelve un `card_id`. Persistimos ese id, la marca y los últimos cuatro.

Endpoints de MP que se usan (verificados contra su referencia):
  POST   /v1/customers                        crear cliente
  GET    /v1/customers/search?email=          buscarlo por email
  POST   /v1/customers/{cid}/cards            guardar tarjeta   body: {"token": ...}
  GET    /v1/customers/{cid}/cards            listar
  DELETE /v1/customers/{cid}/cards/{card_id}  eliminar
  PUT    /preapproval/{id}                    cambiar el medio de pago de la
                                              suscripción   body: {"card_token_id": ...}

Límite del proveedor, importante: **MP exige el código de seguridad para generar
un token desde una tarjeta ya guardada.** Por eso el cambio a la tarjeta de
respaldo no puede ser automático — lo confirma la persona con un clic y su CVV.
Está documentado en los Términos para no prometer algo que la API no permite.

Todo el módulo es INERTE si Mercado Pago no está configurado, igual que
mercadopago_service: sin credenciales, cada función levanta 503 y el resto de la
app sigue funcionando como siempre.
"""
from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import HTTPException
from models.payment_method import PaymentMethod
from models.user import User
from services.mercadopago_service import (
    MP_API,
    _auth_headers,
    _require_mp,
    mp_enabled,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0, connect=8.0)

# Tope de tarjetas por usuario: una para cobrar y una de respaldo. Más que eso
# no aporta y complica la elección.
MAX_TARJETAS = 2

ROL_PRINCIPAL = "principal"
ROL_RESPALDO = "respaldo"


# ─────────────────────────── helpers de MP ───────────────────────────

async def _get_or_create_customer(user: User) -> str:
    """Id de cliente de MP para este usuario. Lo busca por email y si no existe lo crea."""
    _require_mp()
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Buscar primero: crear dos veces el mismo email devuelve error de MP.
        try:
            r = await client.get(
                f"{MP_API}/v1/customers/search",
                params={"email": user.email},
                headers=_auth_headers(),
            )
            if r.status_code < 300:
                for c in (r.json() or {}).get("results") or []:
                    if c.get("id"):
                        return str(c["id"])
        except httpx.HTTPError as e:
            logger.warning("MP customers/search falló (sigo con create): %s", e)

        r = await client.post(
            f"{MP_API}/v1/customers",
            json={"email": user.email, "first_name": (user.full_name or "")[:60]},
            headers=_auth_headers(),
        )
    if r.status_code >= 300:
        # MP devuelve 400 con `already_exists` si el email ya tiene cliente y el
        # search no lo encontró (índice demorado). Se reintenta la búsqueda.
        cuerpo = (r.text or "")[:300]
        if "already_exists" in cuerpo or r.status_code == 400:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                r2 = await client.get(
                    f"{MP_API}/v1/customers/search",
                    params={"email": user.email},
                    headers=_auth_headers(),
                )
            if r2.status_code < 300:
                for c in (r2.json() or {}).get("results") or []:
                    if c.get("id"):
                        return str(c["id"])
        logger.error("MP no pudo crear el cliente (%s): %s", r.status_code, cuerpo)
        raise HTTPException(status_code=502, detail="No pudimos preparar tu medio de pago.")
    cid = (r.json() or {}).get("id")
    if not cid:
        raise HTTPException(status_code=502, detail="No pudimos preparar tu medio de pago.")
    return str(cid)


def _datos_visibles(card: dict) -> dict:
    """De la respuesta de MP, sólo lo que sirve para mostrar. Nada operable."""
    pm = card.get("payment_method") or {}
    titular = ((card.get("cardholder") or {}).get("name") or "")[:120]
    return {
        "mp_card_id": str(card.get("id") or ""),
        "brand": (pm.get("name") or pm.get("id") or "")[:30],
        "last_four": str(card.get("last_four_digits") or "")[:4],
        "exp_month": card.get("expiration_month"),
        "exp_year": card.get("expiration_year"),
        "holder_name": titular,
    }


# ─────────────────────────── operaciones ───────────────────────────

async def listar(db: AsyncSession, user: User) -> list[PaymentMethod]:
    filas = (await db.execute(
        select(PaymentMethod)
        .where(PaymentMethod.user_id == user.id)
        .order_by(PaymentMethod.role.asc(), PaymentMethod.created_at.asc())
    )).scalars().all()
    return list(filas)


async def agregar(db: AsyncSession, user: User, card_token: str) -> PaymentMethod:
    """Guarda en MP la tarjeta que el navegador ya tokenizó y la registra acá."""
    _require_mp()
    if not card_token or len(card_token) < 8:
        raise HTTPException(status_code=422, detail="Falta el token de la tarjeta.")

    actuales = await listar(db, user)
    if len(actuales) >= MAX_TARJETAS:
        raise HTTPException(
            status_code=409,
            detail=f"Ya tenés {MAX_TARJETAS} tarjetas guardadas. Quitá una para agregar otra.",
        )

    customer_id = await _get_or_create_customer(user)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            f"{MP_API}/v1/customers/{customer_id}/cards",
            json={"token": card_token},
            headers=_auth_headers(),
        )
    if r.status_code >= 300:
        logger.error("MP no pudo guardar la tarjeta (%s): %s", r.status_code, (r.text or "")[:300])
        raise HTTPException(
            status_code=502,
            detail="Mercado Pago no aceptó la tarjeta. Revisá los datos e intentá de nuevo.",
        )

    datos = _datos_visibles(r.json() or {})
    if not datos["mp_card_id"]:
        raise HTTPException(status_code=502, detail="Mercado Pago no devolvió la tarjeta.")

    # ¿Ya la tenía guardada? MP acepta duplicados; nosotros no.
    ya = next((t for t in actuales if t.mp_card_id == datos["mp_card_id"]), None)
    if ya:
        return ya

    # La primera que se agrega es la principal; la segunda, el respaldo.
    rol = ROL_PRINCIPAL if not actuales else ROL_RESPALDO
    tarjeta = PaymentMethod(
        user_id=user.id, mp_customer_id=customer_id, role=rol, **datos
    )
    db.add(tarjeta)
    await db.commit()
    await db.refresh(tarjeta)
    logger.info("Tarjeta %s ****%s guardada para user %s",
                tarjeta.brand, tarjeta.last_four, user.id)
    return tarjeta


async def quitar(db: AsyncSession, user: User, card_id: UUID) -> None:
    """Borra la tarjeta de la bóveda de MP y de nuestra tabla."""
    tarjeta = (await db.execute(
        select(PaymentMethod).where(
            PaymentMethod.id == card_id, PaymentMethod.user_id == user.id
        )
    )).scalar_one_or_none()
    if not tarjeta:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada")

    # No dejar al usuario sin medio de pago con la suscripción viva: si es la
    # única y el plan está activo, primero hay que cancelar o cargar otra.
    otras = [t for t in await listar(db, user) if t.id != tarjeta.id]
    if not otras and user.plan == "pro":
        raise HTTPException(status_code=409, detail=(
            "Es tu única tarjeta y tenés la suscripción activa. Agregá otra antes "
            "de quitarla, o cancelá la suscripción."
        ))

    if mp_enabled():
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                await client.delete(
                    f"{MP_API}/v1/customers/{tarjeta.mp_customer_id}/cards/{tarjeta.mp_card_id}",
                    headers=_auth_headers(),
                )
        except httpx.HTTPError as e:
            # Si MP no responde, igual la sacamos de acá: dejarla visible sería
            # peor (el usuario cree que la borró). MP la deja huérfana y no se
            # puede cobrar con ella sin nuestro token.
            logger.warning("No se pudo borrar la tarjeta en MP (sigo local): %s", e)

    era_principal = tarjeta.role == ROL_PRINCIPAL
    await db.delete(tarjeta)
    # Si se fue la principal, la de respaldo pasa a serlo: nunca quedar sin principal.
    if era_principal and otras:
        otras[0].role = ROL_PRINCIPAL
    await db.commit()


async def marcar_principal(
    db: AsyncSession, user: User, card_id: UUID, card_token: str | None = None
) -> list[PaymentMethod]:
    """
    Cambia la tarjeta con la que se cobra la suscripción.

    Con suscripción activa esto NO puede ser un cambio de etiqueta: hay que
    apuntar el preapproval a la tarjeta nueva en Mercado Pago, y MP exige un
    token — que sólo se genera con el código de seguridad, del lado del
    navegador. Si MP no acepta el cambio, el rol tampoco se toca: la pantalla
    nunca dice "se cobra con esta" sobre una tarjeta que MP no va a cobrar.

    Sin suscripción viva (no hay preapproval que actualizar) el rol es sólo
    nuestra preferencia para cuando se suscriba, y se cambia sin token.
    """
    tarjetas = await listar(db, user)
    elegida = next((t for t in tarjetas if t.id == card_id), None)
    if not elegida:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
    if elegida.role == ROL_PRINCIPAL:
        return tarjetas

    preapproval_id = None
    if user.plan == "pro" and mp_enabled():
        from services.mercadopago_service import buscar_preapproval_id
        preapproval_id = await buscar_preapproval_id(user)

    if preapproval_id:
        if not card_token:
            raise HTTPException(status_code=422, detail=(
                "Para cambiar la tarjeta con la que se cobra necesitamos que "
                "confirmes con su código de seguridad."
            ))
        await cambiar_medio_de_pago(preapproval_id, card_token)

    for t in tarjetas:
        t.role = ROL_PRINCIPAL if t.id == elegida.id else ROL_RESPALDO
    await db.commit()
    return await listar(db, user)


async def cambiar_medio_de_pago(preapproval_id: str, card_token: str) -> None:
    """
    Apunta la suscripción a otra tarjeta.

    El `card_token` lo genera el navegador con el SDK de MP a partir de la
    tarjeta guardada MÁS su código de seguridad — MP no permite generarlo sin
    el CVV, y por eso este paso siempre lo confirma la persona.
    """
    _require_mp()
    if not preapproval_id or not card_token:
        raise HTTPException(status_code=422, detail="Faltan datos para actualizar el pago.")
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.put(
            f"{MP_API}/preapproval/{preapproval_id}",
            json={"card_token_id": card_token},
            headers=_auth_headers(),
        )
    if r.status_code >= 300:
        logger.error("MP rechazó el cambio de tarjeta (%s): %s",
                     r.status_code, (r.text or "")[:300])
        raise HTTPException(
            status_code=502,
            detail="Mercado Pago no aceptó el cambio de tarjeta. Probá de nuevo.",
        )
    logger.info("Medio de pago actualizado en el preapproval %s", preapproval_id)


def a_dict(t: PaymentMethod) -> dict:
    """
    Shape que ve el frontend.

    `mp_card_id` va incluido a propósito: es el identificador que el SDK de MP
    necesita en el navegador para pedir un token de esta tarjeta con su código
    de seguridad (reintento de cobro y cambio de tarjeta principal). Por sí solo
    no permite cobrar: hace falta el access token, que nunca sale del backend.
    """
    return {
        "id": str(t.id),
        "mp_card_id": t.mp_card_id,
        "brand": t.brand,
        "last_four": t.last_four,
        "exp_month": t.exp_month,
        "exp_year": t.exp_year,
        "holder_name": t.holder_name,
        "role": t.role,
        "es_principal": t.role == ROL_PRINCIPAL,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }
