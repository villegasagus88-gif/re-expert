"""
Reportes de error — Ayuda → Informar un error.

Usuario (autenticado):
  POST /api/bugs        → crea un reporte, devuelve su número de ticket
  GET  /api/bugs/mine   → sus propios reportes con el estado

Admin (require_admin):
  GET   /api/admin/bugs            → bandeja con filtros + contadores por estado
  PATCH /api/admin/bugs/{id}       → cambiar estado y/o dejar nota interna
  GET   /api/admin/bugs/new-count  → badge de "reportes sin abrir"

Separación deliberada: la vista del usuario NUNCA serializa `admin_note` ni el
contexto técnico, y solo puede ver lo suyo (filtro por user_id en la query, no
por parámetro del cliente).
"""
# Nota: evitar `from __future__ import annotations` en rutas FastAPI
# (los body params quedan como ForwardRef y rompen el OpenAPI).
import logging
from uuid import UUID

from api.schemas.bug_report import (
    BugReportAdminOut,
    BugReportOut,
    BugReportsAdminResponse,
    BugReportsResponse,
    CreateBugReportRequest,
    NewBugsCount,
    UpdateBugReportRequest,
)
from core.auth import get_current_user, require_admin
from core.rate_limit import limiter
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from models.base import get_db
from models.bug_report import BugReport
from models.user import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bugs", tags=["bugs"])
admin_router = APIRouter(prefix="/api/admin/bugs", tags=["bugs-admin"])

# Tope del contexto técnico: es input del cliente y va a JSONB. Sin tope, un
# cliente hostil podría mandar megabytes por reporte.
_MAX_CONTEXT_KEYS = 20
_MAX_CONTEXT_VALUE = 500


def _clean_context(raw: dict) -> dict:
    """Acota el contexto del cliente: N claves, valores string recortados."""
    out: dict[str, str] = {}
    for k, v in list(raw.items())[:_MAX_CONTEXT_KEYS]:
        if v is None:
            continue
        out[str(k)[:40]] = str(v)[:_MAX_CONTEXT_VALUE]
    return out


# ─────────────────────────── usuario ───────────────────────────

@router.post(
    "",
    response_model=BugReportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Informar un error",
)
@limiter.limit("10/hour")
async def create_bug_report(
    request: Request,
    body: CreateBugReportRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = BugReport(
        user_id=current_user.id,
        reporter_email=current_user.email,
        title=body.title.strip(),
        description=body.description.strip(),
        section=(body.section or None),
        notes=(body.notes.strip() if body.notes else None),
        severity=body.severity,
        context=_clean_context(body.context or {}),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    logger.info("bug_report #%s creado por %s", report.ticket, current_user.id)
    return BugReportOut.model_validate(report)


@router.get("/mine", response_model=BugReportsResponse, summary="Mis reportes")
async def list_my_bug_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
):
    rows = list((await db.execute(
        select(BugReport)
        .where(BugReport.user_id == current_user.id)
        .order_by(BugReport.created_at.desc())
        .limit(limit)
    )).scalars().all())
    total = (await db.execute(
        select(func.count()).select_from(BugReport).where(BugReport.user_id == current_user.id)
    )).scalar() or 0
    return BugReportsResponse(
        items=[BugReportOut.model_validate(r) for r in rows], total=total
    )


# ─────────────────────────── admin ───────────────────────────

@admin_router.get("", response_model=BugReportsAdminResponse, summary="Bandeja de reportes")
async def list_bug_reports_admin(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    estado: str | None = Query(None, pattern="^(new|in_review|resolved|dismissed)$"),
    q: str | None = Query(None, max_length=120, description="Busca en título/descripción/email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    filtro = None
    if estado:
        filtro = BugReport.status == estado
    if q:
        patron = f"%{q.strip()}%"
        busq = (
            BugReport.title.ilike(patron)
            | BugReport.description.ilike(patron)
            | BugReport.reporter_email.ilike(patron)
        )
        filtro = busq if filtro is None else (filtro & busq)

    base = select(BugReport)
    if filtro is not None:
        base = base.where(filtro)

    total_q = select(func.count()).select_from(BugReport)
    if filtro is not None:
        total_q = total_q.where(filtro)
    total = (await db.execute(total_q)).scalar() or 0

    rows = list((await db.execute(
        base.order_by(BugReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all())

    # Contadores por estado (para las pestañas de la bandeja), en UNA query.
    counts = {s: 0 for s in ("new", "in_review", "resolved", "dismissed")}
    for st, n in (await db.execute(
        select(BugReport.status, func.count()).group_by(BugReport.status)
    )).all():
        counts[st] = n

    return BugReportsAdminResponse(
        items=[BugReportAdminOut.model_validate(r) for r in rows],
        total=total,
        counts=counts,
    )


@admin_router.get("/new-count", response_model=NewBugsCount, summary="Reportes sin abrir")
async def count_new_bugs(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    n = (await db.execute(
        select(func.count()).select_from(BugReport).where(BugReport.status == "new")
    )).scalar() or 0
    return NewBugsCount(new=n)


@admin_router.patch("/{report_id}", response_model=BugReportAdminOut, summary="Actualizar reporte")
async def update_bug_report(
    report_id: UUID,
    body: UpdateBugReportRequest = Body(...),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(BugReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if body.status is not None:
        report.status = body.status
    if body.admin_note is not None:
        report.admin_note = body.admin_note.strip() or None
    await db.commit()
    await db.refresh(report)
    return BugReportAdminOut.model_validate(report)
