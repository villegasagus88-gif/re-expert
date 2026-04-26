"""
Project dashboard and milestone CRUD endpoints.
One project per user (enforced via unique constraint on user_id).
"""
from datetime import datetime, timezone
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
from models.base import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models.project import ProjectMilestone, Project
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/project", tags=["project"])


def _compute_indicators(project: Project) -> ProjectIndicators:
    pb = float(project.presupuesto_base)
    ac = float(project.costo_real)
    avance_real = float(project.avance_real_pct)
    avance_plan = float(project.avance_plan_pct)

    ev = pb * (avance_real / 100) if pb > 0 else 0.0
    pv = pb * (avance_plan / 100) if pb > 0 else 0.0

    cpi = round(ev / ac, 3) if ac > 0 else None
    spi = round(ev / pv, 3) if pv > 0 else None
    eac_val = pb / cpi if cpi and cpi > 0 else None
    desvio = round(eac_val - pb, 2) if eac_val is not None else None
    pct_ejecutado = round(ac / pb * 100, 1) if pb > 0 else 0.0

    return ProjectIndicators(
        cpi=round(cpi, 2) if cpi is not None else None,
        spi=round(spi, 2) if spi is not None else None,
        eac=Decimal(str(round(eac_val, 2))) if eac_val is not None else None,
        desvio_proyectado=Decimal(str(desvio)) if desvio is not None else None,
        pct_ejecutado=pct_ejecutado,
    )


async def _get_user_project(db: AsyncSession, user_id: UUID) -> Project | None:
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .options(selectinload(Project.milestones))
    )
    return result.scalar_one_or_none()


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
    return ProjectDashboard(
        project=ProjectOut.model_validate(project),
        indicators=_compute_indicators(project),
        milestones=[MilestoneOut.model_validate(m) for m in project.milestones],
    )


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

    return ProjectDashboard(
        project=ProjectOut.model_validate(project),
        indicators=_compute_indicators(project),
        milestones=[],
    )


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
    project.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(project)

    return ProjectDashboard(
        project=ProjectOut.model_validate(project),
        indicators=_compute_indicators(project),
        milestones=[MilestoneOut.model_validate(m) for m in project.milestones],
    )


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
    result = await db.execute(
        select(ProjectMilestone)
        .where(ProjectMilestone.user_id == user.id)
        .order_by(ProjectMilestone.orden.asc())
    )
    return [MilestoneOut.model_validate(m) for m in result.scalars().all()]


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
    milestone.updated_at = datetime.now(timezone.utc)

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
