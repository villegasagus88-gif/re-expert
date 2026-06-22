"""
Análisis de planos (multimodal): POST /api/planos/analyze.

Recibe archivos (imágenes/PDF) vía multipart/form-data, los manda a Claude con
visión y streamea el análisis de materiales por SSE (mismo formato de eventos
que /api/chat: start / delta / done / error).

A diferencia de /api/chat, el body NO pasa por el límite global de 1 MB (ver
_BodySizeLimitMiddleware en main.py, que exime el prefijo /api/planos/): los
planos son grandes. El handler valida tamaño por archivo y total igualmente.
"""
# Nota: NO usar `from __future__ import annotations` acá (rompe el parseo de
# los form params de FastAPI), igual que en agent.py.
import asyncio
import base64
import json
import logging
from uuid import UUID

from config.settings import settings
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
from services.anthropic_service import build_system_prompt, stream_chat
from services.rate_limit_service import check_user_rate_limit
from services.token_usage_service import log_token_usage
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/planos", tags=["planos"])

STREAM_TIMEOUT_SECONDS = 120  # la visión sobre varios archivos puede tardar
MAX_FILES = 8
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB por archivo (límite de la API de visión)
MAX_TOTAL_BYTES = 12 * 1024 * 1024  # 12 MB en total (queda bajo el cap de 16 MB)
MAX_TOKENS = 4096

_PDF_TYPE = "application/pdf"
_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_ALLOWED = _IMAGE_TYPES | {_PDF_TYPE}
_EXT_TO_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": _PDF_TYPE,
}

DEFAULT_PROMPT = (
    "Analizá estos planos de obra y estimá los materiales necesarios. "
    "Devolvé un desglose por rubro con cantidades estimadas (m², m³, kg, "
    "unidades) y, cuando puedas, un rango de costo aproximado en pesos. "
    "Aclará los supuestos que tomaste. Si algo no se ve con claridad en el "
    "plano, indicalo en vez de inventar."
)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _media_type_for(f: UploadFile) -> str | None:
    """Resuelve el media type por content-type y, si no, por extensión."""
    ct = (f.content_type or "").split(";")[0].strip().lower()
    if ct in _ALLOWED:
        return ct
    name = (f.filename or "").lower()
    for ext, mt in _EXT_TO_TYPE.items():
        if name.endswith(ext):
            return mt
    return None


async def _get_or_create_conv(
    db: AsyncSession, user_id: UUID, conversation_id: str | None, names: list[str]
) -> Conversation:
    if conversation_id:
        try:
            cid = UUID(conversation_id)
        except (ValueError, TypeError):
            raise HTTPException(404, "Conversación no encontrada")
        conv = await db.get(Conversation, cid)
        if conv is None or conv.user_id != user_id:
            raise HTTPException(404, "Conversación no encontrada")
        return conv
    title = ("Análisis de planos: " + ", ".join(names))[:60] or "Análisis de planos"
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    await db.flush()
    return conv


@router.post(
    "/analyze",
    summary="Analizar planos con IA (multimodal, streaming SSE)",
    responses={
        400: {"description": "Archivos inválidos o faltantes"},
        401: {"description": "Token inválido o ausente"},
        413: {"description": "Archivos demasiado grandes"},
        429: {"description": "Demasiados análisis, esperá un rato"},
    },
)
@limiter.limit("6/minute")
async def analyze_planos(
    request: Request,
    files: list[UploadFile] = File(...),
    prompt: str | None = Form(None),
    conversation_id: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not files:
        raise HTTPException(400, "No se subió ningún archivo")
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Máximo {MAX_FILES} archivos por análisis")

    content_blocks: list[dict] = []
    names: list[str] = []
    total = 0
    for f in files:
        media_type = _media_type_for(f)
        if media_type is None:
            raise HTTPException(
                400,
                f"Tipo de archivo no soportado: {f.filename!r}. "
                "Usá JPG, PNG, WEBP, GIF o PDF.",
            )
        raw = await f.read()
        size = len(raw)
        if size == 0:
            raise HTTPException(400, f"Archivo vacío: {f.filename!r}")
        if size > MAX_FILE_BYTES:
            raise HTTPException(413, f"{f.filename!r} supera el máximo de 5 MB")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise HTTPException(413, "El total de archivos supera el máximo de 12 MB")

        b64 = base64.b64encode(raw).decode("ascii")
        block_type = "document" if media_type == _PDF_TYPE else "image"
        content_blocks.append(
            {
                "type": block_type,
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64,
                },
            }
        )
        names.append(f.filename or "archivo")

    user_text = (prompt or "").strip() or DEFAULT_PROMPT
    # El texto va primero para anclar la instrucción antes de las imágenes.
    message_content = [{"type": "text", "text": user_text}] + content_blocks

    # Rate-limit por usuario (mismo mecanismo que /api/chat).
    rate_limit_headers = await check_user_rate_limit(db, current_user)

    conv = await _get_or_create_conv(db, current_user.id, conversation_id, names)
    # Persistimos el pedido como texto (no guardamos los bytes de los planos).
    persisted_user = f"{user_text}\n\n📎 Planos adjuntos: {', '.join(names)}"
    db.add(Message(conversation_id=conv.id, role="user", content=persisted_user))
    await db.commit()

    conv_id_str = str(conv.id)
    system_prompt = await build_system_prompt("chat")
    messages = [{"role": "user", "content": message_content}]

    async def stream():
        yield _sse({"type": "start", "conversation_id": conv_id_str})
        full = ""
        in_tok = 0
        out_tok = 0
        try:
            async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
                async for ev in stream_chat(messages, system_prompt, max_tokens=MAX_TOKENS):
                    if ev["type"] == "delta":
                        full += ev["text"]
                        yield _sse({"type": "delta", "text": ev["text"]})
                    elif ev["type"] == "end":
                        in_tok = ev["input_tokens"]
                        out_tok = ev["output_tokens"]
        except TimeoutError:
            yield _sse(
                {
                    "type": "error",
                    "message": f"Timeout: el análisis tardó más de {STREAM_TIMEOUT_SECONDS}s",
                }
            )
            return
        except Exception:
            logger.exception("Error analizando planos")
            yield _sse(
                {
                    "type": "error",
                    "message": "Error analizando los planos. Probá de nuevo en unos segundos.",
                }
            )
            return

        assistant_id = None
        try:
            assistant = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full,
                tokens_used=(in_tok + out_tok) or None,
            )
            db.add(assistant)
            await db.commit()
            assistant_id = assistant.id
        except Exception:
            logger.exception("guardar análisis de planos falló")

        if in_tok and out_tok:
            await log_token_usage(
                db,
                user_id=current_user.id,
                conversation_id=conv.id,
                message_id=assistant_id,
                model=settings.ANTHROPIC_MODEL,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )

        yield _sse({"type": "done", "tokens_used": (in_tok + out_tok) or None})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            **rate_limit_headers,
        },
    )
