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

Stream hard-caps at 180s; if exceeded an error event is emitted.

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
import re
from datetime import UTC, datetime
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
from models.workspace import UserProfileGlobal, Workspace, WorkspaceMemory
from services.anthropic_service import build_system_prompt, stream_chat
from services.model_selector import pick_model
from services.rate_limit_service import check_user_rate_limit
from services.retrieval_tools import RETRIEVAL_TOOL_SCHEMAS, run_retrieval_tool
from services.token_usage_service import log_token_usage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_HISTORY_MESSAGES = 20
STREAM_TIMEOUT_SECONDS = 180


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
    workspace_id: UUID | None = None,
) -> Conversation:
    """
    Load an existing conversation (verifying ownership) or create a new one.

    When creating, derive the title from `first_message` so the sidebar
    shows something meaningful instead of the "Nueva conversación" default.

    `workspace_id` solo aplica al crear (capa 1B). Si viene, verifica que
    el workspace pertenezca al usuario antes de asociarlo.
    """
    if conversation_id is None:
        title = _derive_title(first_message or "")
        # Validar ownership del workspace si fue provisto.
        if workspace_id is not None:
            ws = await db.get(Workspace, workspace_id)
            if ws is None or ws.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace no encontrado",
                )
        conv = Conversation(
            user_id=user_id, title=title, workspace_id=workspace_id
        )
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


async def _load_profile_items(
    db: AsyncSession, user_id: UUID
) -> list[tuple[str, str]]:
    """Carga items de perfil global del usuario, ordenados por sort_order."""
    result = await db.execute(
        select(UserProfileGlobal)
        .where(UserProfileGlobal.user_id == user_id)
        .order_by(
            UserProfileGlobal.sort_order.asc(),
            UserProfileGlobal.created_at.asc(),
        )
    )
    return [(i.key, i.value) for i in result.scalars().all()]


async def _load_workspace_memory(
    db: AsyncSession, workspace_id: UUID
) -> list[tuple[str, str]]:
    """Carga items de memoria del workspace, ordenados por uso reciente primero."""
    result = await db.execute(
        select(WorkspaceMemory)
        .where(WorkspaceMemory.workspace_id == workspace_id)
        .order_by(
            # Items confirmados recientes primero; los viejos al final.
            WorkspaceMemory.last_used_at.desc().nullslast(),
            WorkspaceMemory.created_at.asc(),
        )
    )
    return [(i.key, i.value) for i in result.scalars().all()]


# ════════════════════════════════════════════════════════════════════
# Capa 1B — tool `remember`: captura híbrida de memoria desde el chat.
# El modelo decide CUÁNDO llamarla (reglas en el system prompt). Acá solo
# persistimos. Best-effort: si algo falla, devolvemos error legible y el
# chat sigue.
# ════════════════════════════════════════════════════════════════════
# Caps (espejo de los de routes/workspaces.py y routes/profile.py).
_MAX_WORKSPACE_MEM = 200
_MAX_PROFILE_MEM = 100

REMEMBER_TOOL_SCHEMA: dict = {
    "name": "remember",
    "description": (
        "Guarda un dato DURADERO en la memoria para recordarlo en futuros chats. "
        "Llamala cuando el usuario comparte información estable y útil a futuro.\n\n"
        "scope='workspace' → dato del proyecto activo (cliente, monto en "
        "negociación, dirección/lote, FOT, decisión tomada, dato de una escritura "
        "analizada). Solo si hay un proyecto activo.\n"
        "scope='profile' → dato personal del usuario que aplica a TODOS los chats "
        "(rol, zonas de trabajo, tipología habitual, estructura jurídica preferida).\n\n"
        "key: identificador corto en snake_case (ej: 'cliente_principal', "
        "'precio_m2_objetivo', 'rol'). value: el dato concreto y conciso.\n\n"
        "NO guardes: preguntas, cálculos efímeros, charla trivial, ni datos de pago "
        "sensibles (CBU, número de tarjeta, contraseñas). Si dudás si el usuario "
        "quiere recordarlo, preguntale ANTES en vez de llamar esta tool."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["workspace", "profile"]},
            "key": {"type": "string", "description": "snake_case corto, máx 80 chars"},
            "value": {"type": "string", "description": "el dato, máx 1000 chars"},
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "qué tan seguro estás del dato",
            },
        },
        "required": ["scope", "key", "value"],
    },
}


def _norm_mem_key(raw: str) -> str:
    """Normaliza la key a snake_case seguro (máx 80)."""
    k = (raw or "").strip().lower()
    k = re.sub(r"\s+", "_", k)
    k = re.sub(r"[^a-z0-9_\-\.]", "", k)
    return k[:80]


