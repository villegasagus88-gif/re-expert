"""
Workspaces ("Proyectos" en la UI) + memoria de workspace.

Endpoints scopeados al usuario autenticado. Ningún usuario puede ver/modificar
workspaces o memoria de otro.

- POST   /api/workspaces                     → crear workspace
- GET    /api/workspaces                     → listar workspaces (con conteo de chats)
- GET    /api/workspaces/{id}                → detalle de un workspace
- PATCH  /api/workspaces/{id}                → editar nombre/color/desc/archivar
- DELETE /api/workspaces/{id}                → eliminar (cascade memoria; chats quedan sueltos)
- GET    /api/workspaces/{id}/memory         → listar memoria del workspace
- POST   /api/workspaces/{id}/memory         → agregar/actualizar item de memoria
- PATCH  /api/workspaces/{id}/memory/{mid}   → editar item
- DELETE /api/workspaces/{id}/memory/{mid}   → borrar item
"""
import io
import re
from datetime import UTC, datetime
from uuid import UUID

from api.schemas.workspace import (
    MemoryItemCreate,
    MemoryItemOut,
    MemoryItemUpdate,
    MemoryListOut,
    WorkspaceCreate,
    WorkspaceOut,
    WorkspaceUpdate,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from models.base import get_db
from models.conversation import Conversation
from models.user import User
from models.workspace import Workspace, WorkspaceMemory
from services.memory_export import render_memory_csv, render_memory_pdf
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

# Hard cap por usuario para evitar abuso/UI overflow. Razonable para Real Estate:
# un developer activo suele tener <20 proyectos vivos a la vez.
MAX_WORKSPACES_PER_USER = 50
MAX_MEMORY_ITEMS_PER_WORKSPACE = 200


def _ws_to_out(ws: Workspace, conv_count: int = 0) -> WorkspaceOut:
    return WorkspaceOut(
        id=str(ws.id),
        name=ws.name,
        color=ws.color,
        description=ws.description,
        archived_at=ws.archived_at,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
        conversation_count=conv_count,
    )


def _mem_to_out(item: WorkspaceMemory) -> MemoryItemOut:
    return MemoryItemOut(
        id=str(item.id),
        key=item.key,
        value=item.value,
        source=item.source,
        confidence=item.confidence,
        last_used_at=item.last_used_at,
        confirmed_at=item.confirmed_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _get_owned_workspace(
    db: AsyncSession, user_id: UUID, workspace_id: UUID
) -> Workspace:
    """Carga el workspace verificando ownership. 404 si no existe / no pertenece."""
    ws = await db.get(Workspace, workspace_id)
    if ws is None or ws.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace no encontrado"
        )
    return ws


# ── Workspace CRUD ──

@router.post(
    "",
    response_model=WorkspaceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear workspace",
    responses={409: {"description": "Límite de workspaces alcanzado"}},
)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Cap por usuario.
    count = await db.execute(
        select(func.count())
        .select_from(Workspace)
        .where(Workspace.user_id == current_user.id, Workspace.archived_at.is_(None))
    )
    n = count.scalar() or 0
    if n >= MAX_WORKSPACES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Máximo {MAX_WORKSPACES_PER_USER} proyectos activos por usuario. "
            "Archivá alguno para crear uno nuevo.",
        )

    ws = Workspace(
        user_id=current_user.id,
        name=body.name,
        color=body.color,
        description=body.description,
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return _ws_to_out(ws, conv_count=0)


@router.get(
    "",
    response_model=list[WorkspaceOut],
    summary="Listar workspaces del usuario",
)
async def list_workspaces(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Subquery: conteo de conversaciones por workspace.
    conv_count_sq = (
        select(
            Conversation.workspace_id,
            func.count(Conversation.id).label("n"),
        )
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.workspace_id)
        .subquery()
    )

    base_filter = Workspace.user_id == current_user.id
    if not include_archived:
        base_filter = base_filter & Workspace.archived_at.is_(None)

    q = (
        select(Workspace, conv_count_sq.c.n)
        .outerjoin(conv_count_sq, conv_count_sq.c.workspace_id == Workspace.id)
        .where(base_filter)
        .order_by(Workspace.created_at.desc())
    )
    rows = (await db.execute(q)).all()
    return [_ws_to_out(ws, conv_count=(n or 0)) for ws, n in rows]


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceOut,
    summary="Detalle de un workspace",
    responses={404: {"description": "Workspace no encontrado"}},
)
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await _get_owned_workspace(db, current_user.id, workspace_id)
    n = (
        await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.workspace_id == ws.id,
                Conversation.user_id == current_user.id,
            )
        )
    ).scalar() or 0
    return _ws_to_out(ws, conv_count=n)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceOut,
    summary="Editar workspace (nombre/color/desc/archivar)",
    responses={404: {"description": "Workspace no encontrado"}},
)
async def update_workspace(
    workspace_id: UUID,
    body: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await _get_owned_workspace(db, current_user.id, workspace_id)
    update_data = body.model_dump(exclude_unset=True)

    if "archived" in update_data:
        archived = update_data.pop("archived")
        ws.archived_at = datetime.now(UTC) if archived else None

    for field, value in update_data.items():
        setattr(ws, field, value)
    ws.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(ws)
    return _ws_to_out(ws)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar workspace (los chats asociados quedan sueltos)",
    responses={404: {"description": "Workspace no encontrado"}},
)
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await _get_owned_workspace(db, current_user.id, workspace_id)
    # La FK de conversations.workspace_id tiene ondelete=SET NULL: los chats
    # del workspace quedan "sueltos", no se borran. Memoria sí se borra (CASCADE).
    await db.delete(ws)
    await db.commit()


