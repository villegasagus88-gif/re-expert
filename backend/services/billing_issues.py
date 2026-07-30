"""
Cobros rechazados: período de gracia y reintento con la tarjeta de respaldo.

Por qué existe: la causa número uno de bajas involuntarias en un SaaS es una
tarjeta que se venció o no tenía fondos *ese día*. Cortar el acceso en el primer
rechazo castiga a un cliente que quiere seguir pagando.

Cómo funciona:
  1. Mercado Pago avisa por webhook que un cobro se rechazó.
  2. Se abre un `BillingIssue` con 5 días de gracia. **El acceso NO se corta.**
  3. Al usuario le aparece el aviso en la app (y por email) con el motivo en
     criollo y un botón para pagar con su tarjeta de respaldo.
  4. Confirma con el código de seguridad → se apunta la suscripción a esa
     tarjeta → MP reintenta.
  5. Cuando MP informa un cobro aprobado, el issue se cierra solo.

Límite del proveedor: MP exige el código de seguridad para generar un token
desde una tarjeta guardada, así que el paso 4 no puede ser automático. Es lo
que está declarado en los Términos.
"""
from __future__ import annotations

import html
import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from models.payment_method import BillingIssue
from models.user import User
from services import cards_service as cards
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Días que el usuario conserva el acceso mientras resuelve el pago.
DIAS_DE_GRACIA = 5

# Motivos de rechazo de MP → explicación que entiende una persona.
_MOTIVOS = {
    "cc_rejected_insufficient_amount": "La tarjeta no tenía fondos suficientes.",
    "cc_rejected_high_risk": "El banco rechazó el pago por seguridad.",
    "cc_rejected_bad_filled_card_number": "El número de la tarjeta es incorrecto.",
    "cc_rejected_bad_filled_date": "La fecha de vencimiento es incorrecta.",
    "cc_rejected_bad_filled_security_code": "El código de seguridad es incorrecto.",
    "cc_rejected_call_for_authorize": "Tenés que autorizar el pago con tu banco.",
    "cc_rejected_card_disabled": "La tarjeta está inhabilitada.",
    "cc_rejected_card_error": "Hubo un problema con la tarjeta.",
    "cc_rejected_duplicated_payment": "Se detectó un pago duplicado.",
    "cc_rejected_max_attempts": "Se alcanzó el máximo de intentos.",
    "cc_rejected_expired_card": "La tarjeta está vencida.",
}


def explicar(motivo: str | None) -> str:
    return _MOTIVOS.get(motivo or "", "No pudimos procesar el cobro con tu tarjeta.")


