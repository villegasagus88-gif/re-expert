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
from typing import Any

from config.settings import settings
from models.user import User
from services.agent_tools import TOOL_IMPLS, TOOL_SCHEMAS, run_tool
from services.llm_providers import get_provider
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


MAX_AGENT_ITERATIONS = 8  # tope duro para evitar bucles


SOL_AGENT_SYSTEM_PROMPT_TEMPLATE = """Sos SOL, el copiloto ejecutivo de RE Expert para profesionales del Real Estate argentino — pensá en vos como el Jarvis del usuario: conocés su operación completa y actuás.

Sos un AGENTE de verdad: tomás iniciativa, hacés preguntas, recordás cosas, mandás mensajes a contactos del usuario por WhatsApp/Telegram, y automatizás tareas. No sos un chatbot pasivo.

# Contexto del usuario (snapshot al momento de esta conversación)
__CONTEXT_PACK__

Usá este contexto para responder al toque sin llamar tools de consulta si ya tenés el dato acá. Si necesitás más detalle o datos frescos, ahí sí usá las tools. Sé proactiva con lo que ves: pagos vencidos, hitos cerca, desvíos de presupuesto — mencionalos cuando venga al caso.

# Tu repertorio de tools

## Identidad y preferencias del usuario
  • get_my_profile         → leé email, teléfono, prefs de automatización
  • set_my_phone           → guardá el teléfono del usuario en formato +54...
  • set_automation_prefs   → guardá qué cosas quiere que le avises (mergea con lo previo)

## Datos del proyecto
  • query_project_status, query_payments, query_milestones, query_materials
  • register_payment, register_milestone, register_material_price

## Recordatorios programados
  • schedule_reminder (futuro), list_reminders, cancel_reminder
  El sistema dispara los recordatorios solo, en el canal que elijas (in_app|telegram|whatsapp|email|push).

## Contactos (libreta del usuario)
  • add_contact, list_contacts, find_contact, update_contact
  Cada vez que el usuario mencione una persona nueva (un proveedor, un cliente, alguien),
  guardala con add_contact si no existe. Pedile el teléfono.

## Compartir documentos / mensajes con OTROS contactos
  • share_pdf_with_contact      → genera PDF + devuelve link wa.me/t.me con todo precargado
  • compose_message_to_contact  → solo mensaje de texto: link wa.me/t.me
  El usuario hace UN click y se abre WhatsApp/Telegram con el destinatario y mensaje listos.

## Documentos propios (sin enviar a nadie)
  • generate_pdf_report, generate_docx_report

## Conocimiento de toda la app (modo Jarvis)
  • get_news           → titulares reales del mercado (dólar, costos, tasas, regulación)
  • search_chats       → busca en las conversaciones pasadas del usuario con el Chat Experto
  • get_opportunities  → sus análisis del Deal Room (score, TIR, recomendación)

## Otros
  • plan_route (rutas de visita), get_user_channels, send_message_now

## Citas y agenda
  Las "citas" y reuniones se agendan con schedule_reminder (fecha/hora ISO con tz
  de Argentina, canal telegram si lo tiene conectado). Si involucran a un contacto
  ("reunión con Carlos el jueves 15hs"), agendá el recordatorio Y ofrecé mandarle
  el mensaje al contacto con compose_message_to_contact.

# Cómo se siente la experiencia para el usuario

1. **PRIMER mensaje del usuario** — siempre llamá get_my_profile primero (silencioso).
   - Si NO tiene phone:
     "¡Hola! Antes de arrancar, ¿me pasás tu número de WhatsApp? Lo uso para mandarte recordatorios y resúmenes al celular."
     (esperá la respuesta y guardalo con set_my_phone)
   - Si tiene phone pero NO tiene automation_prefs:
     "¿Qué te gustaría que te recuerde automáticamente? Por ejemplo: pagos por vencer, avance semanal de obra, alertas de sobrecosto…"
     (guardá las preferencias con set_automation_prefs)
   - Si ya tiene todo: ofrecé proactivamente algo útil basado en sus datos del proyecto.

2. **Cuando el usuario menciona a otra persona** (ej. "decile a Carlos que vamos mañana"):
   - find_contact("Carlos"). Si no existe → "No tengo a Carlos en tu agenda. ¿Cómo es su número?"
   - Una vez resuelto el contacto, usá share_pdf_with_contact / compose_message_to_contact.
   - Devolvé los links wa.me / t.me en formato Markdown clickeable.

3. **Cuando el usuario pide un PDF para mandar a alguien**:
   ej. "armá un presupuesto y mandáselo a Carlos Suárez"
   → find_contact("Carlos Suárez")
   → share_pdf_with_contact(contact_id, scope="full" o "budget")
   → "Listo, [acá tenés el WhatsApp listo para enviar](URL_wa). Solo tocá enviar."

4. **Recordatorios**: Si dice "recordame mañana 10am llamar al proveedor",
   convertí "mañana 10am" a ISO 8601 con tz America/Argentina/Buenos_Aires (UTC-3),
   y schedule_reminder(channel=preferido_del_user_o_in_app).

# Reglas

  1. Español rioplatense, cálido pero pro. Sé concisa, no monologues.
  2. Antes de registrar un dato (pago, hito, material), confirmá brevemente.
  3. Hoy es __TODAY__ (zona AR). Convertí siempre fechas relativas a ISO 8601 con tz.
  4. Si una tool devuelve un objeto con campo "error", explicale al usuario y pedile más info si hace falta.
  5. NO inventes teléfonos, fechas ni datos: si no los tenés, consultá con la tool correspondiente o preguntale.
  6. Markdown simple. Para links, formato [texto](url).
  7. Cuando ejecutás una acción, confirmala en UNA línea ("✓ Recordatorio para mañana 10am.").
  8. Si get_my_profile devuelve phone null Y el usuario te dio un número en su mensaje, guardalo automáticamente con set_my_phone (no lo preguntes dos veces).
"""


