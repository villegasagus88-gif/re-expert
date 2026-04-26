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
from models.project import Project
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


TITLE_MAX_LEN = 60


def _derive_title(message: str, max_len: int = TITLE_MAX_LEN) -> str:
    """
    Deriva un título corto a partir del primer mensaje del usuario.

    Colapsa whitespace, trunca a `max_len` chars (respetando palabras cuando
    se puede) y agrega "…" si quedó truncado. Si el mensaje queda vacío,
    usa el placeholder por defecto.
    """
    text = " ".join(message.split()).strip()
    if not text:
        return "Nueva conversación"
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rstrip()
    # Intentar cortar en el último espacio para no partir palabras
    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        truncated = truncated[:last_space].rstrip()
    return truncated + "…"


async def _get_or_create_conversation(
    db: AsyncSession,
    user_id: UUID,
    conversation_id: UUID | None,
    first_message: str | None = None,
) -> Conversation:
    """
    Load an existing conversation (verifying ownership) or create a new one.

    When creating, derive the title from `first_message` so the sidebar
    shows something meaningful instead of the "Nueva conversación" default.
    """
    if conversation_id is None:
        title = _derive_title(first_message or "")
        conv = Conversation(user_id=user_id, title=title)
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


async def _build_sol_project_context(db: AsyncSession, user_id: UUID) -> str:
    """Return a short markdown summary of the user's project for SOL's system prompt."""
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    proj = result.scalar_one_or_none()
    if not proj:
        return ""
    lines = [
        f"- Nombre: {proj.nombre}",
        f"- Estado: {proj.estado} — {proj.estado_texto}",
        f"- Presupuesto base: ${float(proj.presupuesto_base):,.0f}",
        f"- Costo real: ${float(proj.costo_real):,.0f}",
        f"- Avance real: {proj.avance_real_pct:.1f}% (planeado: {proj.avance_plan_pct:.1f}%)",
        f"- Plazo: {proj.meses_transcurridos}/{proj.meses_total} meses",
    ]
    if proj.fecha_inicio:
        lines.append(f"- Inicio: {proj.fecha_inicio.isoformat()}")
    if proj.fecha_entrega_programada:
        lines.append(f"- Entrega programada: {proj.fecha_entrega_programada.isoformat()}")
    if proj.fecha_entrega_estimada:
        lines.append(f"- Entrega estimada: {proj.fecha_entrega_estimada.isoformat()}")
    if proj.notas:
        lines.append(f"- Notas: {proj.notas}")
    return "\n".join(lines)


@router.post(
    "",
    summary="Enviar mensaje al chat (streaming SSE)",
    responses={
        401: {"description": "Token inválido o ausente"},
        403: {"description": "Feature requiere plan Pro"},
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
    # Gate: SOL context requires Pro plan
    if body.context_type == "sol" and current_user.plan != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "El Asistente SOL requiere el plan Pro.",
                "plan_required": "pro",
                "upgrade_url": "/pricing.html",
            },
        )

    # 1. Per-user rate limit check (raises 429 with Retry-After if exceeded).
    #    Must run BEFORE persisting the user message so the current request
    #    isn't double-counted.
    rate_limit_headers = await check_user_rate_limit(db, current_user)

    # 2. Get or create conversation (verifies ownership).
    #    If creating new, derive title from the first user message.
    conv = await _get_or_create_conversation(
        db, current_user.id, body.conversation_id, first_message=body.message
    )

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

    # 6. Build system prompt. For SOL, inject the user's real project data so
    #    the assistant knows current budget, progress, and dates.
    project_context = ""
    if body.context_type == "sol":
        project_context = await _build_sol_project_context(db, current_user.id)
    system_prompt = await build_system_prompt(body.context_type, project_context)

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
