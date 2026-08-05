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
import time
from datetime import UTC, datetime
from uuid import UUID

from api.schemas.chat import ChatRequest
from config.settings import settings
from core.auth import get_current_user
from core.pii_guard import texto_seguro_para_memoria
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.plan_analysis import PlanAlert, PlanAnalysis, PlanFile, PlanProject, PlanTask
from models.project import Project, ProjectMilestone
from models.user import User
from models.workspace import UserProfileGlobal, Workspace, WorkspaceMemory
from services import location_service
from services.anthropic_service import build_system_prompt, stream_chat
from services.calculator_tools import (
    CALCULATOR_TOOL_IMPLS,
    CALCULATOR_TOOL_SCHEMAS,
    run_calculator_tool,
)
from services.corralones import reverse_geocode
from services.financial_artifact import DOCUMENT_TOOL_SCHEMA, generar_documento
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

# Nombres de excepción de fallos TRANSITORIOS de red/timeout contra el LLM
# (SDK de Anthropic + httpx). Los matcheamos por nombre para no acoplar el
# router a esas libs; un hipo de red es lo más común y NO debe mostrar el
# mensaje alarmante de "contactá soporte".
_TRANSIENT_LLM_ERRORS = frozenset({
    "APIConnectionError", "APITimeoutError", "APIConnectionTimeoutError",
    "ConnectError", "ConnectTimeout", "ReadTimeout", "ReadError", "WriteError",
    "TransportError", "TimeoutException", "RemoteProtocolError", "PoolTimeout",
})


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
    # Las conversaciones de SOL (agente) tienen su propio endpoint y prompt;
    # mezclar el chat principal sobre ellas corrompe el historial del agente.
    if getattr(conv, "section", None) in ("sol", "sol_telegram"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada",
        )
    return conv


# Ubicación del usuario → "Ciudad, Provincia" para el system prompt.
# Caché 6 h por usuario: el reverse-geocode externo no se paga por mensaje.
#
# REGLA DE NEGOCIO (no tocar): el TTL es 6 h para TODOS los resultados, incluido
# el vacío. Si el geocoder falla, ese vacío se sostiene las 6 h igual: se
# prefiere no golpear el servicio externo antes que recuperar la jurisdicción
# rápido. Es decisión de producto, no un descuido.
#
# Lo único que se agrega es un TECHO al dict. Es in-process y sin tope entraba
# una entrada por usuario que chatee y no salía nunca, ni siquiera al vencer el
# TTL: en un proceso de larga vida eso acumula memoria para siempre. El desalojo
# NO cambia ninguna respuesta —lo que se tira se vuelve a calcular igual que si
# hubiera vencido— y arranca recién pasado el tope, que está holgado a propósito:
# es un techo de contención, no un tamaño de trabajo.
_LOC_LABEL_CACHE: dict[UUID, tuple[str, float]] = {}
_LOC_LABEL_TTL = 6 * 3600
_LOC_LABEL_MAX = 5000


def _loc_cache_set(user_id: UUID, label: str) -> None:
    ahora = time.time()
    _LOC_LABEL_CACHE[user_id] = (label, ahora)
    if len(_LOC_LABEL_CACHE) <= _LOC_LABEL_MAX:
        return
    # primero las vencidas: sacarlas es gratis, ya no las devolvería nadie
    for uid in [
        u for u, (_, ts) in _LOC_LABEL_CACHE.items()
        if ahora - ts >= _LOC_LABEL_TTL
    ]:
        _LOC_LABEL_CACHE.pop(uid, None)
    # si aún así sobra, la más vieja (dict conserva el orden de inserción)
    while len(_LOC_LABEL_CACHE) > _LOC_LABEL_MAX:
        _LOC_LABEL_CACHE.pop(next(iter(_LOC_LABEL_CACHE)), None)


async def _get_user_location_label(db: AsyncSession, user_id: UUID) -> str:
    hit = _LOC_LABEL_CACHE.get(user_id)
    if hit and time.time() - hit[1] < _LOC_LABEL_TTL:
        return hit[0]
    label = ""
    try:
        fix = await location_service.get_latest(db, user_id)
        if fix is not None:
            geo = await reverse_geocode(fix.lat, fix.lon)
            label = geo.get("zona") or ""
    except Exception:  # noqa: BLE001 — sin ubicación no se rompe el chat
        label = ""
    _loc_cache_set(user_id, label)
    return label


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


