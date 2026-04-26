"""
Data ingest endpoint: POST /api/data/ingest.

Recibe un payload estructurado emitido por SOL (o cualquier otro flujo de
carga manual) y lo persiste en la tabla correspondiente según el campo
`type`. La validación por tipo la hace Pydantic vía discriminated union.

Body shape (uno de):

    { "type": "payment",   "amount": 500000, "currency": "ARS", "provider": "Albañil Juan", "concept": "anticipo", "paid_at": "2026-04-20" }
    { "type": "milestone", "name": "Hormigonado losa P1", "status": "done", "completed_at": "2026-04-22" }
    { "type": "material",  "name": "Cemento Loma Negra", "unit": "bolsa", "unit_price": 12500, "supplier": "Easy" }
    { "type": "budget",    "category": "Albañilería", "amount": 8500000, "kind": "planned" }

Respuesta 201:

    { "id": "<uuid>", "type": "payment", "message": "Pago registrado" }
"""
import logging
from datetime import date
from uuid import UUID

from api.schemas.ingest import (
    BudgetIngest,
    IngestRequest,
    IngestResponse,
    MaterialIngest,
    MilestoneIngest,
    PaymentIngest,
)
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from models.base import get_db
from models.budget import Budget
from models.material import Material
from models.message import Message  # noqa: F401  (asegura registro del modelo)
from models.milestone import Milestone
from models.payment import Payment
from models.user import User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["ingest"])


def _build_record(payload: IngestRequest, user_id: UUID):
    """Map a validated Pydantic payload to its corresponding ORM instance."""
    if isinstance(payload, PaymentIngest):
        return Payment(
            user_id=user_id,
            concepto=payload.concept or "Pago vía SOL",
            proveedor=payload.provider,
            monto=payload.amount,
            fecha=payload.paid_at or date.today(),
            estado="pagado",
            notas=payload.notes,
        ), "Pago registrado"

    if isinstance(payload, MilestoneIngest):
        return Milestone(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            due_date=payload.due_date,
            completed_at=payload.completed_at,
        ), "Hito registrado"

    if isinstance(payload, MaterialIngest):
        return Material(
            user_id=user_id,
            name=payload.name,
            unit=payload.unit,
            unit_price=payload.unit_price,
            currency=payload.currency,
            supplier=payload.supplier,
            quoted_at=payload.quoted_at,
            notes=payload.notes,
        ), "Material registrado"

    if isinstance(payload, BudgetIngest):
        return Budget(
            user_id=user_id,
            category=payload.category,
            amount=payload.amount,
            currency=payload.currency,
            kind=payload.kind,
            notes=payload.notes,
        ), "Item de presupuesto registrado"

    # Should be unreachable thanks to discriminated union validation.
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Tipo de ingesta no soportado: {type(payload).__name__}",
    )


@router.post(
    "/ingest",
    status_code=status.HTTP_201_CREATED,
    response_model=IngestResponse,
    summary="Ingestar dato estructurado (payment/milestone/material/budget)",
    responses={
        401: {"description": "Token inválido o ausente"},
        422: {"description": "Payload inválido para el tipo declarado"},
        429: {"description": "Demasiadas cargas, esperá un rato"},
        500: {"description": "Error guardando el dato"},
    },
)
@limiter.limit("60/minute")
async def ingest(
    request: Request,
    payload: IngestRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    record, message = _build_record(payload, current_user.id)

    try:
        db.add(record)
        await db.commit()
        await db.refresh(record)
    except SQLAlchemyError as e:
        await db.rollback()
        logger.exception("Error guardando ingesta tipo=%s: %s", payload.type, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar el dato",
        ) from e

    return IngestResponse(id=record.id, type=payload.type, message=message)