async def _persist_memory_item(
    db: AsyncSession,
    user_id: UUID,
    workspace_id: UUID | None,
    inputs: dict,
) -> dict:
    """Handler del tool `remember`. Upsert por (scope, key)."""
    scope = (inputs.get("scope") or "").strip()
    key = _norm_mem_key(inputs.get("key") or "")
    value = (inputs.get("value") or "").strip()[:1000]
    confidence = inputs.get("confidence") or "high"
    if confidence not in ("high", "medium", "low"):
        confidence = "high"
    if not key or not value:
        return {"error": "key y value son obligatorios", "saved": False}

    now = datetime.now(UTC)

    if scope == "workspace":
        if workspace_id is None:
            return {
                "error": "No hay proyecto activo en este chat; usá scope='profile' "
                "o pedile al usuario que abra un proyecto.",
                "saved": False,
            }
        existing = await db.execute(
            select(WorkspaceMemory).where(
                WorkspaceMemory.workspace_id == workspace_id,
                WorkspaceMemory.key == key,
            )
        )
        item = existing.scalar_one_or_none()
        if item is None:
            n = (
                await db.execute(
                    select(func.count())
                    .select_from(WorkspaceMemory)
                    .where(WorkspaceMemory.workspace_id == workspace_id)
                )
            ).scalar() or 0
            if n >= _MAX_WORKSPACE_MEM:
                return {"error": "Memoria del proyecto llena", "saved": False}
            item = WorkspaceMemory(
                workspace_id=workspace_id,
                key=key,
                value=value,
                source="auto-silent",
                confidence=confidence,
                confirmed_at=now,
                last_used_at=now,
            )
            db.add(item)
        else:
            item.value = value
            item.confidence = confidence
            item.source = "auto-silent"
            item.confirmed_at = now
            item.last_used_at = now
            item.updated_at = now
        await db.commit()
        return {"saved": True, "scope": "workspace", "key": key}

    # scope == profile (default seguro para cualquier otro valor)
    existing = await db.execute(
        select(UserProfileGlobal).where(
            UserProfileGlobal.user_id == user_id,
            UserProfileGlobal.key == key,
        )
    )
    item = existing.scalar_one_or_none()
    if item is None:
        n = (
            await db.execute(
                select(func.count())
                .select_from(UserProfileGlobal)
                .where(UserProfileGlobal.user_id == user_id)
            )
        ).scalar() or 0
        if n >= _MAX_PROFILE_MEM:
            return {"error": "Perfil lleno", "saved": False}
        item = UserProfileGlobal(
            user_id=user_id,
            key=key,
            value=value,
            source="auto-silent",
            confidence=confidence,
            confirmed_at=now,
            last_used_at=now,
        )
        db.add(item)
    else:
        item.value = value
        item.confidence = confidence
        item.source = "auto-silent"
        item.confirmed_at = now
        item.last_used_at = now
        item.updated_at = now
    await db.commit()
    return {"saved": True, "scope": "profile", "key": key}


