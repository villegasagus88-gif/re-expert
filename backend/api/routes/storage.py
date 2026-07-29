"""
Almacenamiento — los archivos del usuario, en un solo lugar.

Alimenta Configuración → Almacenamiento: listar con buscador, renombrar, borrar
y descargar. Es un AGREGADOR: no crea tablas propias ni duplica bytes, lee las
tablas que ya existen. Hoy la única fuente es `plan_files` (Análisis de Planos),
que es la única tabla del sistema con bytes de un usuario.

Por qué NO aparecen los entregables del chat (PDF/XLSX de SOL): se suben a un
bucket con URL firmada y no dejan fila en la DB, así que no hay `user_id` con el
que filtrarlos. Listarlos exigiría una tabla nueva escrita desde los generadores
(dominio del chat) — queda para una fase 2 coordinada.

Diseño:
- El id que viaja al front es compuesto: "planos:<uuid>". Cuando entre una
  segunda fuente el contrato no cambia.
- El listado NUNCA toca `file_data` (BYTEA): se hace un select explícito de
  columnas, así ni por accidente se bajan los bytes de todos los planos.
- El borrado cascadea (análisis, observaciones, versiones). Sin `?force=true`
  devuelve 409 con el detalle de qué se pierde, para que el front pueda avisar.
"""
import logging
import re
from urllib.parse import quote
from uuid import UUID

from api.schemas.storage import RenameRequest
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from models.base import get_db
from models.plan_analysis import PlanAlert, PlanAnalysis, PlanFile, PlanProject, PlanTask
from models.user import User
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/storage", tags=["storage"])

# Fuentes conocidas. El label es lo que se muestra en la columna "Sección".
FUENTES = {"planos": "Análisis de Planos"}

_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 200

# Columnas del listado. Explícitas a propósito: `PlanFile.file_data` (BYTEA con
# el PDF entero) NO está acá y no puede colarse por un `select(PlanFile)`.
# Hay un test que falla si alguien la agrega.
_COLS_LISTADO = (
    PlanFile.id, PlanFile.file_name, PlanFile.file_type, PlanFile.file_size,
    PlanFile.uploaded_at, PlanFile.project_id, PlanFile.version,
    PlanFile.is_current_version, PlanFile.status,
    PlanProject.name.label("project_name"),
)


# ─────────────────────────── helpers ───────────────────────────

def _parse_id(file_id: str) -> tuple[str, UUID]:
    """"planos:<uuid>" → ("planos", UUID). 404 si no tiene forma válida."""
    fuente, _, ref = file_id.partition(":")
    if fuente not in FUENTES or not ref:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    try:
        return fuente, UUID(ref)
    except ValueError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado") from None


