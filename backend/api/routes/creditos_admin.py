"""
Créditos — endpoints ADMIN (Fase 2: monitoreo + validación humana).

Flujo:
  POST /api/admin/creditos/monitor            → corre el monitor IA, encola propuestas
  GET  /api/admin/creditos/proposals          → cola de propuestas (default: pendientes)
  POST /api/admin/creditos/proposals/{id}/approve → aplica al catálogo + log
  POST /api/admin/creditos/proposals/{id}/reject  → descarta + log
  GET  /api/admin/creditos/history/{credit_id} → historial de cambios aplicados
  GET  /api/admin/creditos/catalog            → catálogo completo (todos los estados)

Aprobar es lo único que MUTA el catálogo público; siempre lo hace un humano.
Todo queda auditado en credit_change_log.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from api.schemas.creditos import (
    CreditosResponse,
    HistoryResponse,
    MonitorRequest,
    MonitorSummary,
    ProposalsResponse,
    ReviewRequest,
    ReviewResult,
)
from core.auth import require_admin
from fastapi import APIRouter, Depends, HTTPException, Query
from models import get_db
from models.credit import MONITORABLE_FIELDS, Credit, CreditChangeLog, CreditProposal
from models.user import User
from services import creditos_repo
from services.creditos_monitor import run_monitor
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/admin/creditos", tags=["creditos-admin"])

_INT_FIELDS = {"max_term_years", "min_employment_seniority_months", "max_age"}
_FLOAT_FIELDS = {
    "interest_rate_tna", "max_financing_percent", "min_income_ars",
    "property_value_limit_ars", "relacion_cuota_ingreso_max",
}


def _cast_value(field: str, raw: str | None):
    if raw is None:
        return None
    if field in _INT_FIELDS:
        return int(float(raw))
    if field in _FLOAT_FIELDS:
        return float(raw)
    return raw


def _now() -> datetime:
    return datetime.now(UTC)


@router.post("/monitor", response_model=MonitorSummary, summary="Correr monitor IA")
async def monitor(
    body: MonitorRequest | None = None,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MonitorSummary:
    await creditos_repo.seed_if_empty(db)
    summary = await run_monitor(db, (body.credit_ids if body else None))
    return MonitorSummary(**summary)


@router.post("/resync", summary="Re-sincronizar catálogo desde el JSON base (UPSERT)")
async def resync(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Empuja la data curada del JSON a la DB aunque ya esté sembrada. Corrige
    valores viejos sin borrar nada. Pensado para aplicar una corrección manual."""
    return await creditos_repo.resync_from_json(db)