async def _load_known_projects(
    db: AsyncSession, user_id: UUID
) -> list[str]:
    """Memoria transversal: los proyectos del usuario en TODA la plataforma.

    Junta workspaces, proyectos del Panel y proyectos de Planos (los más
    recientes primero) para que el chat sepa en qué anda el usuario aunque
    la conversación sea nueva y suelta. Best-effort: nunca rompe el chat.
    """
    names: list[str] = []
    seen: set[str] = set()

    def _add(n: str | None) -> None:
        n = (n or "").strip()
        if n and n.lower() not in seen and n.lower() not in ("mi proyecto", "nueva conversación"):
            seen.add(n.lower())
            names.append(n[:80])

    try:
        for row in (await db.execute(
            select(Workspace.name).where(Workspace.user_id == user_id)
            .order_by(Workspace.updated_at.desc()).limit(6)
        )).scalars():
            _add(row)
        for row in (await db.execute(
            select(Project.nombre).where(Project.user_id == user_id)
            .order_by(Project.updated_at.desc()).limit(6)
        )).scalars():
            _add(row)
        for row in (await db.execute(
            select(PlanProject.name).where(PlanProject.user_id == user_id)
            .order_by(PlanProject.created_at.desc()).limit(6)
        )).scalars():
            _add(row)
    except Exception:  # noqa: BLE001 — la memoria nunca tumba el chat
        logger.exception("known_projects: fallo cargando proyectos")
    return names[:8]


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

    # Barrera determinista contra persistir datos financieros o credenciales.
    # La memoria se guarda EN SILENCIO (source="auto-silent"), sin que el
    # usuario confirme, y hasta acá lo único que lo impedía era una frase en el
    # prompt — o sea, nada verificable. Esto corre en el servidor, antes del
    # INSERT, y no depende de que el modelo obedezca.
    seguro, tipo = texto_seguro_para_memoria(key, value)
    if not seguro:
        logger.warning(
            "Memoria bloqueada para user %s: se detectó %s en el contenido", user_id, tipo
        )
        return {
            "error": (
                f"No guardo datos de este tipo ({tipo}) por seguridad. "
                "Si necesitás tenerlo a mano, usá un gestor de contraseñas."
            ),
            "saved": False,
        }

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


# ════════════════════════════════════════════════════════════════════
# Acceso directo (SOLO LECTURA) a los datos del usuario en la plataforma:
# Panel de Proyecto y Análisis de Planos. El modelo las llama cuando la
# consulta refiere a los proyectos/obras del usuario, en vez de pedirle
# contexto que la plataforma ya tiene. Siempre scopeado a current_user.
# ════════════════════════════════════════════════════════════════════
PROJECT_DATA_TOOL_SCHEMA: dict = {
    "name": "consultar_panel_proyecto",
    "description": (
        "Lee los datos REALES del Panel de Proyecto del usuario: presupuesto "
        "base, costo real, avance real vs planeado, plazos, fechas y estado de "
        "los hitos. Llamala SIEMPRE que la consulta refiera a su proyecto/obra "
        "(números, avance, desvíos, fechas) en vez de pedirle los datos."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "proyecto": {"type": "string",
                         "description": "Filtro opcional por nombre (o parte) del proyecto"},
        },
    },
}

PLANOS_DATA_TOOL_SCHEMA: dict = {
    "name": "consultar_analisis_planos",
    "description": (
        "Lee los proyectos de Análisis de Planos del usuario: planos cargados, "
        "alertas por prioridad (críticas/altas/…), tareas pendientes y el resumen "
        "del último análisis técnico. Llamala SIEMPRE que la consulta refiera a "
        "sus planos, observaciones de obra o el estado técnico de un proyecto."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "proyecto": {"type": "string",
                         "description": "Filtro opcional por nombre (o parte) del proyecto"},
        },
    },
}


def _fnum(v) -> float:
    try:
        return round(float(v), 2)
    except Exception:  # noqa: BLE001
        return 0.0