def _make_chat_tool_runner(
    db: AsyncSession, user_id: UUID, workspace_id: UUID | None
):
    """Dispatcher de tools del chat: retrieval (puras) + remember (con contexto)."""

    async def _runner(name: str, inputs: dict) -> dict:
        if name == "remember":
            try:
                return await _persist_memory_item(db, user_id, workspace_id, inputs or {})
            except Exception as e:  # noqa: BLE001
                logger.exception("remember tool falló")
                return {"error": f"No se pudo guardar: {e}", "saved": False}
        return await run_retrieval_tool(name, inputs)

    return _runner


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
    #    If creating new, derive title from the first user message and
    #    optionally assign workspace.
    conv = await _get_or_create_conversation(
        db,
        current_user.id,
        body.conversation_id,
        first_message=body.message,
        workspace_id=body.workspace_id,
    )

    # 3. Load prior history
    history = await _load_history(db, conv.id)

    # 4. Persist the user message up-front (so it survives stream errors).
    #    Para el log/historial guardamos solo el texto. Las imágenes
    #    multimodales son one-shot: se mandan a Anthropic en este turno
    #    pero NO quedan en la conversación persistida (los archivos viven
    #    en la sesión del browser).
    content_for_log = body.message
    if body.attachments:
        content_for_log = (
            f"{body.message}\n\n"
            f"[Adjuntó {len(body.attachments)} "
            f"{'plano' if len(body.attachments) == 1 else 'planos'} para análisis]"
        )
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=content_for_log,
    )
    db.add(user_msg)
    await db.commit()

    # 5. Build messages payload for the Anthropic API.
    #    El history se manda como texto (los attachments no se persisten).
    #    El mensaje actual lleva content blocks (image + text) si hay
    #    attachments, o solo string si no hay.
    api_messages: list[dict] = [
        {"role": m.role, "content": m.content} for m in history
    ]
    if body.attachments:
        content_blocks: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": att.media_type,
                    "data": att.data,
                },
            }
            for att in body.attachments
        ]
        content_blocks.append({"type": "text", "text": body.message})
        api_messages.append({"role": "user", "content": content_blocks})
    else:
        api_messages.append({"role": "user", "content": body.message})

    # 6. Build system prompt. For SOL, inject the user's real project data so
    #    the assistant knows current budget, progress, and dates.
    #    For chat general, pass user_message so the router selects only
    #    relevant KB docs (reduce input tokens ~80% manteniendo calidad).
    project_context = ""
    if body.context_type == "sol":
        project_context = await _build_sol_project_context(db, current_user.id)

    # Capa 1B — perfil global del usuario y memoria del workspace activo.
    # El perfil viaja siempre. La memoria del workspace solo si la
    # conversación está vinculada a uno. Best-effort: si algo falla acá,
    # mejor responder sin memoria que romper el chat.
    profile_items: list[tuple[str, str]] = []
    workspace_memory: list[tuple[str, str]] = []
    workspace_name: str | None = None
    try:
        profile_items = await _load_profile_items(db, current_user.id)
        if conv.workspace_id is not None:
            workspace_memory = await _load_workspace_memory(db, conv.workspace_id)
            ws_obj = await db.get(Workspace, conv.workspace_id)
            if ws_obj is not None:
                workspace_name = ws_obj.name
    except Exception:
        logger.exception("Error cargando memoria (continúa sin memoria)")

    system_prompt = await build_system_prompt(
        body.context_type,
        project_context,
        user_message=body.message,
        profile_items=profile_items,
        workspace_memory=workspace_memory,
        workspace_name=workspace_name,
    )

    conv_id_str = str(conv.id)

    # 7. Tools de retrieval: solo en chat general (no SOL — SOL tiene su
    #    propio agente). Si el turno trae imágenes adjuntas, deshabilitamos
    #    tools: el flujo multimodal va directo a una sola pasada del modelo.
    use_retrieval_tools = (
        body.context_type == "chat" and not body.attachments
    )
    # Capa 1B: además de retrieval, exponemos `remember` para que el modelo
    # guarde memoria durante el chat (captura híbrida). El dispatcher lleva
    # el contexto (user + workspace de la conversación).
    if use_retrieval_tools:
        tools_arg = RETRIEVAL_TOOL_SCHEMAS + [REMEMBER_TOOL_SCHEMA]
        tool_runner_arg = _make_chat_tool_runner(
            db, current_user.id, conv.workspace_id
        )
    else:
        tools_arg = None
        tool_runner_arg = None

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

        # Selector dinámico Haiku/Sonnet. Queries simples van a Haiku
        # (~75% más barato); las complejas, multimodales o SOL a Sonnet.
        selected_model = pick_model(
            body.message,
            context_type=body.context_type,
            has_attachments=bool(body.attachments),
            plan=current_user.plan,
        )

        try:
            async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
                async for event in stream_chat(
                    api_messages,
                    system_prompt,
                    tools=tools_arg,
                    tool_runner=tool_runner_arg,
                    model=selected_model,
                ):
                    etype = event["type"]
                    if etype == "delta":
                        full_response += event["text"]
                        yield _sse({"type": "delta", "text": event["text"]})
                    elif etype == "tool_use":
                        # Le avisamos al frontend que el modelo está
                        # consultando una fuente externa (UX: "Consultando
                        # dolarapi.com..."). El input puede tener datos
                        # sensibles? No en estas tools (URL pública / serie_id),
                        # pero igual lo recortamos por las dudas.
                        yield _sse(
                            {
                                "type": "tool_use",
                                "name": event["name"],
                                "input": event.get("input") or {},
                            }
                        )
                    elif etype == "tool_result":
                        # No mandamos el payload completo al frontend (puede
                        # ser muy grande). Solo nombre + flag de error.
                        result = event.get("result") or {}
                        yield _sse(
                            {
                                "type": "tool_result",
                                "name": event["name"],
                                "ok": "error" not in result,
                                "source": result.get("source") or result.get("url"),
                            }
                        )
                    elif etype == "end":
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
            # En producción NO exponemos el tipo/mensaje real al cliente:
            # Anthropic suele incluir parte del request en el error, lo
            # que puede filtrar prompts, API key parcial, o info de
            # rate-limit que sirve para reconnaissance. En DEBUG sí
            # exponemos para facilitar dev.
            if settings.DEBUG:
                err_type = type(e).__name__
                err_msg = (str(e) or "").splitlines()[0][:240] if str(e) else ""
                msg = f"Error generando respuesta [{err_type}: {err_msg}]"
            else:
                msg = "Error generando respuesta. Si el problema persiste, contactá soporte."
            yield _sse({"type": "error", "message": msg})
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
                model=selected_model,  # modelo real que respondió (Haiku/Sonnet)
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
