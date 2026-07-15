"""
SOL agent service.

Orquesta un loop tool-use con Claude:
  user message → Claude → (opcional) tool_use → ejecutamos tool →
  tool_result → Claude continúa → ... → respuesta final al usuario.

Cada paso se transmite al frontend como SSE para feedback inmediato.

Eventos SSE emitidos:
  - {"type": "start",     "conversation_id": "..."}
  - {"type": "thinking"} (al iniciar cada vuelta del loop)
  - {"type": "tool_use",  "name": "schedule_reminder", "input": {...}}
  - {"type": "tool_result","name": "schedule_reminder", "result": {...}}
  - {"type": "delta",     "text": "..."}
  - {"type": "done",      "tokens_used": 1234}
  - {"type": "error",     "message": "..."}

Diferencias vs /api/chat:
  - Mantiene mismo modelo de Conversation/Message para historial.
  - System prompt está pensado para acción, no solo conversación.
  - Loop tool-use con tope de iteraciones para evitar infinitos.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from models.user import User
from services.agent_tools import TOOL_IMPLS, TOOL_SCHEMAS, run_tool
from services.llm_providers import get_provider
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


MAX_AGENT_ITERATIONS = 8  # tope duro para evitar bucles


SOL_AGENT_SYSTEM_PROMPT_TEMPLATE = """<identidad>
Sos SOL, el copiloto ejecutivo de RE Expert para profesionales del Real Estate
argentino — el Jarvis del usuario: conocés su operación completa y actuás.
Sos un AGENTE de verdad: tomás iniciativa, hacés preguntas, recordás cosas,
preparás mensajes para contactos del usuario (links de WhatsApp/Telegram que
él envía con un click) y automatizás tareas. No sos un chatbot pasivo.
Hablás español rioplatense, cálida pero profesional. Concisa: no monologueás.
Hoy es __TODAY__ (zona AR).
</identidad>

<contexto_usuario>
Snapshot al momento de esta conversación:
__CONTEXT_PACK__

Usá este contexto para responder al toque sin llamar tools si el dato ya está
acá. Para más detalle o datos frescos, usá las tools. Sé proactiva con lo que
ves: pagos vencidos, hitos cerca, desvíos de presupuesto — mencionalos cuando
venga al caso.
</contexto_usuario>

<grounding>
REGLA DE ORO: trabajás SOLO con información del aplicativo (su base de datos).
- Cualquier cifra o dato de proyecto/pago/deal/agenda: usá la tool
  correspondiente ANTES de afirmarlo, salvo que ya esté en el contexto de
  arriba o en un tool_result de esta conversación.
- Para totales y sumas usá get_payments_summary — NUNCA sumes filas vos.
- Si el dato no existe: decí "no tengo ese dato cargado" y ofrecé cargarlo.
  NUNCA inventes ni estimes montos, fechas, teléfonos ni datos.
- No traés información de la web. get_news es el feed curado de la app.
</grounding>

<confirmacion_de_acciones>
Registrar pago/hito/precio, agendar recordatorio y crear/editar contacto son
acciones de DOS PASOS. Cuando llamás una de esas tools NO se ejecuta: devuelve
`{needs_confirmation, resumen, confirm_token}`. El flujo obligatorio:
  1. Llamá la tool con los datos.
  2. Mostrale al usuario el `resumen` tal cual y preguntale si confirma
     ("Voy a registrar un pago de $X. ¿Lo confirmo?"). TERMINÁ tu turno ahí.
  3. Recién cuando responda que SÍ (en un mensaje nuevo), llamá
     confirm_action(confirm_token) con el token recibido.
NUNCA llames confirm_action en el mismo turno que generaste el token: el
sistema lo rechaza. Si dice que no o cambia un dato, descartá el token y
volvé a empezar. Si en el historial ves `<!--sol-confirm:TOKEN-->` (la acción
pendiente del turno anterior) y el usuario ahora confirma, usá ESE token.
El marcador es interno: no lo menciones ni lo repitas.
Cuando una acción se confirma y ejecuta OK, avisalo en UNA línea
("✓ Pago registrado.").
</confirmacion_de_acciones>

<tools>
Identidad/preferencias: get_my_profile (leé email/teléfono/prefs) ·
  set_my_phone (+54…) · set_automation_prefs (mergea con lo previo).
Proyecto (lectura): query_project_status · query_payments · query_milestones ·
  query_materials · get_payments_summary (totales reales por estado).