async def _consultar_panel_proyecto(db: AsyncSession, user_id: UUID, inputs: dict) -> dict:
    filtro = str(inputs.get("proyecto") or "").strip().lower()
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    projs = list(result.scalars().all())
    if filtro:
        matched = [p for p in projs if filtro in (p.nombre or "").lower()]
        projs = matched or projs
    if not projs:
        return {"proyectos": [], "nota": "No hay proyectos cargados en el Panel de Proyecto."}
    out = []
    for p in projs[:5]:
        ms = (await db.execute(
            select(ProjectMilestone)
            .where(ProjectMilestone.project_id == p.id)
            .order_by(ProjectMilestone.orden.asc())
        )).scalars().all()
        out.append({
            "nombre": p.nombre,
            "estado": f"{p.estado} — {p.estado_texto}",
            "presupuesto_base_usd": _fnum(p.presupuesto_base),
            "costo_real_usd": _fnum(p.costo_real),
            "avance_real_pct": _fnum(p.avance_real_pct),
            "avance_plan_pct": _fnum(p.avance_plan_pct),
            "plazo_meses": f"{p.meses_transcurridos}/{p.meses_total}",
            "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
            "entrega_programada": p.fecha_entrega_programada.isoformat() if p.fecha_entrega_programada else None,
            "entrega_estimada": p.fecha_entrega_estimada.isoformat() if p.fecha_entrega_estimada else None,
            "hitos": [{
                "nombre": m.nombre,
                "estado": m.estado,
                "fecha_objetivo": m.fecha_objetivo.isoformat() if m.fecha_objetivo else None,
                "fecha_real": m.fecha_real.isoformat() if m.fecha_real else None,
            } for m in ms[:12]],
        })
    return {"proyectos": out}