async def _owned_plan_meta(db: AsyncSession, plan_id: UUID, user_id: UUID):
    """Metadatos del plano SIN los bytes. 404 si no es del usuario."""
    row = (await db.execute(
        select(PlanFile.id, PlanFile.file_name, PlanFile.file_type, PlanFile.file_size,
               PlanFile.project_id, PlanFile.is_current_version)
        .where(PlanFile.id == plan_id, PlanFile.user_id == user_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return row


def _item(row) -> dict:
    """Fila del listado → item de la API (mismo shape en lista y en PATCH)."""
    return {
        "id": f"planos:{row.id}",
        "source": "planos",
        "source_label": FUENTES["planos"],
        "ref_id": str(row.id),
        "name": row.file_name,
        "file_type": row.file_type,
        "size_bytes": row.file_size or 0,
        "created_at": row.uploaded_at.isoformat() if row.uploaded_at else None,
        "container": {
            "id": str(row.project_id),
            "name": row.project_name or "",
        },
        "version": row.version,
        "is_current": bool(row.is_current_version),
        "status": row.status or "",
        "can_rename": True,
        "can_delete": True,
        "can_download": True,
    }


def _content_disposition(nombre: str) -> str:
    """
    Content-Disposition seguro (RFC 5987).

    El nombre lo elige el usuario, así que el ASCII de fallback va sin comillas
    ni control chars (evita romper o inyectar el header) y aparte se manda el
    nombre completo UTF-8 percent-encoded para los navegadores modernos.
    """
    ascii_fb = re.sub(r'[^A-Za-z0-9._\- ]', "_", nombre).strip() or "archivo"
    return f'attachment; filename="{ascii_fb}"; filename*=UTF-8\'\'{quote(nombre, safe="")}'


# ─────────────────────────── endpoints ───────────────────────────

@router.get("/files", summary="Archivos del usuario (con buscador y filtros)")
async def list_files(
    q: str = Query("", max_length=120, description="Busca en nombre, tipo y proyecto"),
    type: str = Query("", max_length=10, alias="type", description="pdf | png | jpg | webp"),
    source: str = Query("", max_length=20, description="Fuente (hoy solo 'planos')"),
    project_id: UUID | None = Query(None, description="Filtrar por proyecto"),
    sort: str = Query("recent", pattern="^(recent|oldest|name|size)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Fuente desconocida → lista vacía (no 404: el front puede pedir una fuente
    # que todavía no existe sin romperse).
    if source and source not in FUENTES:
        return {"items": [], "page": page, "page_size": page_size, "total": 0,
                "summary": {"total_files": 0, "total_bytes": 0, "by_type": {}}}

    # Select EXPLÍCITO de columnas: `file_data` (BYTEA) no entra ni por error.
    base = (
        select(*_COLS_LISTADO)
        .join(PlanProject, PlanProject.id == PlanFile.project_id)
        .where(PlanFile.user_id == user.id)
    )

    if q:
        # El buscador es uno solo y busca donde el usuario espera: nombre del
        # archivo, tipo y nombre del proyecto.
        patron = f"%{q.strip()}%"
        base = base.where(or_(
            PlanFile.file_name.ilike(patron),
            PlanFile.file_type.ilike(patron),
            PlanProject.name.ilike(patron),
        ))
    if type:
        t = type.lower().lstrip(".")
        if t == "jpeg":
            t = "jpg"
        base = base.where(PlanFile.file_type == t)
    if project_id:
        base = base.where(PlanFile.project_id == project_id)

    # Totales del filtro actual (sin paginar) en una sola pasada.
    sub = base.subquery()
    tot = (await db.execute(
        select(func.count(sub.c.id), func.coalesce(func.sum(sub.c.file_size), 0))
    )).first()
    total, total_bytes = int(tot[0] or 0), int(tot[1] or 0)

    por_tipo = {
        r[0]: int(r[1])
        for r in (await db.execute(
            select(sub.c.file_type, func.count()).group_by(sub.c.file_type)
        )).all()
    }

    orden = {
        "recent": PlanFile.uploaded_at.desc(),
        "oldest": PlanFile.uploaded_at.asc(),
        "name": PlanFile.file_name.asc(),
        "size": PlanFile.file_size.desc(),
    }[sort]

    filas = (await db.execute(
        base.order_by(orden, PlanFile.id).offset((page - 1) * page_size).limit(page_size)
    )).all()

    return {
        "items": [_item(f) for f in filas],
        "page": page,
        "page_size": page_size,
        "total": total,
        "summary": {"total_files": total, "total_bytes": total_bytes, "by_type": por_tipo},
    }


@router.get("/summary", summary="Espacio usado por el usuario")
async def storage_summary(db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    row = (await db.execute(
        select(func.count(PlanFile.id), func.coalesce(func.sum(PlanFile.file_size), 0))
        .where(PlanFile.user_id == user.id)
    )).first()
    por_tipo = {
        r[0]: int(r[1])
        for r in (await db.execute(
            select(PlanFile.file_type, func.count())
            .where(PlanFile.user_id == user.id).group_by(PlanFile.file_type)
        )).all()
    }
    total, total_bytes = int(row[0] or 0), int(row[1] or 0)
    return {
        "total_files": total,
        "total_bytes": total_bytes,
        "by_source": {"planos": total},
        "by_type": por_tipo,
        # No existe cuota por usuario en el producto: no inventamos una.
        "quota_bytes": None,
    }


@router.patch("/files/{file_id}", summary="Renombrar un archivo")
async def rename_file(file_id: str, body: RenameRequest,
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    _, ref = _parse_id(file_id)
    await _owned_plan_meta(db, ref, user.id)   # 404 si no es suyo

    # UPDATE directo: cargar el objeto traería `file_data` (hasta 8 MB del PDF)
    # a memoria nada más que para tocar el nombre. El WHERE repite el user_id
    # para que no dependa del chequeo de arriba.
    res = await db.execute(
        update(PlanFile)
        .where(PlanFile.id == ref, PlanFile.user_id == user.id)
        .values(file_name=body.name)
    )
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    await db.commit()

    fila = (await db.execute(
        select(*_COLS_LISTADO)
        .join(PlanProject, PlanProject.id == PlanFile.project_id)
        .where(PlanFile.id == ref, PlanFile.user_id == user.id)
    )).first()
    if not fila:
        # Carrera real: otra pestaña borró el archivo entre el commit de arriba
        # y esta lectura. 404 limpio en vez de un 500 con traceback.
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return _item(fila)


@router.delete("/files/{file_id}", summary="Eliminar un archivo")
async def delete_file(file_id: str, force: bool = Query(False),
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    """
    Borra el archivo. El borrado arrastra cosas (los FK de Postgres cascadean):
    los análisis IA del plano y sus observaciones se van con él, las tareas
    quedan huérfanas y la cadena de versiones se corta. Sin `?force=true`
    devolvemos 409 con esos números para que el front pueda avisar de verdad en
    vez de un "¿seguro?" genérico. Con `force=true` se borra.
    """
    _, ref = _parse_id(file_id)
    meta = await _owned_plan_meta(db, ref, user.id)

    if not force:
        analisis = int((await db.execute(select(func.count(PlanAnalysis.id)).where(
            PlanAnalysis.plan_id == ref))).scalar() or 0)
        alertas = int((await db.execute(select(func.count(PlanAlert.id)).where(
            PlanAlert.plan_id == ref))).scalar() or 0)
        tareas = int((await db.execute(select(func.count(PlanTask.id)).where(
            PlanTask.plan_id == ref))).scalar() or 0)
        versiones = int((await db.execute(select(func.count(PlanFile.id)).where(
            PlanFile.previous_version_id == ref))).scalar() or 0)
        # ¿Queda el proyecto sin ningún plano vigente? Ahí el análisis integral
        # del proyecto deja de poder correr, así que conviene avisarlo.
        vigentes = int((await db.execute(select(func.count(PlanFile.id)).where(
            PlanFile.project_id == meta.project_id,
            PlanFile.is_current_version.is_(True)))).scalar() or 0)
        ultimo_vigente = bool(meta.is_current_version and vigentes <= 1)

        if analisis or alertas or tareas or versiones or ultimo_vigente:
            raise HTTPException(status_code=409, detail={
                "message": "Este archivo tiene trabajo asociado que se va a perder.",
                "impact": {
                    "analyses": analisis, "alerts": alertas, "tasks": tareas,
                    "versions": versiones, "last_current_of_project": ultimo_vigente,
                },
                "hint": "Repetí con ?force=true para confirmar.",
            })

    # DELETE directo por el mismo motivo que el rename: no hace falta traer los
    # bytes para borrar la fila. Las cascadas las hacen los FK de Postgres (los
    # modelos no declaran relationship(), así que no hay cascada de ORM que perder).
    res = await db.execute(
        delete(PlanFile).where(PlanFile.id == ref, PlanFile.user_id == user.id)
    )
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/files/{file_id}/download", summary="Descargar el archivo")
async def download_file(file_id: str, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    _, ref = _parse_id(file_id)
    # Acá SÍ queremos los bytes, pero solo esas tres columnas.
    row = (await db.execute(
        select(PlanFile.file_data, PlanFile.file_name, PlanFile.file_type)
        .where(PlanFile.id == ref, PlanFile.user_id == user.id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return Response(
        content=row.file_data,
        media_type=_CONTENT_TYPES.get(row.file_type, "application/octet-stream"),
        headers={
            "Content-Disposition": _content_disposition(row.file_name),
            # no-store: es contenido privado y el nombre puede cambiar.
            "Cache-Control": "private, no-store",
        },
    )
