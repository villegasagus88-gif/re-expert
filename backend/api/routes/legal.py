"""
Botón de Arrepentimiento — Resolución 424/2020 (Secretaría de Comercio Interior).

Público (SIN sesión, a propósito):
  POST /api/legal/arrepentimiento  → registra el pedido de revocación

Admin (require_admin):
  GET   /api/admin/revocaciones        → bandeja, pendientes primero
  PATCH /api/admin/revocaciones/{id}   → marcar atendido / dejar nota

Por qué no pide sesión: la Resolución exige que el botón inicie la revocación
"sin ningún otro trámite". Obligar a loguearse ES un trámite, y quien quiere
arrepentirse puede no acordarse de la contraseña.

Por qué no cancela ni reembolsa solo: sin sesión, cualquiera podría dar de baja
la suscripción de otro escribiendo su email. El pedido queda registrado y se
atiende; el plazo lo fija la normativa. A quien SÍ tiene sesión, la app le
ofrece además la baja con un clic desde Configuración → Facturación.
"""
# Nota: evitar `from __future__ import annotations` en rutas FastAPI
# (los body params quedan como ForwardRef y rompen el OpenAPI).
import html
import logging
from datetime import UTC, datetime
from uuid import UUID

from core.auth import require_admin
from core.rate_limit import limiter
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from models.base import get_db
from models.revocation_request import RevocationRequest
from models.user import User
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal", tags=["legal"])
admin_router = APIRouter(prefix="/api/admin/revocaciones", tags=["legal-admin"])


class RevocacionRequest(BaseModel):
    """Lo mínimo para poder contestar. `nombre` y `motivo` son opcionales
    porque la ley prohíbe exigir justificación."""

    email: EmailStr
    nombre: str = Field("", max_length=120)
    motivo: str = Field("", max_length=2000)


class RevocacionOut(BaseModel):
    numero: int
    mensaje: str