Proyecto (escritura, con confirmación): register_payment · register_milestone ·
  register_material_price.
Recordatorios/citas: schedule_reminder (futuro; canales disponibles HOY:
  in_app y telegram) · list_reminders · cancel_reminder. El sistema los
  dispara solo. Las "citas"/reuniones son schedule_reminder con fecha/hora ISO
  y tz de Argentina; si involucran a un contacto, agendá Y ofrecé avisarle con
  compose_message_to_contact.
Contactos (crear/editar con confirmación): add_contact · update_contact ·
  list_contacts · find_contact. Si el usuario menciona a alguien nuevo,
  ofrecé guardarlo; pedile el teléfono.
Compartir con terceros (human-in-the-loop): share_pdf_with_contact (PDF +
  link wa.me/t.me precargado) · compose_message_to_contact (solo texto).
  El usuario envía con UN click; vos nunca enviás directo a terceros.
Documentos propios: generate_pdf_report · generate_docx_report.
Conocimiento de la app: get_news (titulares del mercado) · search_chats
  (conversaciones pasadas con el Chat Experto) · get_opportunities (Deal Room:
  score, TIR, recomendación).
Otros: plan_route · get_user_channels · send_message_now (mensaje INMEDIATO al
  propio usuario; canales HOY: in_app y telegram). Si el usuario te pide que le
  escribas por WhatsApp a ÉL, WhatsApp todavía NO está disponible como canal para
  avisarle: decilo con honestidad ("por ahora no puedo escribirte por WhatsApp")
  y ofrecé Telegram o la app — NUNCA inventes que es por "su plan". (Para mandarle
  a un CONTACTO sí hay wa.me vía compose_message_to_contact.)
</tools>

<flujos>
1. PRIMER mensaje: llamá get_my_profile (silencioso).
   - Sin phone → pedíselo ("¿me pasás tu WhatsApp? Lo uso para recordatorios")
     y guardalo con set_my_phone. Si ya te lo dio en el mensaje, guardalo
     directo sin volver a preguntar.
   - Con phone pero sin automation_prefs → preguntá qué quiere que le avises
     (pagos por vencer, avance semanal, sobrecostos) y guardá con
     set_automation_prefs.
   - Con todo → ofrecé algo útil basado en su contexto.
2. Mencionan a otra persona ("decile a Carlos que vamos mañana"):
   find_contact → si no existe, pedí el número → compose_message_to_contact /
   share_pdf_with_contact → devolvé el link wa.me/t.me clickeable en Markdown.
3. PDF para un tercero: find_contact → share_pdf_with_contact(contact_id,
   scope) → "Listo, [acá tenés el WhatsApp listo](URL). Solo tocá enviar."
4. Recordatorio: "mañana 10am" → ISO 8601 con tz America/Argentina/Buenos_Aires
   → schedule_reminder (canal telegram si está conectado, si no in_app) →
   flujo de confirmación.
</flujos>

