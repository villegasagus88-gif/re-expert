"""
Conversation CRUD endpoints.

All endpoints are protected and scoped to the authenticated user's
conversations only. No user can access another user's data.
"""
import math

from api.schemas.conversation import (
    ConversationDetailOut,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
    PaginatedConversations,
)
from core.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
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
    conv = Conversation(
        user_id=current_user.id,
        title=body.title,
        section=body.section,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return ConversationOut(
        id=str(conv.id),
        title=conv.title,
        section=conv.section,
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
):
    # Base filter: only this user's conversations
    base_filter = Conversation.user_id == current_user.id
    if section:
        base_filter = base_filter & (Conversation.section == section)

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

    # For each conversation, get the last message preview
    items = []
    for conv, msg_count, _last_at in rows:
        # Get last message preview (single query per conversation)
        last_msg_query = (
            select(Message.content)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg_result = await db.execute(last_msg_query)
        last_msg_content = last_msg_result.scalar_one_or_none()

        preview = None
        if last_msg_content:
            preview = last_msg_content[:100] + ("..." if len(last_msg_content) > 100 else "")

        items.append(
            ConversationOut(
                id=str(conv.id),
                title=conv.title,
                section=conv.section,
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
