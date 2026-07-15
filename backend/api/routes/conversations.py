"""
Conversation CRUD endpoints.

All endpoints are protected and scoped to the authenticated user's
conversations only. No user can access another user's data.
"""
import math
from uuid import UUID

from api.schemas.conversation import (
    ConversationDetailOut,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
    PaginatedConversations,
    UpdateConversationRequest,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
from models.workspace import Workspace
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=ConversationOut,
    status_code=201,
    summary="Crear nueva conversacion",
)
async def create_conversation(
    body: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace_uuid: UUID | None = None
    if body.workspace_id:
        try:
            workspace_uuid = UUID(body.workspace_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workspace_id inválido",
            )
        # Ownership check.
        ws = await db.get(Workspace, workspace_uuid)
        if ws is None or ws.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace no encontrado",
            )

    conv = Conversation(
        user_id=current_user.id,
        title=body.title,
        section=body.section,
        workspace_id=workspace_uuid,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return ConversationOut(
        id=str(conv.id),
        title=conv.title,
        section=conv.section,
        workspace_id=str(conv.workspace_id) if conv.workspace_id else None,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
        last_message_preview=None,
    )


@router.get(
    "",
    response_model=PaginatedConversations,
    summary="Listar conversaciones del usuario (paginado, orden por actividad)",
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Pagina (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items por pagina"),
    section: str | None = Query(None, description="Filtrar por seccion"),
    exclude_sol: bool = Query(
        False, description="Excluir conversaciones del agente SOL (sol / sol_telegram)"
    ),
    workspace_id: str | None = Query(
        None,
        description=(
            "Filtrar por workspace: UUID = solo chats de ese workspace; "
            "'none' = solo chats sueltos (sin workspace); omitido = todos"
        ),
    ),
):
    # Base filter: only this user's conversations
    base_filter = Conversation.user_id == current_user.id
    if section:
        base_filter = base_filter & (Conversation.section == section)
    if exclude_sol:
        base_filter = base_filter & Conversation.section.notin_(["sol", "sol_telegram"])
    if workspace_id is not None:
        if workspace_id == "none":
            base_filter = base_filter & Conversation.workspace_id.is_(None)
        else:
            try:
                ws_uuid = UUID(workspace_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="workspace_id inválido",
                )
            base_filter = base_filter & (Conversation.workspace_id == ws_uuid)

    # Count total
    count_query = select(func.count()).select_from(Conversation).where(base_filter)
    total = (await db.execute(count_query)).scalar() or 0

    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    # Subquery: last message created_at per conversation (for ordering)
    last_msg_sq = (
        select(
            Message.conversation_id,
            func.max(Message.created_at).label("last_message_at"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    # Main query with join
    query = (
        select(
            Conversation,
            func.count(Message.id).label("msg_count"),
            last_msg_sq.c.last_message_at,
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .outerjoin(last_msg_sq, last_msg_sq.c.conversation_id == Conversation.id)
        .where(base_filter)
        .group_by(Conversation.id, last_msg_sq.c.last_message_at)
        .order_by(
            func.coalesce(last_msg_sq.c.last_message_at, Conversation.created_at).desc()
        )
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    # Preview del último mensaje de TODAS las conversaciones de la página en UNA
    # sola query (antes: N+1 — una query por conversación, hasta 100 por request).
    # DISTINCT ON toma la fila más reciente por conversation_id (Postgres).
    conv_ids = [conv.id for conv, _mc, _la in rows]
    previews: dict = {}
    if conv_ids:
        last_msgs = (
            select(Message.conversation_id, Message.content)
            .where(Message.conversation_id.in_(conv_ids))
            .order_by(Message.conversation_id, Message.created_at.desc())
            .distinct(Message.conversation_id)
        )
        for cid, content in (await db.execute(last_msgs)).all():
            previews[cid] = content

    items = []
    for conv, msg_count, _last_at in rows:
        last_msg_content = previews.get(conv.id)
        preview = None
        if last_msg_content:
            preview = last_msg_content[:100] + ("..." if len(last_msg_content) > 100 else "")

        items.append(
            ConversationOut(
                id=str(conv.id),
                title=conv.title,
                section=conv.section,
                workspace_id=str(conv.workspace_id) if conv.workspace_id else None,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
                last_message_preview=preview,
            )
        )

    return PaginatedConversations(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailOut,
    summary="Ver detalle de conversacion con mensajes",
    responses={
        404: {"description": "Conversacion no encontrada o no pertenece al usuario"},
    },
)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID

    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    # Load conversation with messages eagerly
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conv_uuid,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    return ConversationDetailOut(
        id=str(conv.id),
        title=conv.title,
        section=conv.section,
        workspace_id=str(conv.workspace_id) if conv.workspace_id else None,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            MessageOut(
                id=str(m.id),
                role=m.role,
                content=m.content,
                tokens_used=m.tokens_used,
                created_at=m.created_at,
            )
            for m in sorted(conv.messages, key=lambda m: m.created_at)
        ],
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationOut,
    summary="Renombrar conversación o moverla entre workspaces",
    responses={
        404: {"description": "Conversacion no encontrada o no pertenece al usuario"},
    },
)
async def update_conversation(
    conversation_id: str,
    body: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_uuid,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    data = body.model_dump(exclude_unset=True)

    if "title" in data and data["title"]:
        conv.title = data["title"]

    if "workspace_id" in data:
        new_ws_id = data["workspace_id"]
        if new_ws_id is None or new_ws_id == "":
            conv.workspace_id = None
        else:
            try:
                new_ws_uuid = UUID(new_ws_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="workspace_id inválido",
                )
            ws = await db.get(Workspace, new_ws_uuid)
            if ws is None or ws.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace no encontrado",
                )
            conv.workspace_id = new_ws_uuid

    await db.commit()
    await db.refresh(conv)

    return ConversationOut(
        id=str(conv.id),
        title=conv.title,
        section=conv.section,
        workspace_id=str(conv.workspace_id) if conv.workspace_id else None,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.delete(
    "/{conversation_id}",
    status_code=204,
    summary="Eliminar conversacion y todos sus mensajes",
    responses={
        404: {"description": "Conversacion no encontrada o no pertenece al usuario"},
    },
)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID

    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_uuid,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    await db.delete(conv)  # cascade deletes messages
    await db.commit()