async def obtener_issue_abierto(db: AsyncSession, user: User) -> dict | None:
    """El cobro pendiente de resolver, si hay alguno."""
    issue = (await db.execute(
        select(BillingIssue)
        .where(BillingIssue.user_id == user.id, BillingIssue.resolved.is_(False))
        .order_by(BillingIssue.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    if not issue:
        return None
    gracia = issue.grace_until
    if gracia is not None and gracia.tzinfo is None:
        gracia = gracia.replace(tzinfo=UTC)
    return {
        "id": str(issue.id),
        "motivo": explicar(issue.reason),
        "desde": issue.created_at.isoformat() if issue.created_at else None,
        "gracia_hasta": gracia.isoformat() if gracia else None,
        "gracia_vencida": bool(gracia and datetime.now(UTC) >= gracia),
        # El usuario ya cambió el medio de pago y MP está por reintentar: el
        # cartel deja de ser "no pudimos cobrarte" y pasa a "reintento en curso".
        "reintento_pedido": (
            issue.retry_requested_at.isoformat() if issue.retry_requested_at else None
        ),
    }


async def abrir_issue(db: AsyncSession, user_id, motivo: str, payment_id: str = "") -> None:
    """
    Registra un cobro rechazado y avisa al usuario.

    Idempotente por dos vías: el chequeo previo y, si dos entregas del webhook
    corren a la vez, el índice único parcial de `billing_issues` (un solo issue
    abierto por usuario) que convierte la carrera en un IntegrityError que se
    traga acá. Un webhook no puede devolver 500 por esto: MP lo reintenta en
    loop.
    """
    # `.first()`, no `.scalar_one_or_none()`: si por una carrera quedaran dos
    # abiertos, explotar acá dejaría el webhook devolviendo 500 para siempre.
    existente = (await db.execute(
        select(BillingIssue)
        .where(BillingIssue.user_id == user_id, BillingIssue.resolved.is_(False))
        .order_by(BillingIssue.created_at.desc())
        .limit(1)
    )).scalars().first()
    if existente:
        return
    db.add(BillingIssue(
        user_id=user_id,
        reason=(motivo or "")[:80],
        mp_payment_id=(payment_id or "")[:64],
        grace_until=datetime.now(UTC) + timedelta(days=DIAS_DE_GRACIA),
    ))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.info("Cobro rechazado para user %s: ya había un issue abierto", user_id)
        return
    logger.info("Cobro rechazado para user %s (%s) — %d días de gracia",
                user_id, motivo, DIAS_DE_GRACIA)
    await _avisar_cobro_rechazado(db, user_id, motivo)


async def _avisar_cobro_rechazado(db: AsyncSession, user_id, motivo: str) -> None:
    """
    Le avisa al usuario que el cobro se rechazó, por mail y por sus canales.

    Es lo que sostiene la promesa de los Términos («te avisamos el motivo»):
    sin esto el aviso sólo existiría para quien entre a la app por su cuenta,
    y se enteraría cuando ya perdió el acceso. Best-effort: un mail caído no
    puede tumbar el webhook de Mercado Pago, que MP reintentaría en loop.
    """
    try:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return
        hasta = (datetime.now(UTC) + timedelta(days=DIAS_DE_GRACIA)).strftime("%d/%m/%Y")
        texto = (
            f"{explicar(motivo)} Tenés hasta el {hasta} para resolverlo sin perder "
            f"el acceso: entrá a Configuración → Facturación y reintentá el cobro "
            f"con tu tarjeta de respaldo, o cargá otra tarjeta."
        )
        from services.account_security_service import _send_email
        from services.notification_dispatcher import dispatch

        await _send_email(user.email, "No pudimos cobrarte — RE Expert",
                          _html_aviso("No pudimos cobrarte", user.full_name or "", texto))
        try:
            await dispatch(db, user, channel="in_app",
                           title="No pudimos cobrarte", body=texto)
        except Exception:  # noqa: BLE001 — el canal es un extra sobre el mail
            logger.info("Aviso de cobro rechazado: sin canal para user %s", user_id)
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo avisar el cobro rechazado a %s", user_id, exc_info=True)


def _html_aviso(titulo: str, nombre: str, cuerpo: str) -> str:
    """Mail de facturación. Sin bloque de código ni pie de seguridad: esto no es
    una verificación de identidad y mezclarlos confunde (y entrena mal)."""
    saludo = f"Hola {html.escape(nombre)}," if nombre else "Hola,"
    return (
        '<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;'
        'max-width:520px;margin:0 auto;padding:24px;color:#1a1a1a">'
        f'<h2 style="margin:0 0 16px;font-size:20px">{html.escape(titulo)}</h2>'
        f'<p style="margin:0 0 12px">{saludo}</p>'
        f'<p style="margin:0 0 16px;line-height:1.55">{html.escape(cuerpo)}</p>'
        '<p style="margin:24px 0 0;font-size:13px;color:#666">RE Expert — '
        'Configuración → Facturación</p></div>'
    )


async def marcar_downgrade_diferido(db: AsyncSession, user_id) -> bool:
    """
    Marca que el corte de acceso queda pendiente hasta que venza la gracia.

    Devuelve True si hay una gracia vigente que justifique diferirlo (y en ese
    caso el llamador NO baja el plan). False si no hay issue abierto o la gracia
    ya venció: ahí el corte va derecho, como siempre.
    """
    issue = (await db.execute(
        select(BillingIssue)
        .where(BillingIssue.user_id == user_id, BillingIssue.resolved.is_(False))
        .order_by(BillingIssue.created_at.desc())
        .limit(1)
    )).scalars().first()
    if not issue:
        return False
    gracia = issue.grace_until
    if gracia is None:
        return False
    if gracia.tzinfo is None:
        gracia = gracia.replace(tzinfo=UTC)
    if datetime.now(UTC) >= gracia:
        return False
    issue.pending_downgrade = True
    return True


async def aplicar_downgrades_vencidos(db: AsyncSession) -> int:
    """
    Corta el acceso de quienes tenían el downgrade diferido y ya se les venció
    la gracia. Lo corre el scheduler una vez por día.

    Es la contracara de `marcar_downgrade_diferido`: sin esto, diferir el corte
    equivaldría a regalar el servicio para siempre, porque MP manda el webhook
    de `paused` una sola vez.
    """
    ahora = datetime.now(UTC)
    pendientes = (await db.execute(
        select(BillingIssue).where(
            BillingIssue.resolved.is_(False),
            BillingIssue.pending_downgrade.is_(True),
            BillingIssue.grace_until.isnot(None),
            BillingIssue.grace_until <= ahora,
        )
    )).scalars().all()
    cortados = 0
    for issue in pendientes:
        user = (await db.execute(
            select(User).where(User.id == issue.user_id)
        )).scalar_one_or_none()
        if user and user.plan == "pro":
            user.plan = "inactive"
            cortados += 1
            logger.info("Gracia vencida: user %s pasa a inactive", issue.user_id)
        issue.pending_downgrade = False
    if pendientes:
        await db.commit()
    return cortados


async def cerrar_issues(db: AsyncSession, user_id) -> int:
    """Cierra los cobros pendientes. Se llama cuando MP informa un pago aprobado."""
    abiertos = (await db.execute(
        select(BillingIssue).where(
            BillingIssue.user_id == user_id, BillingIssue.resolved.is_(False)
        )
    )).scalars().all()
    for i in abiertos:
        i.resolved = True
        i.resolved_at = datetime.now(UTC)
    if abiertos:
        await db.commit()
        logger.info("Cobro regularizado para user %s (%d issues cerrados)",
                    user_id, len(abiertos))
    return len(abiertos)


async def resolver_con_respaldo(db: AsyncSession, user: User, card_token: str) -> dict:
    """
    Apunta la suscripción a otra tarjeta para que MP reintente el cobro.

    No cierra el issue: eso lo hace el webhook cuando el cobro salga aprobado.
    Prometer que quedó resuelto antes de que MP lo confirme sería mentirle al
    usuario.
    """
    issue = await obtener_issue_abierto(db, user)
    if not issue:
        raise HTTPException(status_code=400, detail="No tenés ningún cobro pendiente.")

    preapproval_id = getattr(user, "mp_preapproval_id", None)
    if not preapproval_id:
        # El id vive en MP asociado al external_reference del usuario.
        from services.mercadopago_service import buscar_preapproval_id
        preapproval_id = await buscar_preapproval_id(user)
    if not preapproval_id:
        raise HTTPException(
            status_code=400,
            detail="No encontramos tu suscripción en Mercado Pago. Escribinos y lo resolvemos.",
        )

    await cards.cambiar_medio_de_pago(preapproval_id, card_token)

    # Dejar constancia de que el reintento está en marcha. El issue sigue
    # abierto (lo cierra el webhook cuando MP acredite), pero la app ya no
    # muestra el mismo cartel rojo como si el usuario no hubiera hecho nada.
    fila = (await db.execute(
        select(BillingIssue)
        .where(BillingIssue.user_id == user.id, BillingIssue.resolved.is_(False))
        .order_by(BillingIssue.created_at.desc())
        .limit(1)
    )).scalars().first()
    if fila:
        fila.retry_requested_at = datetime.now(UTC)
        await db.commit()

    return {
        "ok": True,
        "message": (
            "Listo, actualizamos tu medio de pago. Mercado Pago va a reintentar el "
            "cobro en las próximas horas y te avisamos cuando se acredite."
        ),
    }