<manejo_de_errores>
Si una tool devuelve {"error": ...}: explicáselo al usuario en lenguaje claro
y pedile lo que falte. No reintentes el mismo dato inválido. Markdown simple;
links como [texto](url).
</manejo_de_errores>"""


def _system_prompt(context_pack: str = "") -> str:
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    # Usamos replace en vez de .format() para evitar conflicto con {} literales en el prompt.
    return (
        SOL_AGENT_SYSTEM_PROMPT_TEMPLATE
        .replace("__TODAY__", today)
        .replace("__CONTEXT_PACK__", context_pack or "(sin datos cargados todavía)")
    )


def _safe(v) -> str:
    """Neutraliza texto libre del usuario antes de interpolarlo en el prompt XML.
    Reemplaza '<'/'>' por homoglyphs para que un valor controlado por el usuario
    (nombre de proyecto, concepto de pago, título de oportunidad, etc.) NO pueda
    abrir/cerrar etiquetas ni inyectar instrucciones dentro del system prompt
    (prompt-injection / auto-inyección). Cosmético para el modelo; no toca datos."""
    return str(v).replace("<", "‹").replace(">", "›")


def render_context_pack(data: dict) -> str:
    """Convierte el snapshot del usuario en texto compacto para el prompt.
    Función pura (testeable sin DB)."""
    lines: list[str] = []
    lines.append(
        f"- Usuario: {_safe(data.get('nombre') or data.get('email', '?'))} · plan {_safe(data.get('plan', '?'))}"
        + (" · Telegram conectado" if data.get("telegram") else " · SIN Telegram")
    )
    projs = data.get("projects") or []
    if projs:
        lines.append(f"- Proyectos ({len(projs)}):")
        for p in projs[:5]:
            desvio = ""
            try:
                if p.get("presupuesto_base") and p.get("costo_real") is not None:
                    d = (float(p["costo_real"]) / float(p["presupuesto_base"]) - 1) * 100
                    if abs(d) >= 1:
                        desvio = f", costo {'+' if d > 0 else ''}{d:.0f}% vs presupuesto"
            except (TypeError, ValueError, ZeroDivisionError):
                pass
            lines.append(
                f"    · {_safe(p.get('nombre'))}: avance {p.get('avance_real_pct', 0):.0f}% "
                f"(plan {p.get('avance_plan_pct', 0):.0f}%){desvio}"
            )
    else:
        lines.append("- Proyectos: ninguno cargado aún (ofrecé crear el primero desde el Panel).")
    pagos = data.get("pagos_pendientes") or []
    if pagos:
        # Totales REALES (count/sum de toda la tabla), no de las 8 filas del
        # preview: presentar la suma de 8 como si fuera el total era mentir.
        n_tot = data.get("pagos_pendientes_count", len(pagos))
        monto_tot = data.get("pagos_pendientes_total")
        if monto_tot is None:  # sin agregación → sumamos lo que hay, marcando que es parcial
            monto_tot = sum(float(p.get("monto") or 0) for p in pagos)
        prox = ", ".join(
            f"{_safe(p.get('concepto'))} ({p.get('fecha')})" for p in pagos[:3]
        )
        extra = f" (+{n_tot - len(pagos)} más)" if n_tot > len(pagos) else ""
        lines.append(
            f"- Pagos pendientes: {n_tot} por ${float(monto_tot):,.0f} — "
            f"próximos: {prox}{extra}"
        )
    rems = data.get("reminders") or []
    if rems:
        lines.append(
            "- Recordatorios próximos: "
            + "; ".join(f"{_safe(r.get('message'))} ({r.get('due_at')})" for r in rems[:3])
        )
    if data.get("contacts_count"):
        lines.append(f"- Contactos en agenda: {data['contacts_count']}")
    opps = data.get("opportunities") or []
    if opps:
        lines.append(
            "- Deal Room: "
            + "; ".join(
                f"{_safe(o.get('titulo'))} (score {o.get('score')}, {_safe(o.get('recomendacion') or 's/rec')})"
                for o in opps[:3]
            )
        )
    prefs = data.get("automation_prefs") or {}
    if prefs:
        activas = [k for k, v in prefs.items() if v]
        if activas:
            lines.append(f"- Automatizaciones activas: {', '.join(activas)}")
    return "\n".join(lines)


async def build_context_pack(db: AsyncSession, user: User) -> str:
    """Junta el snapshot del usuario (pocas queries chicas) y lo renderiza.
    Best-effort: ante cualquier fallo devuelve pack vacío — SOL funciona igual."""
    try:
        from models.contact import Contact
        from models.opportunity import Opportunity
        from models.payment import Payment
        from models.project import Project
        from models.reminder import Reminder
        from models.user_channel import UserChannel
        from sqlalchemy import func as sqlfunc
        from sqlalchemy import select

        projs = list((await db.execute(
            select(Project).where(Project.user_id == user.id).order_by(Project.created_at)
        )).scalars().all())
        pagos = list((await db.execute(
            select(Payment).where(
                Payment.user_id == user.id, Payment.estado == "pendiente"
            ).order_by(Payment.fecha).limit(8)
        )).scalars().all())
        # Agregación real (no la suma de las 8 filas de arriba).
        pagos_agg = (await db.execute(
            select(sqlfunc.count(Payment.id), sqlfunc.coalesce(sqlfunc.sum(Payment.monto), 0))
            .where(Payment.user_id == user.id, Payment.estado == "pendiente")
        )).first()
        pagos_count = int(pagos_agg[0]) if pagos_agg else len(pagos)
        pagos_total = float(pagos_agg[1]) if pagos_agg else 0.0
        rems = list((await db.execute(
            select(Reminder).where(
                Reminder.user_id == user.id, Reminder.status == "pending"
            ).order_by(Reminder.due_at).limit(5)
        )).scalars().all())
        opps = list((await db.execute(
            select(Opportunity).where(Opportunity.user_id == user.id)
            .order_by(Opportunity.updated_at.desc()).limit(3)
        )).scalars().all())
        n_contacts = (await db.execute(
            select(sqlfunc.count()).select_from(Contact).where(Contact.user_id == user.id)
        )).scalar() or 0
        tg = (await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == user.id,
                UserChannel.channel == "telegram",
                UserChannel.verified.is_(True),
            )
        )).scalars().first()

        data = {
            "nombre": user.full_name,
            "email": user.email,
            "plan": user.plan,
            "telegram": bool(tg),
            "automation_prefs": user.automation_prefs or {},
            "contacts_count": int(n_contacts),
            "projects": [
                {
                    "nombre": p.nombre,
                    "avance_real_pct": float(p.avance_real_pct or 0),
                    "avance_plan_pct": float(p.avance_plan_pct or 0),
                    "presupuesto_base": float(p.presupuesto_base or 0),
                    "costo_real": float(p.costo_real or 0),
                }
                for p in projs
            ],
            "pagos_pendientes": [
                {"concepto": p.concepto, "monto": float(p.monto or 0),
                 "fecha": p.fecha.isoformat() if p.fecha else None}
                for p in pagos
            ],
            "pagos_pendientes_count": pagos_count,
            "pagos_pendientes_total": pagos_total,
            "reminders": [
                # Reminder tiene title/body, NO message. Este bug tiraba
                # AttributeError → el pack entero (try/except de abajo) se caía
                # en silencio para cualquier usuario con recordatorios pendientes.
                {"message": r.title, "due_at": r.due_at.isoformat() if r.due_at else None}
                for r in rems
            ],
            "opportunities": [
                {"titulo": o.titulo, "score": o.score, "recomendacion": o.recomendacion}
                for o in opps
            ],
        }
        return render_context_pack(data)
    except Exception:  # noqa: BLE001 — el pack nunca debe romper a SOL
        logger.exception("build_context_pack falló; sigo sin contexto")
        return ""


async def run_agent(
    db: AsyncSession,
    user: User,
    history: list[dict],
    user_message: str,
    max_iterations: int = MAX_AGENT_ITERATIONS,
) -> AsyncIterator[dict]:
    """
    Ejecuta el loop tool-use y va emitiendo eventos.

    Usa el LLM provider configurado (Gemini o Anthropic) vía abstracción
    en services.llm_providers. El formato de mensajes/tools es el de
    Anthropic; el provider Gemini hace la traducción internamente.
    """
    provider = get_provider()
    context_pack = await build_context_pack(db, user)
    system = _system_prompt(context_pack)
    messages: list[dict] = [
        *[{"role": m["role"], "content": m["content"]} for m in history],
        {"role": "user", "content": user_message},
    ]

    total_input = 0
    total_output = 0
    full_text = ""
    # Tokens de confirmación emitidos EN ESTE turno: si el modelo intenta
    # confirmar uno de estos en la misma vuelta, se rechaza (ver loop abajo).
    tokens_emitidos_turno: set[str] = set()
    tokens_confirmados_turno: set[str] = set()

    for iteration in range(max_iterations):
        yield {"type": "thinking", "iteration": iteration, "provider": provider.name}

        try:
            resp = await provider.generate(
                system=system,
                messages=messages,
                tools=TOOL_SCHEMAS,
                max_tokens=4096,
            )
        except Exception:
            logger.exception("LLM call failed (%s)", provider.name)
            yield {"type": "error", "message": "No pude generar la respuesta en este momento. Probá de nuevo en unos segundos."}
            return

        total_input += resp.usage.get("input_tokens", 0) or 0
        total_output += resp.usage.get("output_tokens", 0) or 0

        # Recolectar bloques de la respuesta unificada
        text_chunks: list[str] = []
        tool_uses: list[dict] = []
        assistant_blocks_for_history: list[dict] = []

        for block in resp.content:
            if block.type == "text":
                text_chunks.append(block.text or "")
                assistant_blocks_for_history.append(
                    {"type": "text", "text": block.text or ""}
                )
            elif block.type == "tool_use":
                tool_uses.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "input": block.input or {},
                    }
                )
                assistant_blocks_for_history.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input or {},
                    }
                )

        # Emitir el texto incremental como un solo "delta" (no es streaming
        # token-a-token, es por turno; el frontend igual lo va concatenando).
        if text_chunks:
            chunk = "".join(text_chunks)
            full_text += chunk
            yield {"type": "delta", "text": chunk}

        # Persistir respuesta del modelo (incluyendo tool_use blocks) en messages
        messages.append({"role": "assistant", "content": assistant_blocks_for_history})

        # Si no usó tools, terminamos.
        if resp.stop_reason != "tool_use" or not tool_uses:
            break

        # Si Gemini emitió tool_use SIN texto previo, mandamos el delta vacío para
        # que el frontend cierre el bubble de "thinking" y muestre los chips.

        # Ejecutar todas las tools que pidió en este turno (en serie por
        # simplicidad; podrían ir en paralelo con asyncio.gather)
        tool_results_blocks: list[dict] = []
        for tu in tool_uses:
            yield {"type": "tool_use", "name": tu["name"], "input": tu["input"]}
            # Human-in-the-loop server-side: no dejar que el modelo confirme una
            # acción cuyo token generó en ESTE mismo turno. La confirmación tiene
            # que venir tras un nuevo mensaje del usuario (turno siguiente).
            if (tu["name"] == "confirm_action"
                    and (tu["input"] or {}).get("confirm_token") in tokens_emitidos_turno):
                result = {"error": (
                    "El usuario todavía no confirmó esta acción. Mostrale el resumen "
                    "y esperá que responda que sí; recién en tu próximo turno confirmá."
                )}
            else:
                result = await run_tool(tu["name"], db, user, tu["input"])
            if isinstance(result, dict) and result.get("confirm_token"):
                tokens_emitidos_turno.add(result["confirm_token"])
            # Si el modelo confirmó OK, ese token ya no está pendiente.
            if (tu["name"] == "confirm_action" and isinstance(result, dict)
                    and result.get("confirmed")):
                tokens_confirmados_turno.add((tu["input"] or {}).get("confirm_token"))
            yield {"type": "tool_result", "name": tu["name"], "result": result}
            tool_results_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

        # Mandar los tool_results en un mensaje de rol "user" (es el formato Anthropic)
        messages.append({"role": "user", "content": tool_results_blocks})

    # Tokens de confirmación que quedaron PENDIENTES (preview mostrado, usuario
    # todavía no dijo que sí). Se persisten como marcador oculto en el historial
    # para que el modelo pueda confirmarlos en el próximo turno (el historial
    # guarda solo texto, no los tool_result blocks).
    pendientes = sorted(tokens_emitidos_turno - tokens_confirmados_turno)
    yield {
        "type": "done",
        "input_tokens": total_input,
        "output_tokens": total_output,
        "tokens_used": total_input + total_output,
        "final_text": full_text,
        "pending_confirmations": pendientes,
        "model": getattr(provider, "model", provider.name),
    }


# Marcador (comentario HTML, invisible en el render) para llevar el/los tokens
# de confirmación pendientes dentro del texto persistido del assistant.
_CONFIRM_MARK_RE = None  # se compila lazy en strip_confirm_marker


def append_confirm_marker(text: str, tokens: list[str]) -> str:
    """Anexa los tokens pendientes como comentario HTML al final del texto que
    se PERSISTE (no el que se muestra al usuario)."""
    if not tokens:
        return text
    return f"{text}\n<!--sol-confirm:{','.join(tokens)}-->"


def strip_confirm_marker(text: str) -> str:
    """Quita el marcador (por si alguna vista muestra el content persistido)."""
    import re
    global _CONFIRM_MARK_RE
    if _CONFIRM_MARK_RE is None:
        _CONFIRM_MARK_RE = re.compile(r"\n?<!--sol-confirm:[^>]*-->")
    return _CONFIRM_MARK_RE.sub("", text or "")


# ════════════════════════════════════════════════════════════════════
# Lista de tools que el frontend puede mostrar como acciones
# ("chips" debajo del input). El frontend solo muestra label/icon;
# el backend valida y ejecuta.
# ════════════════════════════════════════════════════════════════════
PUBLIC_TOOL_INDEX = [
    {"name": n, "schema": s}
    for n, s in zip([t["name"] for t in TOOL_SCHEMAS], TOOL_SCHEMAS, strict=False)
]
__all__ = ["run_agent", "PUBLIC_TOOL_INDEX", "TOOL_IMPLS"]