async def _consultar_analisis_planos(db: AsyncSession, user_id: UUID, inputs: dict) -> dict:
    filtro = str(inputs.get("proyecto") or "").strip().lower()
    result = await db.execute(select(PlanProject).where(PlanProject.user_id == user_id))
    projs = list(result.scalars().all())
    if filtro:
        matched = [p for p in projs if filtro in (p.name or "").lower()]
        projs = matched or projs
    if not projs:
        return {"proyectos": [], "nota": "No hay proyectos en Análisis de Planos."}
    out = []
    for p in projs[:4]:
        planos = (await db.execute(
            select(PlanFile.file_name, PlanFile.detected_plan_type, PlanFile.status)
            .where(PlanFile.project_id == p.id, PlanFile.is_current_version.is_(True))
        )).all()
        alerts = (await db.execute(
            select(PlanAlert)
            .where(PlanAlert.project_id == p.id,
                   PlanAlert.status.in_(("pendiente", "en_revision", "validado")))
            .order_by(PlanAlert.created_at.desc())
        )).scalars().all()
        por_prioridad: dict[str, int] = {}
        for a in alerts:
            por_prioridad[a.priority] = por_prioridad.get(a.priority, 0) + 1
        destacadas = [{
            "titulo": a.title,
            "prioridad": a.priority,
            "categoria": a.category,
            "recomendacion": (a.recommendation or "")[:220],
        } for a in alerts if a.priority in ("critica", "alta")][:6]
        tareas = (await db.execute(
            select(PlanTask)
            .where(PlanTask.project_id == p.id,
                   PlanTask.status.in_(("pendiente", "en_curso", "en_revision")))
            .order_by(PlanTask.created_at.desc())
        )).scalars().all()
        ultimo = (await db.execute(
            select(PlanAnalysis)
            .where(PlanAnalysis.project_id == p.id)
            .order_by(PlanAnalysis.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        out.append({
            "nombre": p.name,
            "tipo_obra": p.obra_type,
            "ubicacion": p.location or None,
            "etapa": p.stage,
            "cliente": p.client_name or None,
            "planos": [{"archivo": f, "tipo": t or None, "estado": st} for f, t, st in planos[:10]],
            "alertas_abiertas_por_prioridad": por_prioridad,
            "alertas_destacadas": destacadas,
            "tareas_pendientes": [{"titulo": t.title, "prioridad": t.priority,
                                   "estado": t.status} for t in tareas[:8]],
            "ultimo_analisis": ({
                "fecha": ultimo.created_at.isoformat(),
                "riesgo_general": ultimo.general_risk,
                "resumen": (ultimo.summary or "")[:600],
                "recomendaciones": list(ultimo.recommendations or [])[:3],
            } if ultimo else None),
        })
    return {"proyectos": out}


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
        # Calculadoras financieras (Capa 2): tools puras, sin db/red.
        if name in CALCULATOR_TOOL_IMPLS:
            return await run_calculator_tool(name, inputs)
        # Entregable descargable (PDF/Excel + link WhatsApp).
        if name == "generar_documento_analisis":
            try:
                return await generar_documento(**(inputs or {}))
            except Exception as e:  # noqa: BLE001
                logger.exception("generar_documento falló")
                return {"error": f"No se pudo generar el documento: {e}", "ok": False}
        # Datos reales del usuario en la plataforma (solo lectura)
        if name == "consultar_panel_proyecto":
            try:
                return await _consultar_panel_proyecto(db, user_id, inputs or {})
            except Exception as e:  # noqa: BLE001
                logger.exception("consultar_panel_proyecto falló")
                return {"error": f"No se pudo leer el Panel de Proyecto: {e}"}
        if name == "consultar_analisis_planos":
            try:
                return await _consultar_analisis_planos(db, user_id, inputs or {})
            except Exception as e:  # noqa: BLE001
                logger.exception("consultar_analisis_planos falló")
                return {"error": f"No se pudo leer Análisis de Planos: {e}"}
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
    # SOL ya no tiene gate propio: el router de chat exige `require_access`
    # (modelo pago-only), y el trial habilita SOL igual que pro.

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
    # Filtramos mensajes con content vacío: Anthropic rechaza bloques de texto
    # vacíos con 400. Defensa para historiales que puedan tener un mensaje
    # assistant vacío persistido (ver guard al persistir, más abajo).
    api_messages: list[dict] = [
        {"role": m.role, "content": m.content}
        for m in history
        if m.content and m.content.strip()
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
    known_projects: list[str] = []
    user_location = ""
    try:
        profile_items = await _load_profile_items(db, current_user.id)
        known_projects = await _load_known_projects(db, current_user.id)
        # Proyectos que el propio chat guardó con remember(scope='profile')
        for k, v in profile_items:
            if k.startswith("proyecto"):
                nom = (v.split(",")[0] or "").strip()[:80]
                if nom and nom.lower() not in {n.lower() for n in known_projects}:
                    known_projects.append(nom)
        user_location = await _get_user_location_label(db, current_user.id)
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
        known_projects=known_projects,
        user_location=user_location,
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
        tools_arg = (
            RETRIEVAL_TOOL_SCHEMAS
            + CALCULATOR_TOOL_SCHEMAS
            + [REMEMBER_TOOL_SCHEMA, DOCUMENT_TOOL_SCHEMA,
               PROJECT_DATA_TOOL_SCHEMA, PLANOS_DATA_TOOL_SCHEMA]
        )
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
            # Mapear fallos de upstream (LLM) a mensajes prolijos de "no
            # disponible" en vez de un error feo. Cubre: saldo de API agotado
            # (400 "credit balance"), auth/permiso (401/403), rate limit (429)
            # y caídas/saturación (5xx/529). El error real ya quedó logueado
            # arriba; al usuario NO le filtramos detalle.
            status_code = getattr(e, "status_code", None)
            emsg = (str(e) or "").lower()
            if "credit balance" in emsg or "billing" in emsg or status_code in (401, 402, 403):
                msg = "El asistente no está disponible en este momento. Reintentá en unos minutos."
            elif status_code in (429, 500, 502, 503, 529) or "overloaded" in emsg or "rate limit" in emsg:
                msg = "El asistente está con mucha demanda ahora. Probá de nuevo en un minuto."
            elif type(e).__name__ in _TRANSIENT_LLM_ERRORS:
                # Error de red/timeout contra el LLM (el caso MÁS común de un hipo
                # transitorio): sin status_code ni keywords, antes caía en el
                # mensaje alarmante de "contactá soporte". Lo tratamos como demanda.
                msg = "El asistente está con mucha demanda ahora. Probá de nuevo en un minuto."
            elif settings.DEBUG:
                err_type = type(e).__name__
                err_msg = (str(e) or "").splitlines()[0][:240] if str(e) else ""
                msg = f"Error generando respuesta [{err_type}: {err_msg}]"
            else:
                msg = "Error generando respuesta. Si el problema persiste, contactá soporte."
            yield _sse({"type": "error", "message": msg})
            return

        # Persist assistant message (con token count si lo hay).
        # Guard anti-vacío: si el modelo no produjo texto (p.ej. el loop de
        # tool-use terminó sin prosa), NO persistimos. Un content "" se
        # re-enviaría en el próximo turno y Anthropic rechaza bloques de texto
        # vacíos con 400 → dejaría la conversación inutilizable para siempre.
        assistant_msg_id = None
        if full_response.strip():
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
