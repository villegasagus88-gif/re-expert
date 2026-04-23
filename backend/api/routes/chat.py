"""
Chat endpoint: POST /api/chat.

Receives a user message and (optional) conversation_id, loads history,
builds system prompt + knowledge context, streams Claude's response
as Server-Sent Events (SSE), and persists both user and assistant
messages in the database.

SSE event spec:
  - start: {"type": "start", "conversation_id": "<uuid>"}
  - delta: {"type": "delta", "text": "<chunk>"}
  - done:  {"type": "done",  "tokens_used": <int|null>}
  - error: {"type": "error", "message": "<human message>"}

Stream hard-caps at 60s; if exceeded an error event is emitted.

Smoke test with curl (replace <JWT>):

    curl -N -X POST https://<host>/api/chat \\
        -H "Authorization: Bearer <JWT>" \\
        -H "Content-Type: application/json" \\
        -d '{"message": "Hola, ¿qué sabés de costos de obra en CABA?"}'

The -N flag disables output buffering so you see tokens in real time.
"""
import asyncio
import json
import logging
from uuid import UUID

from api.schemas.chat import ChatRequest
from config.settings import settings
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
from services.anthropic_service import build_system_prompt, stream_chat
from services.rate_limit_service import check_user_rate_limit
from services.token_usage_service import log_token_usage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_HISTORY_MESSAGES = 20
STREAM_TIMEOUT_SECONDS = 60


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
    # 1. Per-user rate limit check (raises 429 with Retry-After if exceeded).
    #    Must run BEFORE persisting the user message so the current request
    #    isn't double-counted.
    rate_limit_headers = await check_user_rate_limit(db, current_user)

    # 2. Get or create conversation (verifies ownership)
    conv = await _get_or_create_conversation(db, current_user.id, body.conversation_id)

    # 3. Load prior history
    history = await _load_history(db, conv.id)

    # 4. Persist the user message up-front (so it survives stream errors)
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.commit()

    # 5. Build messages payload for the Anthropic API
    api_messages: list[dict] = [
        {"role": m.role, "content": m.content} for m in history
    ]
    api_messages.append({"role": "user", "content": body.message})

    # 6. Build system prompt (includes knowledge context if available)
    system_prompt = await build_system_prompt()

    conv_id_str = str(conv.id)

    async def event_stream():
        """
        Yield SSE events per the streaming spec and persist the assistant
        message when the stream completes successfully.

        Events:
          - start: { type, conversation_id }
          - delta: { type, text }
          - done:  { type, tokens_used }
          - error: { type, message }
        """
        # start
        yield _sse({"type": "start", "conversation_id": conv_id_str})

        full_response = ""
        tokens_used: int | None = None
        input_tokens: int | None = None
        output_tokens: int | None = None

        try:
            async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
                async for event in stream_chat(api_messages, system_prompt):
                    if event["type"] == "delta":
                        full_response += event["text"]
                        yield _sse({"type": "delta", "text": event["text"]})
                    elif event["type"] == "end":
                        input_tokens = event["input_tokens"]
                        output_tokens = event["output_tokens"]
                        tokens_used = input_tokens + output_tokens
        except TimeoutError:
            logger.warning("Stream timeout after %ss", STREAM_TIMEOUT_SECONDS)
            yield _sse(
                {
                    "type": "error",
                    "message": f"Timeout: la respuesta tardó más de {STREAM_TIMEOUT_SECONDS}s",
                }
            )
            return
        except Exception as e:
            logger.exception("Error en stream_chat: %s", e)
            yield _sse({"type": "error", "message": "Error generando respuesta"})
            return

        # Persist assistant message (with token count if available)
        assistant_msg_id = None
        try:
            assistant_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_response,
                tokens_used=tokens_used,
            )
            db.add(assistant_msg)
            await db.commit()
            assistant_msg_id = assistant_msg.id
        except Exception as e:
            logger.exception("Error guardando assistant message: %s", e)

        # Log token usage for billing/analytics (best-effort; never blocks reply).
        if input_tokens is not None and output_tokens is not None:
            await log_token_usage(
                db,
                user_id=current_user.id,
                conversation_id=conv.id,
                message_id=assistant_msg_id,
                model=settings.ANTHROPIC_MODEL,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        yield _sse({"type": "done", "tokens_used": tokens_used})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering if fronted
            **rate_limit_headers,
        },
    )
