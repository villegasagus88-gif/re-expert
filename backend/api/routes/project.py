"""
Project dashboard and milestone CRUD endpoints.
One project per user (enforced via unique constraint on user_id).
"""
import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from api.schemas.project import (
    CreateMilestoneRequest,
    CreateProjectRequest,
    MilestoneOut,
    ProjectDashboard,
    ProjectIndicators,
    ProjectOut,
    UpdateMilestoneRequest,
    UpdateProjectRequest,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from models.base import get_db
from models.payment import Payment
from models.project import Project, ProjectMilestone
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/project", tags=["project"])
logger = logging.getLogger(__name__)


def _compute_indicators(
    project: Project,
    ac: Decimal | None = None,
    comprometido: Decimal | None = None,
    gasto_desde_pagos: bool = False,
) -> ProjectIndicators:
    # ac = costo real (AC). Si viene None se usa el costo_real cargado a mano;
    # normalmente viene de la suma de pagos "pagado" (ver _aggregate_payments).
    pb = float(project.presupuesto_base)
    ac_f = float(ac if ac is not None else project.costo_real)
    avance_real = float(project.avance_real_pct)
    avance_plan = float(project.avance_plan_pct)

    ev = pb * (avance_real / 100) if pb > 0 else 0.0
    pv = pb * (avance_plan / 100) if pb > 0 else 0.0

    cpi = round(ev / ac_f, 3) if ac_f > 0 else None
    spi = round(ev / pv, 3) if pv > 0 else None
    eac_val = (pb * ac_f / ev) if (ev > 0 and ac_f > 0) else None  # EAC exacto (BAC/CPI sin arrastrar el redondeo del CPI)
    desvio = round(eac_val - pb, 2) if eac_val is not None else None
    pct_ejecutado = round(ac_f / pb * 100, 1) if pb > 0 else 0.0

    return ProjectIndicators(
        cpi=round(cpi, 2) if cpi is not None else None,
        spi=round(spi, 2) if spi is not None else None,
        eac=Decimal(str(round(eac_val, 2))) if eac_val is not None else None,
        desvio_proyectado=Decimal(str(desvio)) if desvio is not None else None,
        pct_ejecutado=pct_ejecutado,
        costo_real=Decimal(str(round(ac_f, 2))),
        comprometido=comprometido,
        gasto_desde_pagos=gasto_desde_pagos,
    )


async def _get_user_project(db: AsyncSession, user_id: UUID) -> Project | None:
    # Sin selectinload de milestones a propósito: si la tabla project_milestones
    # tuviera un problema de esquema, igual queremos poder cargar el proyecto.
    # Los hitos se cargan aparte, de forma tolerante (ver _load_milestones).
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    return result.scalar_one_or_none()


async def _load_milestones(db: AsyncSession, project_id: UUID) -> list[ProjectMilestone]:
    """Carga los hitos de un proyecto de forma tolerante.

    Si la consulta falla (p.ej. inconsistencia de esquema), devuelve [] en vez
    de tumbar el panel entero — el proyecto y sus indicadores se siguen viendo.
    No hace rollback a propósito: el objeto Project ya está materializado y la
    sesión se cierra al terminar el request.
    """
    try:
        result = await db.execute(
            select(ProjectMilestone)
            .where(ProjectMilestone.project_id == project_id)
            .order_by(ProjectMilestone.orden.asc())
        )
        return list(result.scalars().all())
    except Exception:  # noqa: BLE001 — un problema con hitos no debe romper el dashboard
        logger.exception("No se pudieron cargar hitos del proyecto %s", project_id)
        return []


async def _aggregate_payments(db: AsyncSession, user_id: UUID) -> dict | None:
    """Suma los pagos del usuario para derivar el gasto real (AC) del proyecto.

    Como hay un proyecto por usuario, los pagos del usuario son los del proyecto.
    El AC sale de los pagos en estado 'pagado'; lo 'pendiente' es el compromiso a
    futuro; el desglose por categoría sirve para los costos por rubro. Tolerante:
    si falla, devuelve None y el dashboard cae al costo_real cargado a mano.
    """
    try:
        result = await db.execute(select(Payment).where(Payment.user_id == user_id))
        rows = list(result.scalars().all())
    except Exception:  # noqa: BLE001 — un problema con pagos no debe romper el panel
        logger.exception("No se pudieron agregar pagos del usuario %s", user_id)
        return None

    pagado = sum((p.monto for p in rows if p.estado == "pagado"), Decimal(0))
    pendiente = sum((p.monto for p in rows if p.estado == "pendiente"), Decimal(0))
    por_categoria: dict[str, Decimal] = {}
    for p in rows:
        if p.estado == "pagado":
            cat = (p.categoria or "").strip().lower() or "otros"
            por_categoria[cat] = por_categoria.get(cat, Decimal(0)) + p.monto
    tiene_pagos = any(p.estado in ("pagado", "pendiente") for p in rows)
    return {
        "pagado": pagado,
        "pendiente": pendiente,
        "por_categoria": por_categoria,
        "tiene_pagos": tiene_pagos,
    }


async def _build_dashboard(db: AsyncSession, project: Project) -> ProjectDashboard:
    """Arma el dashboard: deriva el gasto real (AC) de los pagos, calcula los
    indicadores EVM con ese AC, y carga los hitos. Todo tolerante: ningún
    sub-fallo (pagos o hitos) debe tumbar el panel. Lo usan get/create/update."""
    pay = await _aggregate_payments(db, project.user_id)
    if pay and pay["tiene_pagos"]:
        ac: Decimal | None = pay["pagado"]
        comprometido = pay["pendiente"]
        from_pagos = True
        por_categoria = pay["por_categoria"]
    else:
        ac = None  # sin pagos → usa el costo_real cargado a mano (compat)
        comprometido = pay["pendiente"] if pay else None
        from_pagos = False
        por_categoria = pay["por_categoria"] if pay else {}

    try:
        indicators = _compute_indicators(
            project, ac=ac, comprometido=comprometido, gasto_desde_pagos=from_pagos
        )
    except Exception:  # noqa: BLE001 — datos raros no deben tumbar el dashboard
        logger.exception("compute_indicators falló para proyecto %s", project.id)
        indicators = ProjectIndicators(
            cpi=None, spi=None, eac=None, desvio_proyectado=None, pct_ejecutado=0.0,
            costo_real=project.costo_real, comprometido=comprometido, gasto_desde_pagos=False,
        )

    milestones = await _load_milestones(db, project.id)
    return ProjectDashboard(
        project=ProjectOut.model_validate(project),
        indicators=indicators,
        milestones=[MilestoneOut.model_validate(m) for m in milestones],
        gasto_por_categoria=por_categoria,
    )


@router.get(
    "/dashboard",
    response_model=ProjectDashboard,
    summary="Dashboard del proyecto con indicadores calculados",
    responses={
        401: {"description": "Token inválido"},
        404: {"description": "Sin proyecto"},
    },
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await _get_user_project(db, user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Sin proyecto configurado")
    return await _build_dashboard(db, project)


@router.post(
    "",
    response_model=ProjectDashboard,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto (uno por usuario)",
    responses={
        401: {"description": "Token inválido"},
        409: {"description": "Ya existe un proyecto para este usuario"},
    },
)
async def create_project(
    body: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Project).where(Project.user_id == user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un proyecto para este usuario")

    project = Project(
        user_id=user.id,
        **body.model_dump(exclude_none=False),
    )
    # Store JSONB fields as plain dicts/lists
    project.costos_rubros = [r.model_dump() for r in body.costos_rubros]
    project.alertas = [a.model_dump() for a in body.alertas]
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return await _build_dashboard(db, project)


@router.put(
    "",
    response_model=ProjectDashboard,
    summary="Actualizar proyecto",
    responses={
        401: {"description": "Token inválido"},
        404: {"description": "Sin proyecto"},
    },
)
async def update_project(
    body: UpdateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await _get_user_project(db, user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Sin proyecto configurado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "costos_rubros" and value is not None:
            setattr(project, field, [r.model_dump() if hasattr(r, "model_dump") else r for r in value])
        elif field == "alertas" and value is not None:
            setattr(project, field, [a.model_dump() if hasattr(a, "model_dump") else a for a in value])
        else:
            setattr(project, field, value)
    project.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(project)

    return await _build_dashboard(db, project)


# ── ProjectMilestones ──

@router.get(
    "/milestones",
    response_model=list[MilestoneOut],
    summary="Listar hitos del proyecto",
)
async def list_milestones(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(ProjectMilestone)
            .where(ProjectMilestone.user_id == user.id)
            .order_by(ProjectMilestone.orden.asc())
        )
        rows = result.scalars().all()
    except Exception:  # noqa: BLE001 — un problema con hitos no debe romper la vista
        logger.exception("No se pudieron listar hitos del usuario %s", user.id)
        return []
    return [MilestoneOut.model_validate(m) for m in rows]


@router.post(
    "/milestones",
    response_model=MilestoneOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear hito",
    responses={404: {"description": "Sin proyecto"}},
)
async def create_milestone(
    body: CreateMilestoneRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    proj_result = await db.execute(select(Project).where(Project.user_id == user.id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Sin proyecto configurado")

    milestone = ProjectMilestone(
        project_id=project.id,
        user_id=user.id,
        nombre=body.nombre,
        fecha_objetivo=body.fecha_objetivo,
        fecha_real=body.fecha_real,
        estado=body.estado,
        detalle=body.detalle,
        orden=body.orden,
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    return MilestoneOut.model_validate(milestone)


@router.put(
    "/milestones/{milestone_id}",
    response_model=MilestoneOut,
    summary="Actualizar hito",
    responses={404: {"description": "Hito no encontrado"}},
)
async def update_milestone(
    milestone_id: UUID,
    body: UpdateMilestoneRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProjectMilestone).where(ProjectMilestone.id == milestone_id, ProjectMilestone.user_id == user.id)
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="Hito no encontrado")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(milestone, field, value)
    milestone.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(milestone)
    return MilestoneOut.model_validate(milestone)


@router.delete(
    "/milestones/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar hito",
    responses={404: {"description": "Hito no encontrado"}},
)
async def delete_milestone(
    milestone_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProjectMilestone).where(ProjectMilestone.id == milestone_id, ProjectMilestone.user_id == user.id)
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="Hito no encontrado")

    await db.delete(milestone)
    await db.commit()
