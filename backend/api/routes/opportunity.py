"""
Opportunity Scanner — endpoints CRUD + análisis.

Todo scopeado al usuario autenticado (Model.user_id == user.id). El análisis
combina motor determinístico (services.opportunity_scanner) + capa LLM tolerante.
"""
import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from api.schemas.opportunity import (
    CreateOpportunityRequest,
    ExtractRequest,
    ExtractResponse,
    OpportunitiesListResponse,
    OpportunitiesSummary,
    OpportunityOut,
    UpdateOpportunityRequest,
)
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from models.base import get_db
from models.opportunity import Opportunity
from models.user import User
from services.opportunity_scanner import analyze_opportunity, extract_inputs
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])
logger = logging.getLogger(__name__)

_SCALAR_FIELDS = (
    "titulo", "zona", "ciudad", "tipo_inmueble", "objetivo",
    "superficie_terreno_m2", "m2_vendibles", "precio_pedido",
    "costo_obra_m2", "precio_venta_m2", "moneda", "estado_pipeline",
)


def _dec(v) -> float | None:
    return float(v) if isinstance(v, Decimal) else v


def _opp_inputs(opp: Opportunity) -> dict:
    """Merge de los inputs JSONB + columnas escalares (las escalares mandan)."""
    base = dict(opp.inputs or {})
    base.update({
        "titulo": opp.titulo, "zona": opp.zona, "ciudad": opp.ciudad,
        "tipo_inmueble": opp.tipo_inmueble, "objetivo": opp.objetivo,
        "superficie_terreno_m2": opp.superficie_terreno_m2, "m2_vendibles": opp.m2_vendibles,
        "precio_pedido": _dec(opp.precio_pedido), "costo_obra_m2": _dec(opp.costo_obra_m2),
        "precio_venta_m2": _dec(opp.precio_venta_m2), "moneda": opp.moneda,
    })
    return base


async def _get_owned(db: AsyncSession, opportunity_id: UUID, user_id: UUID) -> Opportunity:
    result = await db.execute(
        select(Opportunity).where(
            Opportunity.id == opportunity_id, Opportunity.user_id == user_id
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return opp


@router.get("", response_model=OpportunitiesListResponse, summary="Listar oportunidades (Deal Room)")
async def list_opportunities(
    estado_pipeline: str | None = Query(None, pattern="^(nueva|en_analisis|shortlist|descartada|cerrada)$"),
    tipo_inmueble: str | None = Query(None, max_length=40),
    min_score: float | None = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Opportunity).where(Opportunity.user_id == user.id).order_by(Opportunity.created_at.desc())
    if estado_pipeline:
        q = q.where(Opportunity.estado_pipeline == estado_pipeline)
    if tipo_inmueble:
        q = q.where(Opportunity.tipo_inmueble == tipo_inmueble)
    if min_score is not None:
        q = q.where(Opportunity.score >= min_score)
    rows = list((await db.execute(q)).scalars().all())

    # Summary siempre sobre TODAS las oportunidades del usuario (no el filtro),
    # calculado en SQL (antes: se recargaba la tabla entera y se agregaba en
    # Python — doble full-scan por request en un Deal Room activo).
    agg = (await db.execute(
        select(
            func.count().label("count_total"),
            func.count().filter(Opportunity.estado_pipeline == "shortlist").label("count_shortlist"),
            func.count().filter(Opportunity.estado_pipeline == "descartada").label("count_descartada"),
            func.avg(Opportunity.score).label("avg_score"),
        ).where(Opportunity.user_id == user.id)
    )).one()
    summary = OpportunitiesSummary(
        count_total=agg.count_total or 0,
        count_shortlist=agg.count_shortlist or 0,
        count_descartada=agg.count_descartada or 0,
        avg_score=round(float(agg.avg_score), 1) if agg.avg_score is not None else None,
    )
    return OpportunitiesListResponse(
        items=[OpportunityOut.model_validate(r) for r in rows],
        summary=summary,
        total=len(rows),
    )


@router.post("", response_model=OpportunityOut, status_code=status.HTTP_201_CREATED, summary="Crear oportunidad")
async def create_opportunity(
    body: CreateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = body.model_dump()
    inputs = data.pop("inputs", {}) or {}
    opp = Opportunity(user_id=user.id, **data)
    opp.inputs = inputs
    db.add(opp)
    await db.commit()
    await db.refresh(opp)
    return OpportunityOut.model_validate(opp)


@router.get("/{opportunity_id}", response_model=OpportunityOut, summary="Detalle de oportunidad")
async def get_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return OpportunityOut.model_validate(await _get_owned(db, opportunity_id, user.id))


@router.put("/{opportunity_id}", response_model=OpportunityOut, summary="Editar / mover de etapa")
async def update_opportunity(
    opportunity_id: UUID,
    body: UpdateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    opp = await _get_owned(db, opportunity_id, user.id)
    update_data = body.model_dump(exclude_unset=True)
    inputs = update_data.pop("inputs", None)
    for field, value in update_data.items():
        if field in _SCALAR_FIELDS and value is not None:
            setattr(opp, field, value)
    if inputs is not None:
        opp.inputs = {**(opp.inputs or {}), **inputs}
    opp.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(opp)
    return OpportunityOut.model_validate(opp)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar oportunidad")
async def delete_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    opp = await _get_owned(db, opportunity_id, user.id)
    await db.delete(opp)
    await db.commit()


@router.post("/{opportunity_id}/analyze", response_model=OpportunityOut, summary="Analizar oportunidad (motor + IA)")
@limiter.limit("15/minute")
async def analyze(
    request: Request,
    opportunity_id: UUID,
    use_llm: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    opp = await _get_owned(db, opportunity_id, user.id)
    analysis = await analyze_opportunity(_opp_inputs(opp), use_llm=use_llm)
    opp.analysis = analysis
    opp.score = float(analysis["score"]) if analysis.get("score") is not None else None
    opp.recomendacion = analysis.get("recomendacion_label")
    opp.last_analyzed_at = datetime.now(UTC)
    if opp.estado_pipeline == "nueva":
        opp.estado_pipeline = "en_analisis"
    opp.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(opp)
    return OpportunityOut.model_validate(opp)


@router.post("/extract", response_model=ExtractResponse, summary="Extraer datos desde URL/texto (IA)")
@limiter.limit("10/minute")
async def extract(
    request: Request,
    body: ExtractRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await extract_inputs(body.texto, body.url)
    return ExtractResponse(**result)