@router.get("/proposals", response_model=ProposalsResponse, summary="Cola de propuestas")
async def list_proposals(
    status_filter: str = Query("pending_review", alias="status"),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ProposalsResponse:
    stmt = (
        select(CreditProposal, Credit.credit_name, Credit.bank_name)
        .outerjoin(Credit, Credit.id == CreditProposal.credit_id)
        .order_by(CreditProposal.detected_at.desc())
    )
    if status_filter and status_filter != "all":
        stmt = stmt.where(CreditProposal.status == status_filter)
    rows = (await db.execute(stmt)).all()
    items = [
        {
            "id": str(p.id),
            "credit_id": p.credit_id,
            "credit_name": cn or "",
            "bank_name": bn or "",
            "change_type": p.change_type,
            "field": p.field,
            "old_value": p.old_value,
            "new_value": p.new_value,
            "source_url": p.source_url,
            "confidence": p.confidence,
            "rationale": p.rationale,
            "status": p.status,
            "detected_at": p.detected_at.isoformat() if p.detected_at else "",
        }
        for (p, cn, bn) in rows
    ]
    return ProposalsResponse(items=items, count=len(items))


async def _get_pending(db: AsyncSession, proposal_id: UUID) -> CreditProposal:
    prop = await db.get(CreditProposal, proposal_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    if prop.status != "pending_review":
        raise HTTPException(status_code=409, detail=f"La propuesta ya está {prop.status}")
    return prop


@router.post(
    "/proposals/{proposal_id}/approve",
    response_model=ReviewResult,
    summary="Aprobar propuesta (aplica al catálogo)",
)
async def approve_proposal(
    proposal_id: UUID,
    body: ReviewRequest | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ReviewResult:
    prop = await _get_pending(db, proposal_id)
    today = _now().strftime("%Y-%m-%d")
    note = body.note if body else None

    if prop.change_type == "new_credit":
        payload = dict(prop.proposed_payload or {})
        if not payload.get("id"):
            raise HTTPException(status_code=400, detail="Propuesta de crédito nuevo sin id")
        if await db.get(Credit, payload["id"]):
            raise HTTPException(status_code=409, detail="Ya existe un crédito con ese id")
        payload.update({"validation_status": "approved", "last_updated_at": today})
        payload.setdefault("status", "active")
        db.add(Credit(**creditos_repo.item_to_kwargs(payload)))
        db.add(CreditChangeLog(
            credit_id=payload["id"], field="*", old_value=None,
            new_value="(alta de crédito)", source=prop.source_url,
            change_type="new_credit", changed_by=admin.id, proposal_id=prop.id,
        ))
        msg = f"Crédito '{payload['id']}' dado de alta y publicado."
    else:
        if prop.field not in MONITORABLE_FIELDS:
            raise HTTPException(status_code=400, detail=f"Campo no editable: {prop.field}")
        credit = await db.get(Credit, prop.credit_id) if prop.credit_id else None
        if not credit:
            raise HTTPException(status_code=404, detail="Crédito de la propuesta no encontrado")
        old = getattr(credit, prop.field, None)
        new = _cast_value(prop.field, prop.new_value)
        setattr(credit, prop.field, new)
        credit.last_updated_at = today
        db.add(CreditChangeLog(
            credit_id=credit.id, field=prop.field,
            old_value=None if old is None else str(old),
            new_value=None if new is None else str(new),
            source=prop.source_url, change_type="approved",
            changed_by=admin.id, proposal_id=prop.id,
        ))
        msg = f"'{prop.field}' actualizado en {credit.id}: {old} → {new}."

    prop.status = "approved"
    prop.reviewed_by = admin.id
    prop.reviewed_at = _now()
    prop.review_note = note
    await db.commit()
    return ReviewResult(
        ok=True, proposal_id=str(prop.id), status="approved", applied=True, message=msg
    )


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ReviewResult,
    summary="Rechazar propuesta",
)
async def reject_proposal(
    proposal_id: UUID,
    body: ReviewRequest | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ReviewResult:
    prop = await _get_pending(db, proposal_id)
    note = body.note if body else None
    db.add(CreditChangeLog(
        credit_id=prop.credit_id or "(nuevo)", field=prop.field,
        old_value=prop.old_value, new_value=prop.new_value,
        source=prop.source_url, change_type="rejected",
        changed_by=admin.id, proposal_id=prop.id,
    ))
    prop.status = "rejected"
    prop.reviewed_by = admin.id
    prop.reviewed_at = _now()
    prop.review_note = note
    await db.commit()
    return ReviewResult(
        ok=True, proposal_id=str(prop.id), status="rejected", applied=False,
        message="Propuesta rechazada.",
    )


@router.get(
    "/history/{credit_id}", response_model=HistoryResponse, summary="Historial de cambios"
)
async def history(
    credit_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    rows = (
        await db.scalars(
            select(CreditChangeLog)
            .where(CreditChangeLog.credit_id == credit_id)
            .order_by(CreditChangeLog.changed_at.desc())
        )
    ).all()
    items = [
        {
            "id": str(r.id), "credit_id": r.credit_id, "field": r.field,
            "old_value": r.old_value, "new_value": r.new_value, "source": r.source,
            "change_type": r.change_type,
            "changed_at": r.changed_at.isoformat() if r.changed_at else "",
        }
        for r in rows
    ]
    return HistoryResponse(credit_id=credit_id, items=items)


@router.get(
    "/catalog", response_model=CreditosResponse, summary="Catálogo completo (admin)"
)
async def admin_catalog(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CreditosResponse:
    await creditos_repo.seed_if_empty(db)
    rows = (
        await db.scalars(select(Credit).order_by(Credit.audience, Credit.bank_name))
    ).all()
    m = creditos_repo.meta()
    return CreditosResponse(
        updated_at=m["updated_at"],
        disclaimer=m["disclaimer"],
        relacion_cuota_ingreso_max_default=m["relacion_cuota_ingreso_max_default"],
        items=[c.to_item_dict() for c in rows],
    )
