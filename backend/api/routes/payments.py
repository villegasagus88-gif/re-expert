"""
Payments CRUD endpoints.

All endpoints are scoped to the authenticated user — users can only
read/write their own payment records.
"""
from decimal import Decimal
from uuid import UUID

from api.schemas.payment import (
    CreatePaymentRequest,
    PaymentOut,
    PaymentsListResponse,
    PaymentsSummary,
    UpdatePaymentRequest,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.base import get_db
from models.payment import Payment
from models.project import Project
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _build_summary(rows: list[Payment]) -> PaymentsSummary:
    totals: dict[str, Decimal] = {"pagado": Decimal(0), "pendiente": Decimal(0), "cancelado": Decimal(0)}
    counts: dict[str, int] = {"pagado": 0, "pendiente": 0, "cancelado": 0}
    for p in rows:
        estado = p.estado if p.estado in totals else "pendiente"
        totals[estado] += p.monto
        counts[estado] += 1
    return PaymentsSummary(
        total_pagado=totals["pagado"],
        total_pendiente=totals["pendiente"],
        total_cancelado=totals["cancelado"],
        grand_total=totals["pagado"] + totals["pendiente"],
        count_pagado=counts["pagado"],
        count_pendiente=counts["pendiente"],
        count_cancelado=counts["cancelado"],
        count_total=len(rows),
    )


@router.get(
    "",
    response_model=PaymentsListResponse,
    summary="Listar pagos del usuario",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def list_payments(
    estado: str | None = Query(None, pattern="^(pendiente|pagado|cancelado)$"),
    project_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # base = pagos del usuario, opcionalmente acotados a un proyecto.
    base = select(Payment).where(Payment.user_id == user.id)
    if project_id is not None:
        base = base.where(Payment.project_id == project_id)
    q = base.order_by(Payment.fecha.desc())
    if estado:
        q = q.where(Payment.estado == estado)
    result = await db.execute(q)
    rows = list(result.scalars().all())

    # El summary va sobre todos los pagos (del proyecto), sin filtrar por estado.
    if estado:
        all_rows = list((await db.execute(base)).scalars().all())
        summary = _build_summary(all_rows)
    else:
        summary = _build_summary(rows)

    return PaymentsListResponse(
        items=[PaymentOut.model_validate(p) for p in rows],
        summary=summary,
        total=len(rows),
    )


@router.post(
    "",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pago",
    responses={401: {"description": "Token inválido o ausente"}},
)
async def create_payment(
    body: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Resolver/validar el proyecto del pago (multi-proyecto). Si viene project_id,
    # validamos que sea del usuario; si no, lo asignamos al primer proyecto del
    # usuario (compat con 1 proyecto). Un id ajeno/inexistente queda en None.
    pq = select(Project).where(Project.user_id == user.id)
    if body.project_id is not None:
        pq = pq.where(Project.id == body.project_id)
    else:
        pq = pq.order_by(Project.created_at.asc())
    proj = (await db.execute(pq)).scalars().first()
    # Si vino un project_id EXPLÍCITO y no es del usuario (o no existe), fallar
    # claro en vez de crear un pago huérfano (project_id=None) silenciosamente.
    if body.project_id is not None and proj is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    payment = Payment(
        user_id=user.id,
        project_id=proj.id if proj else None,
        concepto=body.concepto,
        proveedor=body.proveedor,
        monto=body.monto,
        fecha=body.fecha,
        estado=body.estado,
        categoria=body.categoria,
        notas=body.notas,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)


@router.put(
    "/{payment_id}",
    response_model=PaymentOut,
    summary="Editar pago",
    responses={
        401: {"description": "Token inválido o ausente"},
        404: {"description": "Pago no encontrado"},
    },
)
async def update_payment(
    payment_id: UUID,
    body: UpdatePaymentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.user_id == user.id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    await db.commit()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar pago",
    responses={
        401: {"description": "Token inválido o ausente"},
        404: {"description": "Pago no encontrado"},
    },
)
async def delete_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.user_id == user.id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    await db.delete(payment)
    await db.commit()