@router.post(
    "/arrepentimiento",
    response_model=RevocacionOut,
    status_code=201,
    summary="Botón de Arrepentimiento — registra un pedido de revocación",
)
@limiter.limit("5/hour")
async def pedir_revocacion(
    request: Request,
    body: RevocacionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    email = body.email.strip().lower()

    # Si el email corresponde a una cuenta, se enlaza para no tener que buscarla
    # después. Que NO exista no es motivo para rechazar el pedido: puede haberse
    # tipeado distinto, o ser una compra hecha con otro correo, y rebotarlo sería
    # exactamente el "trámite adicional" que la Resolución prohíbe.
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

    pedido = RevocationRequest(
        email=email,
        user_id=user.id if user else None,
        nombre=(body.nombre or "").strip()[:120],
        motivo=(body.motivo or "").strip()[:2000],
    )
    db.add(pedido)
    await db.commit()
    await db.refresh(pedido)

    logger.info(
        "Arrepentimiento #%s registrado (cuenta asociada: %s)",
        pedido.numero, "sí" if user else "no",
    )

    # Los avisos son best-effort y van DESPUÉS del commit: el pedido ya está a
    # salvo en la base, así que un proveedor de mail caído no puede hacerlo
    # desaparecer ni devolverle un error a quien está ejerciendo un derecho.
    await _avisar(pedido, user)

    return RevocacionOut(
        numero=pedido.numero,
        mensaje=(
            f"Recibimos tu solicitud de revocación (N° {pedido.numero}). No tenés que "
            f"hacer ningún otro trámite. Te vamos a contactar a {email} para "
            f"confirmarte la baja y, si corresponde, el reembolso por el mismo medio "
            f"de pago que usaste."
        ),
    )


async def _avisar(pedido: RevocationRequest, user: User | None) -> None:
    """Confirma al usuario y le avisa al titular. Nunca levanta."""
    try:
        from config.settings import settings
        from services.account_security_service import _send_email

        cuerpo = (
            f"Recibimos tu solicitud de revocación N° {pedido.numero}. "
            f"No tenés que hacer ningún otro trámite ni darnos explicaciones. "
            f"Nos vamos a comunicar a esta misma dirección para confirmarte la baja "
            f"y, si corresponde, el reembolso por el mismo medio de pago que usaste."
        )
        await _send_email(
            pedido.email,
            f"Solicitud de revocación N° {pedido.numero} — RE Expert",
            _html_simple("Recibimos tu solicitud", pedido.nombre, cuerpo),
        )

        # Aviso al titular: sin esto el pedido queda esperando a que alguien
        # entre al panel de admin por casualidad.
        destinos = [
            e.strip() for e in (settings.ADMIN_EMAILS or "").split(",") if e.strip()
        ]
        if destinos:
            detalle = (
                f"Pedido N° {pedido.numero} de {pedido.email}"
                f"{' (cuenta existente)' if user else ' (sin cuenta asociada)'}. "
                f"Motivo declarado: {pedido.motivo or 'no declaró'}. "
                f"Hay que atenderlo dentro del plazo de la Res. 424/2020."
            )
            for destino in destinos[:5]:
                await _send_email(
                    destino,
                    f"⚖️ Arrepentimiento N° {pedido.numero} — acción requerida",
                    _html_simple("Nuevo pedido de revocación", "", detalle),
                )
    except Exception:  # noqa: BLE001 — el pedido ya está registrado; el mail es un extra
        logger.warning("No se pudo avisar el arrepentimiento #%s", pedido.numero, exc_info=True)


def _html_simple(titulo: str, nombre: str, cuerpo: str) -> str:
    saludo = f"Hola {html.escape(nombre)}," if nombre else "Hola,"
    return (
        '<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;'
        'max-width:520px;margin:0 auto;padding:24px;color:#1a1a1a">'
        f'<h2 style="margin:0 0 16px;font-size:20px">{html.escape(titulo)}</h2>'
        f'<p style="margin:0 0 12px">{saludo}</p>'
        f'<p style="margin:0 0 16px;line-height:1.55">{html.escape(cuerpo)}</p>'
        '<p style="margin:24px 0 0;font-size:13px;color:#666">RE Expert</p></div>'
    )


# ─────────────────────────── bandeja de admin ───────────────────────────


@admin_router.get("", summary="Pedidos de revocación (pendientes primero)")
async def listar_revocaciones(
    solo_pendientes: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(RevocationRequest)
    if solo_pendientes:
        q = q.where(RevocationRequest.processed.is_(False))
    q = q.order_by(
        RevocationRequest.processed.asc(), RevocationRequest.created_at.asc()
    ).limit(limit)
    filas = (await db.execute(q)).scalars().all()

    pendientes = (await db.execute(
        select(func.count()).select_from(RevocationRequest)
        .where(RevocationRequest.processed.is_(False))
    )).scalar_one()

    return {
        "pendientes": pendientes,
        "items": [
            {
                "id": str(r.id),
                "numero": r.numero,
                "email": r.email,
                "nombre": r.nombre,
                "motivo": r.motivo,
                "tiene_cuenta": r.user_id is not None,
                "processed": r.processed,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
                "admin_note": r.admin_note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in filas
        ],
    }


class ActualizarRevocacion(BaseModel):
    processed: bool | None = None
    admin_note: str | None = Field(None, max_length=2000)


@admin_router.patch("/{pedido_id}", summary="Marcar atendido / dejar nota")
async def actualizar_revocacion(
    pedido_id: UUID,
    body: ActualizarRevocacion = Body(...),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pedido = (await db.execute(
        select(RevocationRequest).where(RevocationRequest.id == pedido_id)
    )).scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if body.admin_note is not None:
        pedido.admin_note = body.admin_note[:2000]
    if body.processed is not None and body.processed != pedido.processed:
        pedido.processed = body.processed
        pedido.processed_at = datetime.now(UTC) if body.processed else None
    await db.commit()
    return {"ok": True}