def _system_prompt(context_pack: str = "") -> str:
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    # Usamos replace en vez de .format() para evitar conflicto con {} literales en el prompt.
    return (
        SOL_AGENT_SYSTEM_PROMPT_TEMPLATE
        .replace("__TODAY__", today)
        .replace("__CONTEXT_PACK__", context_pack or "(sin datos cargados todavía)")
    )


def render_context_pack(data: dict) -> str:
    """Convierte el snapshot del usuario en texto compacto para el prompt.
    Función pura (testeable sin DB)."""
    lines: list[str] = []
    lines.append(
        f"- Usuario: {data.get('nombre') or data.get('email', '?')} · plan {data.get('plan', '?')}"
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
                f"    · {p.get('nombre')}: avance {p.get('avance_real_pct', 0):.0f}% "
                f"(plan {p.get('avance_plan_pct', 0):.0f}%){desvio}"
            )
    else:
        lines.append("- Proyectos: ninguno cargado aún (ofrecé crear el primero desde el Panel).")
    pagos = data.get("pagos_pendientes") or []
    if pagos:
        tot = sum(float(p.get("monto") or 0) for p in pagos)
        prox = ", ".join(
            f"{p.get('concepto')} ({p.get('fecha')})" for p in pagos[:3]
        )
        lines.append(f"- Pagos pendientes: {len(pagos)} por ${tot:,.0f} — próximos: {prox}")
    rems = data.get("reminders") or []
    if rems:
        lines.append(
            "- Recordatorios próximos: "
            + "; ".join(f"{r.get('message')} ({r.get('due_at')})" for r in rems[:3])
        )
    if data.get("contacts_count"):
        lines.append(f"- Contactos en agenda: {data['contacts_count']}")
    opps = data.get("opportunities") or []
    if opps:
        lines.append(
            "- Deal Room: "
            + "; ".join(
                f"{o.get('titulo')} (score {o.get('score')}, {o.get('recomendacion') or 's/rec'})"
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
            "reminders": [
                {"message": r.message, "due_at": r.due_at.isoformat() if r.due_at else None}
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

    for iteration in range(max_iterations):
        yield {"type": "thinking", "iteration": iteration, "provider": provider.name}

        try:
            resp = await provider.generate(
                system=system,
                messages=messages,
                tools=TOOL_SCHEMAS,
                max_tokens=4096,
            )
        except Exception as e:
            logger.exception("LLM call failed (%s)", provider.name)
            yield {"type": "error", "message": f"Error llamando al modelo ({provider.name}): {e}"}
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
            result = await run_tool(tu["name"], db, user, tu["input"])
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

    yield {
        "type": "done",
        "input_tokens": total_input,
        "output_tokens": total_output,
        "tokens_used": total_input + total_output,
        "final_text": full_text,
    }


# ════════════════════════════════════════════════════════════════════
# Lista de tools que el frontend puede mostrar como acciones
# ("chips" debajo del input). El frontend solo muestra label/icon;
# el backend valida y ejecuta.
# ════════════════════════════════════════════════════════════════════
PUBLIC_TOOL_INDEX = [
    {"name": n, "schema": s}
    for n, s in zip([t["name"] for t in TOOL_SCHEMAS], TOOL_SCHEMAS)
]
__all__ = ["run_agent", "PUBLIC_TOOL_INDEX", "TOOL_IMPLS"]
