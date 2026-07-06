"""
Análisis de Planos — API del panel inteligente de planos por proyecto.

Jerarquía: proyecto → planos (con versiones) → análisis IA → observaciones
(alertas con pins) → tareas. Todo scopeado por user_id (multi-tenant).

Los archivos se guardan como BYTEA en Postgres (máx 8 MB por archivo: el
middleware global capea el body en 10 MB). GET /plans/{id}/content sirve los
bytes para el visor del frontend (pdf.js / <img>).
"""
import logging
from datetime import UTC, datetime
from uuid import UUID

from api.schemas.planos import (
    AlertCreate,
    AlertUpdate,
    AnalyzeRequest,
    ChecklistItemUpdate,
    CompareRequest,
    PlanUpdate,
    ProjectAnalyzeRequest,
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskUpdate,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from models.base import get_db
from models.plan_analysis import PlanAlert, PlanAnalysis, PlanFile, PlanProject, PlanTask
from models.user import User
from services.plan_analyzer import (
    DISCLAIMER,
    analyze_plan,
    analyze_project,
    classify_plan,
    compare_plans,
    load_frequent_errors,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/planos", tags=["planos"])

MAX_FILE_SIZE = 8 * 1024 * 1024  # 8 MB (el body total capea en 10 MB)
ALLOWED_EXT = {"pdf": "pdf", "png": "png", "jpg": "jpg", "jpeg": "jpg", "webp": "webp"}
_CONTENT_TYPES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}
_MAGIC = {
    "pdf": (b"%PDF",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8\xff",),
    "webp": (b"RIFF",),
}


# ─────────────────────────── helpers ───────────────────────────

async def _owned_project(db: AsyncSession, project_id: UUID, user_id: UUID) -> PlanProject:
    row = (await db.execute(select(PlanProject).where(
        PlanProject.id == project_id, PlanProject.user_id == user_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return row


async def _owned_plan(db: AsyncSession, plan_id: UUID, user_id: UUID, with_data: bool = False) -> PlanFile:
    q = select(PlanFile).where(PlanFile.id == plan_id, PlanFile.user_id == user_id)
    if not with_data:
        q = q.options(defer(PlanFile.file_data))
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Plano no encontrado")
    return row


def _project_dict(p: PlanProject, extra: dict | None = None) -> dict:
    d = {
        "id": str(p.id), "name": p.name, "obra_type": p.obra_type, "location": p.location,
        "estimated_area": p.estimated_area, "stage": p.stage, "analysis_goal": p.analysis_goal,
        "analysis_goals": p.analysis_goals or [], "analysis_goal_custom": p.analysis_goal_custom or "",
        "client_name": p.client_name, "description": p.description,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
    if extra:
        d.update(extra)
    return d


def _plan_dict(f: PlanFile) -> dict:
    return {
        "id": str(f.id), "project_id": str(f.project_id), "file_name": f.file_name,
        "file_type": f.file_type, "file_size": f.file_size,
        "detected_plan_type": f.detected_plan_type, "discipline": f.discipline,
        "sheet_number": f.sheet_number, "scale": f.scale, "plan_date": f.plan_date,
        "floor_level": f.floor_level, "classification": f.classification or {},
        "status": f.status, "version": f.version, "version_notes": f.version_notes,
        "is_current_version": f.is_current_version,
        "previous_version_id": str(f.previous_version_id) if f.previous_version_id else None,
        "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
        "analyzed_at": f.analyzed_at.isoformat() if f.analyzed_at else None,
    }


def _alert_dict(a: PlanAlert) -> dict:
    return {
        "id": str(a.id), "analysis_id": str(a.analysis_id),
        "plan_id": str(a.plan_id) if a.plan_id else None,
        "project_id": str(a.project_id), "title": a.title, "location": a.location,
        "category": a.category, "description": a.description, "risk": a.risk,
        "impact": a.impact, "recommendation": a.recommendation, "priority": a.priority,
        "confidence": a.confidence, "suggested_action": a.suggested_action,
        "status": a.status, "responsible": a.responsible, "due_date": a.due_date,
        "pin_x": a.pin_x, "pin_y": a.pin_y, "pin_page": a.pin_page,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _analysis_dict(an: PlanAnalysis, alerts: list[PlanAlert] | None = None) -> dict:
    d = {
        "id": str(an.id), "project_id": str(an.project_id),
        "plan_id": str(an.plan_id) if an.plan_id else None,
        "mode": an.mode, "profile": an.profile,
        "compare_plan_id": str(an.compare_plan_id) if an.compare_plan_id else None,
        "summary": an.summary, "detected_data": an.detected_data or {},
        "general_risk": an.general_risk, "confidence": an.confidence,
        "plan_score": an.plan_score or {}, "strengths": an.strengths or [],
        "missing_info": an.missing_info or [], "inconsistencies": an.inconsistencies or [],
        "recommendations": an.recommendations or [],
        "suggested_questions": an.suggested_questions or [], "checklist": an.checklist or [],
        "created_at": an.created_at.isoformat() if an.created_at else None,
        "disclaimer": DISCLAIMER,
    }
    if alerts is not None:
        d["alerts"] = [_alert_dict(a) for a in alerts]
    return d


def _task_dict(t: PlanTask) -> dict:
    return {
        "id": str(t.id), "project_id": str(t.project_id),
        "plan_id": str(t.plan_id) if t.plan_id else None,
        "alert_id": str(t.alert_id) if t.alert_id else None,
        "title": t.title, "description": t.description, "priority": t.priority,
        "responsible": t.responsible, "status": t.status, "due_date": t.due_date,
        "comments": t.comments,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
    }


def _parse_uuid(value: str, field: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field} inválido") from exc


# ─────────────────────────── proyectos ───────────────────────────

@router.get("/projects", summary="Dashboard multi-proyecto")
async def list_projects(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    projects = list((await db.execute(
        select(PlanProject).where(PlanProject.user_id == user.id)
        .order_by(PlanProject.updated_at.desc()))).scalars().all())
    if not projects:
        return {"projects": [], "disclaimer": DISCLAIMER}
    pids = [p.id for p in projects]

    plan_counts = dict((await db.execute(
        select(PlanFile.project_id, func.count()).where(PlanFile.project_id.in_(pids))
        .group_by(PlanFile.project_id))).all())
    alert_rows = (await db.execute(
        select(PlanAlert.project_id, PlanAlert.priority, func.count())
        .where(PlanAlert.project_id.in_(pids),
               PlanAlert.status.notin_(["resuelto", "rechazado", "ignorado"]))
        .group_by(PlanAlert.project_id, PlanAlert.priority))).all()
    task_counts = dict((await db.execute(
        select(PlanTask.project_id, func.count()).where(
            PlanTask.project_id.in_(pids), PlanTask.status.in_(["pendiente", "en_curso"]))
        .group_by(PlanTask.project_id))).all())
    # Último análisis por proyecto (riesgo general + fecha)
    analyses = (await db.execute(
        select(PlanAnalysis.project_id, PlanAnalysis.general_risk, PlanAnalysis.created_at)
        .where(PlanAnalysis.project_id.in_(pids))
        .order_by(PlanAnalysis.created_at.desc()))).all()
    last_by_project: dict = {}
    for pid, risk, created in analyses:
        if pid not in last_by_project:
            last_by_project[pid] = {"general_risk": risk, "last_analysis": created.isoformat()}

    alerts_by_project: dict = {}
    for pid, prio, n in alert_rows:
        alerts_by_project.setdefault(pid, {})[prio] = n

    out = []
    for p in projects:
        ap = alerts_by_project.get(p.id, {})
        last = last_by_project.get(p.id, {})
        out.append(_project_dict(p, {
            "plans_count": plan_counts.get(p.id, 0),
            "critical_alerts": ap.get("critica", 0),
            "high_alerts": ap.get("alta", 0),
            "open_alerts": sum(ap.values()),
            "pending_tasks": task_counts.get(p.id, 0),
            "general_risk": last.get("general_risk", ""),
            "last_analysis": last.get("last_analysis", ""),
        }))
    return {"projects": out, "disclaimer": DISCLAIMER}


@router.post("/projects", status_code=status.HTTP_201_CREATED, summary="Crear proyecto")
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    p = PlanProject(user_id=user.id, **body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _project_dict(p)


@router.get("/projects/{project_id}", summary="Detalle de proyecto (planos + tareas)")
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    p = await _owned_project(db, project_id, user.id)
    plans = list((await db.execute(
        select(PlanFile).options(defer(PlanFile.file_data))
        .where(PlanFile.project_id == p.id)
        .order_by(PlanFile.is_current_version.desc(), PlanFile.uploaded_at.desc()))).scalars().all())
    tasks = list((await db.execute(
        select(PlanTask).where(PlanTask.project_id == p.id)
        .order_by(PlanTask.created_at.desc()))).scalars().all())
    analyses = list((await db.execute(
        select(PlanAnalysis).where(PlanAnalysis.project_id == p.id)
        .order_by(PlanAnalysis.created_at.desc()).limit(30))).scalars().all())
    return {
        "project": _project_dict(p),
        "plans": [_plan_dict(f) for f in plans],
        "tasks": [_task_dict(t) for t in tasks],
        "analyses": [{
            "id": str(a.id), "plan_id": str(a.plan_id) if a.plan_id else None, "mode": a.mode,
            "general_risk": a.general_risk, "confidence": a.confidence,
            "compare_plan_id": str(a.compare_plan_id) if a.compare_plan_id else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        } for a in analyses],
        "disclaimer": DISCLAIMER,
    }


@router.put("/projects/{project_id}", summary="Editar proyecto")
async def update_project(project_id: UUID, body: ProjectUpdate,
                         db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    p = await _owned_project(db, project_id, user.id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return _project_dict(p)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar proyecto")
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    p = await _owned_project(db, project_id, user.id)
    await db.delete(p)
    await db.commit()


# ─────────────────────────── planos (upload / versiones) ───────────────────────────

@router.post("/projects/{project_id}/plans", status_code=status.HTTP_201_CREATED,
             summary="Subir un plano (o una nueva versión de uno existente)")
async def upload_plan(project_id: UUID, file: UploadFile = File(...),
                      version_of: str = Form(default=""),
                      version_notes: str = Form(default=""),
                      db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    project = await _owned_project(db, project_id, user.id)

    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=422, detail="Formato no soportado: usá PDF, PNG, JPG o WEBP")
    file_type = ALLOWED_EXT[ext]
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El archivo supera el máximo de 8 MB")
    if len(data) < 100:
        raise HTTPException(status_code=422, detail="Archivo vacío o corrupto")
    if not any(data.startswith(m) for m in _MAGIC[file_type]):
        raise HTTPException(status_code=422, detail="El contenido no coincide con la extensión del archivo")

    plan = PlanFile(
        project_id=project.id, user_id=user.id,
        file_name=(file.filename or f"plano.{ext}")[:255],
        file_type=file_type, file_data=data, file_size=len(data),
        status="cargado", version_notes=version_notes[:2000],
    )

    if version_of:
        old = await _owned_plan(db, _parse_uuid(version_of, "version_of"), user.id)
        if old.project_id != project.id:
            raise HTTPException(status_code=422, detail="El plano original pertenece a otro proyecto")
        plan.version = old.version + 1
        plan.previous_version_id = old.id
        # Hereda la clasificación editable (el usuario puede corregirla)
        plan.detected_plan_type = old.detected_plan_type
        plan.discipline = old.discipline
        plan.sheet_number = old.sheet_number
        plan.scale = old.scale
        plan.floor_level = old.floor_level
        old.is_current_version = False
        old.status = "version_anterior"

    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _plan_dict(plan)


@router.get("/plans/{plan_id}/content", summary="Bytes del plano (para el visor)")
async def plan_content(plan_id: UUID, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id, with_data=True)
    return Response(
        content=plan.file_data,
        media_type=_CONTENT_TYPES.get(plan.file_type, "application/octet-stream"),
        headers={"Content-Disposition": f'inline; filename="{plan.file_name}"',
                 "Cache-Control": "private, max-age=3600"},
    )


@router.patch("/plans/{plan_id}", summary="Editar clasificación / metadatos del plano")
async def update_plan(plan_id: UUID, body: PlanUpdate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return _plan_dict(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar plano")
async def delete_plan(plan_id: UUID, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id)
    await db.delete(plan)
    await db.commit()


@router.get("/plans/{plan_id}/versions", summary="Historial de versiones del plano")
async def plan_versions(plan_id: UUID, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id)
    # Cadena hacia atrás (previous_version_id) y hacia adelante dentro del proyecto
    all_plans = list((await db.execute(
        select(PlanFile).options(defer(PlanFile.file_data))
        .where(PlanFile.project_id == plan.project_id, PlanFile.user_id == user.id))).scalars().all())
    by_id = {p.id: p for p in all_plans}
    chain = [plan]
    cur = plan
    while cur.previous_version_id and cur.previous_version_id in by_id:
        cur = by_id[cur.previous_version_id]
        chain.append(cur)
    forward = {p.previous_version_id: p for p in all_plans if p.previous_version_id}
    cur = plan
    while cur.id in forward:
        cur = forward[cur.id]
        chain.insert(0, cur)
    return {"versions": [_plan_dict(p) for p in chain]}


# ─────────────────────────── IA: clasificar / analizar / comparar ───────────────────────────

@router.post("/plans/{plan_id}/classify", summary="Clasificación automática del plano (IA)")
async def classify(plan_id: UUID, db: AsyncSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id, with_data=True)
    try:
        result = await classify_plan(plan.file_type, plan.file_data, plan.file_name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Planos: clasificación falló para %s", plan_id)
        plan.status = "pendiente_clasificacion"
        await db.commit()
        raise HTTPException(status_code=502, detail="La clasificación IA falló. Podés cargar los datos manualmente.") from exc

    plan.detected_plan_type = (result.get("plan_type") or "")[:60]
    plan.discipline = (result.get("discipline") or "")[:40]
    plan.sheet_number = (result.get("sheet_number") or "")[:60]
    plan.scale = (result.get("scale") or "")[:40]
    plan.plan_date = (result.get("plan_date") or "")[:40]
    plan.floor_level = (result.get("floor_level") or "")[:80]
    plan.classification = result
    if plan.status == "cargado":
        plan.status = "clasificado"
    await db.commit()
    await db.refresh(plan)
    return _plan_dict(plan)


@router.post("/plans/{plan_id}/analyze", summary="Análisis IA completo del plano")
async def analyze(plan_id: UUID, body: AnalyzeRequest, db: AsyncSession = Depends(get_db),
                  user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id, with_data=True)
    project = await _owned_project(db, plan.project_id, user.id)

    plan.status = "procesando"
    await db.commit()
    try:
        result = await analyze_plan(plan, project, body.mode, body.profile)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Planos: análisis falló para %s", plan_id)
        plan.status = "error"
        await db.commit()
        raise HTTPException(status_code=502, detail="El análisis IA falló. Reintentá en unos minutos.") from exc

    checklist = [{"item": c.get("item", ""), "priority": c.get("priority", "media"),
                  "status": "pendiente", "comment": ""}
                 for c in (result.get("checklist") or [])]
    questions = [{**q, "status": "pendiente"} for q in (result.get("suggested_questions") or [])]

    analysis = PlanAnalysis(
        project_id=project.id, plan_id=plan.id, user_id=user.id,
        mode=body.mode, profile=body.profile,
        summary=result.get("summary", ""),
        detected_data=result.get("detected_data") or {},
        general_risk=result.get("general_risk", "medio"),
        confidence=int(result.get("confidence") or 0),
        plan_score=result.get("plan_score") or {},
        strengths=result.get("strengths") or [],
        missing_info=result.get("missing_info") or [],
        inconsistencies=result.get("inconsistencies") or [],
        recommendations=result.get("recommendations") or [],
        suggested_questions=questions,
        checklist=checklist,
    )
    db.add(analysis)
    await db.flush()  # necesita analysis.id para las alertas

    alerts = []
    for a in (result.get("alerts") or []):
        alerts.append(PlanAlert(
            analysis_id=analysis.id, plan_id=plan.id, project_id=project.id, user_id=user.id,
            title=(a.get("title") or "Observación")[:255],
            location=(a.get("location") or "")[:255],
            category=(a.get("category") or "")[:60],
            description=a.get("description") or "",
            risk=a.get("risk") or "", impact=a.get("impact") or "",
            recommendation=a.get("recommendation") or "",
            priority=a.get("priority") if a.get("priority") in
                ("critica", "alta", "media", "baja", "informativa") else "media",
            confidence=int(a.get("confidence") or 0),
            suggested_action=(a.get("suggested_action") or "")[:255],
        ))
    db.add_all(alerts)
    plan.status = "revision_recomendada" if any(
        al.priority in ("critica", "alta") for al in alerts) else "analizado"
    plan.analyzed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(analysis)
    for al in alerts:
        await db.refresh(al)
    return _analysis_dict(analysis, alerts)


_MAX_PROJECT_ANALYSIS_BYTES = 20 * 1024 * 1024  # límite combinado del análisis integral


def _match_plan_ref(ref: str, plans: list[PlanFile]) -> UUID | None:
    """Mapea el plan_ref devuelto por la IA (nombre de archivo) a un plan_id."""
    if not ref:
        return None
    ref_n = ref.strip().lower()
    for p in plans:
        if p.file_name.strip().lower() == ref_n:
            return p.id
    for p in plans:  # match laxo: uno contiene al otro
        n = p.file_name.strip().lower()
        if ref_n in n or n in ref_n:
            return p.id
    return None


@router.post("/projects/{project_id}/analyze",
             summary="Análisis integral del proyecto (todos los planos juntos, IA)")
async def analyze_whole_project(project_id: UUID, body: ProjectAnalyzeRequest,
                                db: AsyncSession = Depends(get_db),
                                user: User = Depends(get_current_user)):
    project = await _owned_project(db, project_id, user.id)

    q = select(PlanFile).where(PlanFile.project_id == project.id, PlanFile.user_id == user.id)
    if body.plan_ids:
        ids = [_parse_uuid(x, "plan_ids") for x in body.plan_ids]
        q = q.where(PlanFile.id.in_(ids))
    else:
        q = q.where(PlanFile.is_current_version.is_(True))
    plans = list((await db.execute(q.order_by(PlanFile.uploaded_at))).scalars().all())

    if not plans:
        raise HTTPException(status_code=422, detail="El proyecto no tiene planos para analizar")
    if len(plans) > 12:
        raise HTTPException(status_code=422,
                            detail=f"Máximo 12 planos por análisis integral (seleccionaste {len(plans)}). Destildá algunos.")
    total = sum(p.file_size for p in plans)
    if total > _MAX_PROJECT_ANALYSIS_BYTES:
        raise HTTPException(status_code=413, detail=(
            f"Los planos seleccionados suman {total / 1024 / 1024:.1f} MB y el máximo por "
            "análisis integral es 20 MB. Destildá los más pesados o analizalos por separado."))

    try:
        result = await analyze_project(plans, project, body.mode, body.profile, body.focus)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Planos: análisis integral falló para proyecto %s", project_id)
        raise HTTPException(status_code=502, detail="El análisis integral falló. Reintentá en unos minutos.") from exc

    checklist = [{"item": c.get("item", ""), "priority": c.get("priority", "media"),
                  "status": "pendiente", "comment": ""}
                 for c in (result.get("checklist") or [])]
    questions = [{**qq, "status": "pendiente"} for qq in (result.get("suggested_questions") or [])]
    detected = result.get("detected_data") or {}
    detected["plans_included"] = [p.file_name for p in plans]

    analysis = PlanAnalysis(
        project_id=project.id, plan_id=None, user_id=user.id,
        mode=body.mode, profile=body.profile,
        summary=result.get("summary", ""),
        detected_data=detected,
        general_risk=result.get("general_risk", "medio"),
        confidence=int(result.get("confidence") or 0),
        plan_score=result.get("plan_score") or {},
        strengths=result.get("strengths") or [],
        missing_info=result.get("missing_info") or [],
        inconsistencies=result.get("inconsistencies") or [],
        recommendations=result.get("recommendations") or [],
        suggested_questions=questions,
        checklist=checklist,
    )
    db.add(analysis)
    await db.flush()

    alerts = []
    for a in (result.get("alerts") or []):
        alerts.append(PlanAlert(
            analysis_id=analysis.id,
            plan_id=_match_plan_ref(a.get("plan_ref") or "", plans),
            project_id=project.id, user_id=user.id,
            title=(a.get("title") or "Observación")[:255],
            location=(a.get("location") or "")[:255],
            category=(a.get("category") or "")[:60],
            description=a.get("description") or "",
            risk=a.get("risk") or "", impact=a.get("impact") or "",
            recommendation=a.get("recommendation") or "",
            priority=a.get("priority") if a.get("priority") in
                ("critica", "alta", "media", "baja", "informativa") else "media",
            confidence=int(a.get("confidence") or 0),
            suggested_action=(a.get("suggested_action") or "")[:255],
        ))
    db.add_all(alerts)
    await db.commit()
    await db.refresh(analysis)
    for al in alerts:
        await db.refresh(al)
    return _analysis_dict(analysis, alerts)


@router.post("/compare", summary="Comparar dos planos o versiones (IA)")
async def compare(body: CompareRequest, db: AsyncSession = Depends(get_db),
                  user: User = Depends(get_current_user)):
    plan_a = await _owned_plan(db, _parse_uuid(body.plan_a, "plan_a"), user.id, with_data=True)
    plan_b = await _owned_plan(db, _parse_uuid(body.plan_b, "plan_b"), user.id, with_data=True)
    if plan_a.project_id != plan_b.project_id:
        raise HTTPException(status_code=422, detail="Los planos deben pertenecer al mismo proyecto")
    if plan_a.file_size + plan_b.file_size > 14 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Los dos planos juntos superan el límite para comparar (14 MB)")
    project = await _owned_project(db, plan_a.project_id, user.id)

    try:
        result = await compare_plans(plan_a, plan_b, project, body.focus)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Planos: comparación falló %s vs %s", plan_a.id, plan_b.id)
        raise HTTPException(status_code=502, detail="La comparación IA falló. Reintentá en unos minutos.") from exc

    analysis = PlanAnalysis(
        project_id=project.id, plan_id=plan_a.id, user_id=user.id,
        mode="comparacion", profile="", compare_plan_id=plan_b.id,
        summary=result.get("summary", ""),
        detected_data={
            "changes": result.get("changes") or [],
            "added": result.get("added") or [],
            "removed": result.get("removed") or [],
            "measure_changes": result.get("measure_changes") or [],
            "impact": result.get("impact") or [],
        },
        general_risk=result.get("general_risk", "medio"),
        confidence=int(result.get("confidence") or 0),
        recommendations=result.get("recommendations") or [],
        inconsistencies=result.get("changes") or [],
    )
    db.add(analysis)
    await db.flush()
    alerts = []
    for a in (result.get("alerts") or []):
        alerts.append(PlanAlert(
            analysis_id=analysis.id, plan_id=plan_a.id, project_id=project.id, user_id=user.id,
            title=(a.get("title") or "Inconsistencia")[:255],
            location=(a.get("location") or "")[:255],
            category=(a.get("category") or "comparacion")[:60],
            description=a.get("description") or "",
            risk=a.get("risk") or "", impact=a.get("impact") or "",
            recommendation=a.get("recommendation") or "",
            priority=a.get("priority") if a.get("priority") in
                ("critica", "alta", "media", "baja", "informativa") else "media",
            confidence=int(a.get("confidence") or 0),
            suggested_action=(a.get("suggested_action") or "")[:255],
        ))
    db.add_all(alerts)
    await db.commit()
    await db.refresh(analysis)
    for al in alerts:
        await db.refresh(al)
    return _analysis_dict(analysis, alerts)


# ─────────────────────────── análisis / checklist ───────────────────────────

@router.get("/plans/{plan_id}/analyses", summary="Historial de análisis del plano")
async def plan_analyses(plan_id: UUID, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    plan = await _owned_plan(db, plan_id, user.id)
    rows = list((await db.execute(
        select(PlanAnalysis).where(PlanAnalysis.plan_id == plan.id)
        .order_by(PlanAnalysis.created_at.desc()))).scalars().all())
    return {"analyses": [{
        "id": str(a.id), "mode": a.mode, "profile": a.profile,
        "general_risk": a.general_risk, "confidence": a.confidence,
        "compare_plan_id": str(a.compare_plan_id) if a.compare_plan_id else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in rows]}


@router.get("/analyses/{analysis_id}", summary="Análisis completo (con observaciones)")
async def get_analysis(analysis_id: UUID, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    an = (await db.execute(select(PlanAnalysis).where(
        PlanAnalysis.id == analysis_id, PlanAnalysis.user_id == user.id))).scalar_one_or_none()
    if not an:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    alerts = list((await db.execute(
        select(PlanAlert).where(PlanAlert.analysis_id == an.id)
        .order_by(PlanAlert.created_at))).scalars().all())
    return _analysis_dict(an, alerts)


@router.patch("/analyses/{analysis_id}/checklist", summary="Actualizar ítem del checklist")
async def update_checklist(analysis_id: UUID, body: ChecklistItemUpdate,
                           db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    an = (await db.execute(select(PlanAnalysis).where(
        PlanAnalysis.id == analysis_id, PlanAnalysis.user_id == user.id))).scalar_one_or_none()
    if not an:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    items = list(an.checklist or [])
    if body.index >= len(items):
        raise HTTPException(status_code=422, detail="Ítem de checklist inexistente")
    items[body.index] = {**items[body.index], "status": body.status,
                         "comment": body.comment, "updated_at": datetime.now(UTC).isoformat()}
    an.checklist = items
    await db.commit()
    return {"checklist": items}


# ─────────────────────────── observaciones (alertas + pins) ───────────────────────────

@router.post("/alerts", status_code=status.HTTP_201_CREATED, summary="Crear observación manual (pin)")
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    an = (await db.execute(select(PlanAnalysis).where(
        PlanAnalysis.id == _parse_uuid(body.analysis_id, "analysis_id"),
        PlanAnalysis.user_id == user.id))).scalar_one_or_none()
    if not an:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    alert = PlanAlert(
        analysis_id=an.id, plan_id=an.plan_id, project_id=an.project_id, user_id=user.id,
        title=body.title, description=body.description, category=body.category,
        location=body.location, recommendation=body.recommendation,
        priority=body.priority, confidence=100, suggested_action="Observación manual",
        pin_x=body.pin_x, pin_y=body.pin_y, pin_page=body.pin_page,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return _alert_dict(alert)


@router.patch("/alerts/{alert_id}", summary="Actualizar observación (estado, prioridad, pin…)")
async def update_alert(alert_id: UUID, body: AlertUpdate, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    alert = (await db.execute(select(PlanAlert).where(
        PlanAlert.id == alert_id, PlanAlert.user_id == user.id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    data = body.model_dump(exclude_none=True, exclude={"clear_pin"})
    for k, v in data.items():
        setattr(alert, k, v)
    if body.clear_pin:
        alert.pin_x = None
        alert.pin_y = None
    await db.commit()
    await db.refresh(alert)
    return _alert_dict(alert)


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar observación manual")
async def delete_alert(alert_id: UUID, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    alert = (await db.execute(select(PlanAlert).where(
        PlanAlert.id == alert_id, PlanAlert.user_id == user.id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    await db.delete(alert)
    await db.commit()


# ─────────────────────────── tareas ───────────────────────────

@router.get("/projects/{project_id}/tasks", summary="Tareas del proyecto")
async def list_tasks(project_id: UUID, db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    await _owned_project(db, project_id, user.id)
    rows = list((await db.execute(
        select(PlanTask).where(PlanTask.project_id == project_id)
        .order_by(PlanTask.created_at.desc()))).scalars().all())
    return {"tasks": [_task_dict(t) for t in rows]}


@router.post("/projects/{project_id}/tasks", status_code=status.HTTP_201_CREATED, summary="Crear tarea")
async def create_task(project_id: UUID, body: TaskCreate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    await _owned_project(db, project_id, user.id)
    t = PlanTask(
        project_id=project_id, user_id=user.id, title=body.title,
        description=body.description, priority=body.priority,
        responsible=body.responsible, due_date=body.due_date,
        plan_id=_parse_uuid(body.plan_id, "plan_id") if body.plan_id else None,
        alert_id=_parse_uuid(body.alert_id, "alert_id") if body.alert_id else None,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return _task_dict(t)


@router.patch("/tasks/{task_id}", summary="Actualizar tarea")
async def update_task(task_id: UUID, body: TaskUpdate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    t = (await db.execute(select(PlanTask).where(
        PlanTask.id == task_id, PlanTask.user_id == user.id))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    if body.status == "resuelta" and not t.resolved_at:
        t.resolved_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(t)
    return _task_dict(t)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar tarea")
async def delete_task(task_id: UUID, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    t = (await db.execute(select(PlanTask).where(
        PlanTask.id == task_id, PlanTask.user_id == user.id))).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    await db.delete(t)
    await db.commit()


# ─────────────────────────── biblioteca de errores frecuentes ───────────────────────────

@router.get("/biblioteca", summary="Biblioteca de errores frecuentes en planos")
async def biblioteca(_user: User = Depends(get_current_user)):
    return {"errors": load_frequent_errors(), "disclaimer": DISCLAIMER}
