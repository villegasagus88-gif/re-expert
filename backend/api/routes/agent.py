"""
SOL agent endpoint: POST /api/sol/agent.

Entrada (JSON):
    { "message": "...", "conversation_id": "uuid|null" }

Salida: stream SSE con eventos definidos en services.agent_service.run_agent.

Difiere de /api/chat:
  - Habilita tool-use (Claude puede llamar tools del sistema).
  - System prompt orientado a acción.
  - Persiste user/assistant messages igual que /api/chat.
"""
# Nota: NO usar `from __future__ import annotations` acá. FastAPI rompe el OpenAPI
# si los body params quedan como ForwardRef (intenta tratarlos como Query).
import asyncio
import json
import logging

from api.schemas.chat import ChatRequest
from config.settings import settings
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
from services import agent_service
from services.agent_service import run_agent
from services.rate_limit_service import check_user_rate_limit
from services.token_usage_service import log_token_usage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sol", tags=["sol-agent"])

MAX_HISTORY_MESSAGES = 14
STREAM_TIMEOUT_SECONDS = 120  # los loops tool-use pueden tardar más


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


async def _get_or_create_conv(
    db: AsyncSession, user_id, conversation_id, first_message: str
) -> Conversation:
    if conversation_id is None:
        title = " ".join(first_message.split())[:60] or "SOL"
        conv = Conversation(user_id=user_id, title=title, section="sol")
        db.add(conv)
        await db.flush()
        return conv
    conv = await db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user_id:
        raise HTTPException(404, "Conversación no encontrada")
    # SOL no debe escribir en conversaciones del Chat Experto (otra sección):
    # mezclaría hilos y contaminaría el dominio del chat.
    if conv.section != "sol":
        raise HTTPException(404, "Conversación no encontrada")
    return conv


async def _load_history(db: AsyncSession, conv_id, limit: int = MAX_HISTORY_MESSAGES):
    rows = list(
        (
            await db.execute(
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    rows.reverse()
    # Convertir a formato Anthropic. Filtramos contenidos vacíos por las dudas.
    msgs = [
        {"role": m.role, "content": m.content}
        for m in rows
        if m.content
    ]
    # El historial DEBE arrancar con rol "user" (Anthropic rechaza si empieza
    # con assistant). Al truncar a N puede quedar un assistant colgado adelante.
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    return msgs


@router.post(
    "/agent",
    summary="Stream SOL agent response (tool-use SSE)",
    responses={
        401: {"description": "Token inválido o ausente"},
        403: {"description": "SOL requiere plan Pro"},
        429: {"description": "Demasiados mensajes"},
    },
)
@limiter.limit("10/minute")
async def sol_agent(
    request: Request,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # SOL no tiene gate propio: el router exige `require_access` (modelo
    # pago-only) y el trial habilita SOL igual que pro.
    rate_limit_headers = await check_user_rate_limit(db, current_user)
    conv = await _get_or_create_conv(
        db, current_user.id, body.conversation_id, body.message
    )
    history = await _load_history(db, conv.id)
    user_msg = Message(conversation_id=conv.id, role="user", content=body.message)
    db.add(user_msg)
    await db.commit()

    conv_id_str = str(conv.id)

    async def stream():
        yield _sse({"type": "start", "conversation_id": conv_id_str})
        full_text = ""
        in_tok = 0
        out_tok = 0
        pending_confirms: list = []
        used_model = settings.ANTHROPIC_MODEL
        try:
            async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
                async for ev in run_agent(db, current_user, history, body.message):
                    if ev["type"] == "delta":
                        full_text += ev["text"]
                    if ev["type"] == "done":
                        in_tok = ev.get("input_tokens", 0)
                        out_tok = ev.get("output_tokens", 0)
                        pending_confirms = ev.get("pending_confirmations") or []
                        used_model = ev.get("model") or used_model
                    yield _sse(ev)
        except TimeoutError:
            yield _sse({"type": "error", "message": "Timeout SOL agent"})
            return
        except Exception as e:
            logger.exception("agent error")
            yield _sse({"type": "error", "message": str(e)})
            return

        # Persistir respuesta del agente. Al content persistido le anexamos, si
        # hay, el marcador oculto con los tokens de confirmación pendientes: el
        # usuario ya vio el texto limpio por el stream; el marcador solo lo lee
        # el modelo en el próximo turno para poder confirmar.
        persisted = agent_service.append_confirm_marker(full_text, pending_confirms)
        try:
            assistant = Message(
                conversation_id=conv.id,
                role="assistant",
                content=persisted,
                tokens_used=(in_tok + out_tok) or None,
            )
            db.add(assistant)
            await db.commit()
            assistant_id = assistant.id
        except Exception:
            logger.exception("save agent reply failed")
            assistant_id = None

        if in_tok and out_tok:
            await log_token_usage(
                db,
                user_id=current_user.id,
                conversation_id=conv.id,
                message_id=assistant_id,
                model=used_model,  # el modelo REAL que respondió (Anthropic o Gemini)
                input_tokens=in_tok,
                output_tokens=out_tok,
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            **rate_limit_headers,
        },
    )
