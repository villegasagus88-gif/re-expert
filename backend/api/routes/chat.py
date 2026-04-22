"""
Chat endpoint: POST /api/chat.

Receives a user message and (optional) conversation_id, loads history,
builds system prompt + knowledge context, streams Claude's response
as Server-Sent Events (SSE), and persists both user and assistant
messages in the database.
"""
import json
import logging
from uuid import UUID

from api.schemas.chat import ChatRequest
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
from services.anthropic_service import build_system_prompt, stream_chat
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_HISTORY_MESSAGES = 20


async def _get_or_create_conversation(
    db: AsyncSession,
    user_id: UUID,
    conversation_id: UUID | None,
) -> Conversation:
    """Load an existing conversation (verifying ownership) or create a new one."""
    if conversation_id is None:
        conv = Conversation(user_id=user_id)
        db.add(conv)
        await db.flush()
        return conv

    conv = await db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada",
        )
    return conv


async def _load_history(
    db: AsyncSession,
    conversation_id: UUID,
    limit: int = MAX_HISTORY_MESSAGES,
) -> list[Message]:
    """Fetch the most recent N messages, returned in chronological order."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()  # chronological
    return rows


def _sse(data: dict) -> str:
    """Format a dict as a Server-Sent Event line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "",
    summary="Enviar mensaje al chat (streaming SSE)",
    responses={
        401: {"description": "Token inválido o ausente"},
        404: {"description": "Conversación no encontrada"},
        429: {"description": "Demasiados mensajes, esperá un rato"},
    },
)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Get or create conversation (verifies ownership)
    conv = await _get_or_create_conversation(db, current_user.id, body.conversation_id)

    # 2. Load prior history
    history = await _load_history(db, conv.id)

    # 3. Persist the user message up-front (so it survives stream errors)
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.commit()

    # 4. Build messages payload for the Anthropic API
    api_messages: list[dict] = [
        {"role": m.role, "content": m.content} for m in history
    ]
    api_messages.append({"role": "user", "content": body.message})

    # 5. Build system prompt (includes knowledge context if available)
    system_prompt = await build_system_prompt()

    conv_id_str = str(conv.id)

    async def event_stream():
        """Yield SSE events and persist the final assistant message."""
        # First event: echo the conversation id so the client can store it
        yield _sse({"type": "meta", "conversation_id": conv_id_str})

        full_response = ""
        try:
            async for token in stream_chat(api_messages, system_prompt):
                full_response += token
                yield _sse({"type": "token", "text": token})
        except Exception as e:
            logger.exception("Error en stream_chat: %s", e)
            yield _sse({"type": "error", "message": "Error generando respuesta"})
            return

        # Persist the assistant response once streaming completes successfully
        try:
            assistant_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_msg)
            await db.commit()
        except Exception as e:
            logger.exception("Error guardando assistant message: %s", e)

        yield _sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if fronted
        },
    )