# ── Workspace memory ──

@router.get(
    "/{workspace_id}/memory",
    response_model=MemoryListOut,
    summary="Listar memoria del workspace",
)
async def list_memory(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workspace(db, current_user.id, workspace_id)
    result = await db.execute(
        select(WorkspaceMemory)
        .where(WorkspaceMemory.workspace_id == workspace_id)
        .order_by(WorkspaceMemory.created_at.asc())
    )
    items = list(result.scalars().all())
    return MemoryListOut(items=[_mem_to_out(i) for i in items])


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (name or "proyecto").strip().lower())
    return s.strip("-")[:40] or "proyecto"


@router.get(
    "/{workspace_id}/export",
    summary="Exportar la memoria del proyecto (PDF o CSV) para una reunión",
    responses={
        404: {"description": "Workspace no encontrado"},
        400: {"description": "Formato no soportado"},
    },
)
async def export_memory(
    workspace_id: UUID,
    format: str = Query("pdf", pattern="^(pdf|csv)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await _get_owned_workspace(db, current_user.id, workspace_id)
    result = await db.execute(
        select(WorkspaceMemory)
        .where(WorkspaceMemory.workspace_id == workspace_id)
        .order_by(WorkspaceMemory.created_at.asc())
    )
    items = [
        {
            "key": i.key,
            "value": i.value,
            "confidence": i.confidence,
            "source": i.source,
            "updated_at": i.updated_at,
        }
        for i in result.scalars().all()
    ]

    today = datetime.now().strftime("%Y-%m-%d")
    base = f"memoria-{_slugify(ws.name)}-{today}"
    if format == "pdf":
        blob = render_memory_pdf(ws.name, items)
        media = "application/pdf"
        filename = f"{base}.pdf"
    else:
        blob = render_memory_csv(ws.name, items)
        media = "text/csv; charset=utf-8"
        filename = f"{base}.csv"

    return StreamingResponse(
        io.BytesIO(blob),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/{workspace_id}/memory",
    response_model=MemoryItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear o actualizar item de memoria (upsert por key)",
    responses={409: {"description": "Límite de items alcanzado"}},
)
async def upsert_memory(
    workspace_id: UUID,
    body: MemoryItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workspace(db, current_user.id, workspace_id)

    # ¿Existe item con esa key? Upsert manual (la unique key (workspace_id, key)
    # lo protege a nivel BD, pero igual hacemos lookup para UX consistente).
    existing = await db.execute(
        select(WorkspaceMemory).where(
            WorkspaceMemory.workspace_id == workspace_id,
            WorkspaceMemory.key == body.key,
        )
    )
    item = existing.scalar_one_or_none()

    if item is None:
        # Cap por workspace.
        count = await db.execute(
            select(func.count())
            .select_from(WorkspaceMemory)
            .where(WorkspaceMemory.workspace_id == workspace_id)
        )
        n = count.scalar() or 0
        if n >= MAX_MEMORY_ITEMS_PER_WORKSPACE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Máximo {MAX_MEMORY_ITEMS_PER_WORKSPACE} items de memoria por proyecto.",
            )
        item = WorkspaceMemory(
            workspace_id=workspace_id,
            key=body.key,
            value=body.value,
            source=body.source,
            confidence=body.confidence,
            confirmed_at=datetime.now(UTC),
        )
        db.add(item)
    else:
        item.value = body.value
        item.confidence = body.confidence
        item.source = body.source
        item.confirmed_at = datetime.now(UTC)
        item.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(item)
    return _mem_to_out(item)


@router.patch(
    "/{workspace_id}/memory/{item_id}",
    response_model=MemoryItemOut,
    summary="Editar item de memoria",
    responses={404: {"description": "Item no encontrado"}},
)
async def update_memory(
    workspace_id: UUID,
    item_id: UUID,
    body: MemoryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workspace(db, current_user.id, workspace_id)
    item = await db.get(WorkspaceMemory, item_id)
    if item is None or item.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item de memoria no encontrado"
        )
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    item.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(item)
    return _mem_to_out(item)


@router.delete(
    "/{workspace_id}/memory/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar item de memoria",
    responses={404: {"description": "Item no encontrado"}},
)
async def delete_memory(
    workspace_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workspace(db, current_user.id, workspace_id)
    item = await db.get(WorkspaceMemory, item_id)
    if item is None or item.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item de memoria no encontrado"
        )
    await db.delete(item)
    await db.commit()
