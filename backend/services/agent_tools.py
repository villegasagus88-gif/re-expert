"""
Tool definitions for the SOL agent.

Cada tool tiene:
  - JSON schema (para Anthropic tool_use)
  - implementación async que recibe (db, user, **inputs) y devuelve dict

El agent_service itera el loop de tool-use hasta que Claude emite un
mensaje sin tool_use o se llega al límite de iteraciones.

Catálogo de herramientas:
  - query_project_status      Lee estado actual del proyecto del usuario.
  - query_payments            Lista pagos con filtros opcionales.
  - query_milestones          Lista hitos del cronograma.
  - query_materials           Lee tabla de precios de materiales.
  - register_payment          Crea un pago.
  - register_milestone        Crea un hito.
  - register_material_price   Registra precio de material.
  - schedule_reminder         Crea un recordatorio futuro.
  - list_reminders            Lista recordatorios pendientes/enviados del usuario.
  - cancel_reminder           Cancela un recordatorio por id.
  - generate_pdf_report       Genera PDF y devuelve URL descargable.
  - generate_docx_report      Genera DOCX y devuelve URL descargable.
  - send_message_now          Envía un mensaje al canal del usuario en este momento.
  - get_user_channels         Lista canales conectados.
  - plan_route                Stub: arma una ruta optimizada entre paradas (requiere Maps API).
"""
from __future__ import annotations

import logging
from datetime import date as Date
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from models.contact import Contact
from models.material import Material
from models.milestone import Milestone
from models.payment import Payment
from models.project import Project
from models.reminder import Reminder
from models.user import User
from models.user_channel import UserChannel
from sqlalchemy import func as sqlfunc
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# JSON schemas que Claude ve (formato Anthropic tool_use).
# ════════════════════════════════════════════════════════════════════
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "query_project_status",
        "description": (
            "Devuelve el estado actual del proyecto del usuario: presupuesto, "
            "costo real, avance real vs planeado, plazo, fechas y notas. "
            "Usalo cuando el usuario pregunte cómo va la obra, cuánto avanzó, "
            "si hay desvíos, etc."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "query_payments",
        "description": (
            "Lista pagos del usuario filtrando opcionalmente por estado y/o "
            "rango de fechas. Si no pasás filtros, devuelve los últimos 50."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "enum": ["pagado", "pendiente", "cancelado"],
                    "description": "Filtrar por estado.",
                },
                "desde": {"type": "string", "format": "date", "description": "Fecha mínima (YYYY-MM-DD)."},
                "hasta": {"type": "string", "format": "date", "description": "Fecha máxima (YYYY-MM-DD)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
            },
        },
    },
    {
        "name": "query_milestones",
        "description": "Lista los hitos / cronograma del proyecto del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["planned", "in_progress", "done", "delayed"],
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 100},
            },
        },
    },
    {
        "name": "query_materials",
        "description": "Lista materiales (cotizaciones, precios) cargados por el usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100},
            },
        },
    },
    {
        "name": "register_payment",
        "description": (
            "Registra un nuevo pago en el sistema. Solo llamar después de "
            "haber confirmado los datos con el usuario."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concepto": {"type": "string", "minLength": 1},
                "monto": {"type": "number"},
                "fecha": {"type": "string", "format": "date"},
                "estado": {"type": "string", "enum": ["pagado", "pendiente", "cancelado"]},
                "proveedor": {"type": "string"},
                "categoria": {"type": "string"},
                "notas": {"type": "string"},
            },
            "required": ["concepto", "monto", "fecha", "estado"],
        },
    },
    {
        "name": "register_milestone",
        "description": "Registra un hito del cronograma.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "description": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["planned", "in_progress", "done", "delayed"],
                },
                "due_date": {"type": "string", "format": "date"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "register_material_price",
        "description": "Registra/actualiza el precio cotizado de un material.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "unit": {"type": "string", "description": "ej. m2, m3, kg, ud, bolsa"},
                "unit_price": {"type": "number"},
                "currency": {"type": "string", "default": "ARS"},
                "supplier": {"type": "string"},
                "quoted_at": {"type": "string", "format": "date"},
                "notes": {"type": "string"},
            },
            "required": ["name", "unit", "unit_price"],
        },
    },
    {
        "name": "schedule_reminder",
        "description": (
            "Crea un recordatorio futuro para el usuario. El sistema lo "
            "disparará automáticamente al canal indicado (in_app si no hay otro). "
            "Aceptá fechas/hora en formato ISO 8601 con zona horaria. "
            "Si el usuario dice 'mañana 10am', convertí a ISO usando la zona "
            "America/Argentina/Buenos_Aires (UTC-3)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 300},
                "body": {"type": "string", "maxLength": 4000},
                "due_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO 8601 con tz, ej. 2026-05-11T10:00:00-03:00",
                },
                "channel": {
                    "type": "string",
                    "enum": ["in_app", "email", "telegram", "whatsapp", "push"],
                    "default": "in_app",
                },
            },
            "required": ["title", "due_at"],
        },
    },
    {
        "name": "list_reminders",
        "description": "Devuelve los recordatorios del usuario. Por defecto solo los pending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "sent", "failed", "cancelled", "all"],
                    "default": "pending",
                }
            },
        },
    },
    {
        "name": "cancel_reminder",
        "description": "Cancela un recordatorio por su id (uuid).",
        "input_schema": {
            "type": "object",
            "properties": {"reminder_id": {"type": "string", "format": "uuid"}},
            "required": ["reminder_id"],
        },
    },
    {
        "name": "generate_pdf_report",
        "description": (
            "Genera un PDF con el resumen de un alcance (project|payments|milestones) "
            "para el período indicado y devuelve una URL descargable + un mensaje "
            "listo para compartir por WhatsApp/Telegram."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["project", "payments", "milestones", "full"],
                    "default": "project",
                },
                "title": {"type": "string", "default": "Resumen RE Expert"},
                "period_from": {"type": "string", "format": "date"},
                "period_to": {"type": "string", "format": "date"},
            },
        },
    },
    {
        "name": "generate_docx_report",
        "description": "Igual que generate_pdf_report pero genera un DOCX editable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["project", "payments", "milestones", "full"],
                    "default": "project",
                },
                "title": {"type": "string", "default": "Resumen RE Expert"},
                "period_from": {"type": "string", "format": "date"},
                "period_to": {"type": "string", "format": "date"},
            },
        },
    },
    {
        "name": "send_message_now",
        "description": (
            "Envía un mensaje INMEDIATO al usuario por el canal indicado. "
            "Solo llamar si el usuario lo pidió explícitamente. "
            "Para mensajes futuros usá schedule_reminder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "minLength": 1, "maxLength": 4000},
                "channel": {
                    "type": "string",
                    "enum": ["telegram", "whatsapp", "email", "push", "in_app"],
                    "default": "in_app",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "get_user_channels",
        "description": "Devuelve los canales de notificación que el usuario tiene conectados y verificados.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "plan_route",
        "description": (
            "Arma una ruta optimizada entre múltiples paradas (visitas a obra, "
            "proveedores, etc.). Devuelve orden sugerido y duración estimada. "
            "Si Google Maps no está configurado devuelve un fallback simple."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Dirección o lugar de origen."},
                "stops": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "Lista de paradas (direcciones o nombres de lugar).",
                },
                "return_to_origin": {"type": "boolean", "default": False},
            },
            "required": ["origin", "stops"],
        },
    },
    # ─── Identidad y preferencias del usuario ────────────────────────────
    {
        "name": "get_my_profile",
        "description": (
            "Devuelve datos del usuario actual: email, nombre, teléfono, "
            "preferencias de automatización (qué le gusta que le avises). "
            "Llamalo al inicio de la conversación cuando sospeches que falta info."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_my_phone",
        "description": (
            "Guarda el teléfono del usuario en formato internacional (+54911...). "
            "Llamalo cuando el usuario te lo dé. SOL lo usa luego para enviar "
            "WhatsApp/SMS y para componer deep links."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "minLength": 6,
                    "description": "Ej: +5491155555555 o 5491155555555",
                }
            },
            "required": ["phone"],
        },
    },
    {
        "name": "set_automation_prefs",
        "description": (
            "Guarda las preferencias de automatización del usuario (qué cosas "
            "quiere que SOL le avise, por qué canal, frecuencia). Es un objeto "
            "libre con keys como daily_summary, alert_overruns, alert_milestones, "
            "preferred_channel ('telegram'|'whatsapp'|'in_app'). Mergea con lo previo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prefs": {
                    "type": "object",
                    "description": "Diccionario libre con preferencias. Ej: {\"daily_summary\":true,\"preferred_channel\":\"whatsapp\"}",
                }
            },
            "required": ["prefs"],
        },
    },
    # ─── Contactos (libreta) ─────────────────────────────────────────────
    {
        "name": "add_contact",
        "description": (
            "Crea un contacto en la libreta del usuario. Útil cuando el usuario "
            "menciona a alguien por nombre y querés guardar su teléfono / rol. "
            "Si ya existe un contacto con el mismo nombre, no duplica — devuelve "
            "el existente con campo {already_exists:true}."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "phone": {"type": "string", "description": "Internacional, ej +5491155555555"},
                "email": {"type": "string"},
                "role": {"type": "string", "description": "Ej: Proveedor, Cliente, Arquitecto"},
                "notes": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_contacts",
        "description": (
            "Lista los contactos del usuario, filtrando opcionalmente por nombre/rol/teléfono."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Filtro de búsqueda"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
            },
        },
    },
    {
        "name": "find_contact",
        "description": (
            "Busca UN contacto por nombre (fuzzy). Usar antes de send_pdf_to_contact "
            "para resolver 'Carlos' → ID + datos. Devuelve null si no encuentra."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "minLength": 1}},
            "required": ["name"],
        },
    },
    {
        "name": "update_contact",
        "description": "Actualiza datos de un contacto existente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "format": "uuid"},
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["contact_id"],
        },
    },
    # ─── Compartir docs vía deep links (sin Twilio / sin bot) ───────────
    {
        "name": "share_pdf_with_contact",
        "description": (
            "Genera un PDF (resumen/pagos/cronograma/presupuesto) y devuelve un "
            "link 1-click para abrir WhatsApp o Telegram con el mensaje pre-cargado "
            "y el contacto destinatario. El usuario hace UN click y se abre la app "
            "de mensajería con todo listo para enviar.\n\n"
            "Si el contacto no tiene phone → solo Telegram link.\n"
            "Si tiene phone → WhatsApp link (preferido) + Telegram fallback.\n"
            "El PDF queda hosteado y accesible por 24h."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "format": "uuid"},
                "scope": {
                    "type": "string",
                    "enum": ["project", "payments", "milestones", "budget", "full"],
                    "default": "project",
                },
                "title": {"type": "string", "default": "Resumen RE Expert"},
                "custom_message": {
                    "type": "string",
                    "description": "Mensaje personalizado que precede al link. Default: 'Hola <nombre>, te paso el resumen del proyecto:'",
                },
            },
            "required": ["contact_id"],
        },
    },
    {
        "name": "compose_message_to_contact",
        "description": (
            "Compone un link wa.me / t.me para enviarle UN MENSAJE de texto a un "
            "contacto (sin documento). Útil para 'mandale a Carlos: vamos mañana 10am'. "
            "Devuelve URLs que el usuario abre con 1 click."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_id": {"type": "string", "format": "uuid"},
                "message": {"type": "string", "minLength": 1, "maxLength": 4000},
            },
            "required": ["contact_id", "message"],
        },
    },
    {
        "name": "get_news",
        "description": (
            "Titulares recientes del mercado inmobiliario/economía argentina "
            "(mismo feed que la sección Noticias de la app). Usala cuando el "
            "usuario pregunte qué está pasando, por el dólar, costos, tasas, "
            "o pida un resumen de noticias. Devuelve título, fuente, categoría "
            "y link de cada nota."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "todas|macro|mercado|costos|financiacion|regulacion",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 12},
            },
        },
    },
    {
        "name": "search_chats",
        "description": (
            "Busca en las conversaciones PASADAS del usuario con el Chat Experto "
            "de RE Expert. Usala cuando pregunte '¿qué me dijiste de X?', "
            "'¿qué habíamos hablado sobre el terreno de Y?' o para retomar un "
            "tema anterior. Devuelve fragmentos con título del chat y fecha."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2, "maxLength": 120},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_opportunities",
        "description": (
            "Lista los análisis de oportunidades del Deal Room del usuario "
            "(Opportunity Scanner): título, zona, score, recomendación y métricas "
            "clave. Usala cuando pregunte por sus deals, qué oportunidad conviene, "
            "o quiera comparar análisis que ya hizo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
        },
    },
    {
        "name": "get_payments_summary",
        "description": (
            "Totales REALES de pagos del usuario calculados en la base "
            "(cantidad y suma por estado). Usala SIEMPRE que el usuario pida "
            "'cuánto debo', 'total pendiente', 'cuánto pagué' — NO sumes los "
            "pagos vos: pedí el total acá para no equivocarte."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {"type": "string", "enum": ["pendiente", "pagado", "cancelado"],
                           "description": "Filtrar por estado; omitir para el desglose completo."},
            },
        },
    },
    {
        "name": "confirm_action",
        "description": (
            "Ejecuta una acción de escritura que quedó pendiente de confirmación. "
            "Las tools de registrar/agendar/contacto NO ejecutan directo: devuelven "
            "un resumen y un confirm_token. Mostrale el resumen al usuario, esperá "
            "que responda que SÍ, y RECIÉN AHÍ (en tu próximo turno) llamá esta tool "
            "con ese token. Nunca la llames en el mismo turno que generaste el token."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "confirm_token": {"type": "string", "description": "El token devuelto por la tool de escritura."},
            },
            "required": ["confirm_token"],
        },
    },
]


# ════════════════════════════════════════════════════════════════════
# Implementaciones.
# Cada función recibe (db, user, **inputs) y devuelve un dict serializable.
# Errores de validación se devuelven como {"error": "..."} para que el
# modelo pueda reaccionar; excepciones inesperadas se propagan al loop.
# ════════════════════════════════════════════════════════════════════


def _serialize_decimal(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, Date)):
        return v.isoformat()
    if isinstance(v, UUID):
        return str(v)
    return v


async def _tool_get_payments_summary(
    db: AsyncSession, user: User, estado: str | None = None, **_: Any
) -> dict:
    """Totales reales por estado (count + sum) calculados en SQL — el modelo
    NO debe sumar filas a mano. Siempre filtrado por user.id."""
    q = (
        select(Payment.estado, sqlfunc.count(Payment.id),
               sqlfunc.coalesce(sqlfunc.sum(Payment.monto), 0))
        .where(Payment.user_id == user.id)
        .group_by(Payment.estado)
    )
    if estado:
        q = q.where(Payment.estado == estado)
    rows = (await db.execute(q)).all()
    por_estado = {
        r[0]: {"count": int(r[1]), "total": float(r[2])} for r in rows
    }
    return {
        "por_estado": por_estado,
        "total_general": float(sum(v["total"] for v in por_estado.values())),
        "moneda": "ARS",
    }


def _project_to_dict(proj: Project) -> dict:
    return {
        "id": str(proj.id),
        "nombre": proj.nombre,
        "estado": proj.estado,
        "estado_texto": proj.estado_texto,
        "presupuesto_base": float(proj.presupuesto_base),
        "costo_real": float(proj.costo_real),
        "avance_real_pct": float(proj.avance_real_pct),
        "avance_plan_pct": float(proj.avance_plan_pct),
        "meses_transcurridos": proj.meses_transcurridos,
        "meses_total": proj.meses_total,
        "fecha_inicio": proj.fecha_inicio.isoformat() if proj.fecha_inicio else None,
        "fecha_entrega_programada": (
            proj.fecha_entrega_programada.isoformat() if proj.fecha_entrega_programada else None
        ),
        "fecha_entrega_estimada": (
            proj.fecha_entrega_estimada.isoformat() if proj.fecha_entrega_estimada else None
        ),
        "notas": proj.notas,
    }


async def _tool_query_project_status(db: AsyncSession, user: User, **_: Any) -> dict:
    # Multi-proyecto: el usuario puede tener N proyectos — devolvemos todos
    # (scalar_one_or_none() reventaba con MultipleResultsFound con 2+).
    rows = list((
        await db.execute(
            select(Project).where(Project.user_id == user.id).order_by(Project.created_at)
        )
    ).scalars().all())
    if not rows:
        return {"has_project": False, "message": "El usuario no tiene proyecto cargado."}
    return {
        "has_project": True,
        "count": len(rows),
        "projects": [_project_to_dict(p) for p in rows],
        # Compat con prompts/consumidores viejos: el primero como "principal".
        **_project_to_dict(rows[0]),
    }


async def _tool_query_payments(
    db: AsyncSession,
    user: User,
    estado: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    limit: int = 50,
    **_: Any,
) -> dict:
    q = select(Payment).where(Payment.user_id == user.id)
    if estado:
        q = q.where(Payment.estado == estado)
    if desde:
        try:
            q = q.where(Payment.fecha >= Date.fromisoformat(desde))
        except ValueError:
            return {"error": f"Fecha 'desde' inválida: {desde}"}
    if hasta:
        try:
            q = q.where(Payment.fecha <= Date.fromisoformat(hasta))
        except ValueError:
            return {"error": f"Fecha 'hasta' inválida: {hasta}"}
    q = q.order_by(Payment.fecha.desc()).limit(min(max(limit, 1), 200))
    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "concepto": r.concepto,
                "proveedor": r.proveedor,
                "monto": float(r.monto),
                "fecha": r.fecha.isoformat(),
                "estado": r.estado,
                "categoria": r.categoria,
                "notas": r.notas,
            }
            for r in rows
        ],
    }


async def _tool_query_milestones(
    db: AsyncSession, user: User, status: str | None = None, limit: int = 100, **_: Any
) -> dict:
    q = select(Milestone).where(Milestone.user_id == user.id)
    if status:
        q = q.where(Milestone.status == status)
    q = q.order_by(Milestone.due_date.asc().nulls_last()).limit(min(max(limit, 1), 200))
    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "status": r.status,
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in rows
        ],
    }


async def _tool_query_materials(
    db: AsyncSession, user: User, supplier: str | None = None, limit: int = 100, **_: Any
) -> dict:
    q = select(Material).where(Material.user_id == user.id)
    if supplier:
        q = q.where(Material.supplier == supplier)
    q = q.order_by(Material.created_at.desc()).limit(min(max(limit, 1), 500))
    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "unit": r.unit,
                "unit_price": float(r.unit_price),
                "currency": r.currency,
                "supplier": r.supplier,
                "quoted_at": r.quoted_at.isoformat() if r.quoted_at else None,
                "notes": r.notes,
            }
            for r in rows
        ],
    }


async def _tool_register_material_price(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        m = Material(
            user_id=user.id,
            name=inputs["name"],
            unit=inputs["unit"],
            unit_price=Decimal(str(inputs["unit_price"])),
            currency=inputs.get("currency", "ARS"),
            supplier=inputs.get("supplier"),
            quoted_at=Date.fromisoformat(inputs["quoted_at"]) if inputs.get("quoted_at") else None,
            notes=inputs.get("notes"),
        )
        db.add(m)
        await db.commit()
        await db.refresh(m)
        return {"ok": True, "id": str(m.id), "name": m.name}
    except KeyError as e:
        return {"error": f"Campo obligatorio faltante: {e}"}
    except Exception as e:
        logger.exception("register_material_price failed")
        return {"error": str(e)}


async def _tool_register_payment(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        p = Payment(
            user_id=user.id,
            concepto=inputs["concepto"],
            monto=Decimal(str(inputs["monto"])),
            fecha=Date.fromisoformat(inputs["fecha"]),
            estado=inputs["estado"],
            proveedor=inputs.get("proveedor"),
            categoria=inputs.get("categoria"),
            notas=inputs.get("notas"),
        )
        db.add(p)
        await db.commit()
        await db.refresh(p)
        return {"ok": True, "id": str(p.id), "concepto": p.concepto}
    except KeyError as e:
        return {"error": f"Campo obligatorio faltante: {e}"}
    except Exception as e:
        logger.exception("register_payment failed")
        return {"error": str(e)}


async def _tool_register_milestone(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        m = Milestone(
            user_id=user.id,
            name=inputs["name"],
            description=inputs.get("description"),
            status=inputs.get("status", "planned"),
            due_date=Date.fromisoformat(inputs["due_date"]) if inputs.get("due_date") else None,
        )
        db.add(m)
        await db.commit()
        await db.refresh(m)
        return {"ok": True, "id": str(m.id), "name": m.name}
    except Exception as e:
        logger.exception("register_milestone failed")
        return {"error": str(e)}


async def _tool_schedule_reminder(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        title = inputs["title"]
        due_at_raw = inputs["due_at"]
        due_at = datetime.fromisoformat(due_at_raw.replace("Z", "+00:00"))
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if due_at <= datetime.now(timezone.utc):
            return {"error": "due_at tiene que estar en el futuro."}
        r = Reminder(
            user_id=user.id,
            title=title,
            body=inputs.get("body"),
            due_at=due_at,
            channel=inputs.get("channel", "in_app"),
        )
        db.add(r)
        await db.commit()
        await db.refresh(r)
        return {
            "ok": True,
            "id": str(r.id),
            "title": r.title,
            "due_at": r.due_at.isoformat(),
            "channel": r.channel,
        }
    except KeyError as e:
        return {"error": f"Campo obligatorio faltante: {e}"}
    except ValueError as e:
        return {"error": f"Fecha/hora inválida: {e}"}
    except Exception as e:
        logger.exception("schedule_reminder failed")
        return {"error": str(e)}


async def _tool_list_reminders(
    db: AsyncSession, user: User, status: str = "pending", **_: Any
) -> dict:
    q = select(Reminder).where(Reminder.user_id == user.id)
    if status != "all":
        q = q.where(Reminder.status == status)
    q = q.order_by(Reminder.due_at.asc()).limit(200)
    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "title": r.title,
                "body": r.body,
                "due_at": r.due_at.isoformat(),
                "channel": r.channel,
                "status": r.status,
            }
            for r in rows
        ],
    }


async def _tool_cancel_reminder(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        rid = UUID(inputs["reminder_id"])
    except (KeyError, ValueError):
        return {"error": "reminder_id inválido"}
    r = await db.get(Reminder, rid)
    if not r or r.user_id != user.id:
        return {"error": "Recordatorio no encontrado"}
    if r.status != "pending":
        return {"error": f"No se puede cancelar (estado={r.status})"}
    r.status = "cancelled"
    await db.commit()
    return {"ok": True, "id": str(r.id)}


async def _tool_generate_pdf_report(db: AsyncSession, user: User, **inputs: Any) -> dict:
    from services.document_service import generate_report

    try:
        return await generate_report(db, user, fmt="pdf", **inputs)
    except Exception as e:
        logger.exception("generate_pdf_report failed")
        return {"error": str(e)}


async def _tool_generate_docx_report(db: AsyncSession, user: User, **inputs: Any) -> dict:
    from services.document_service import generate_report

    try:
        return await generate_report(db, user, fmt="docx", **inputs)
    except Exception as e:
        logger.exception("generate_docx_report failed")
        return {"error": str(e)}


async def _tool_send_message_now(db: AsyncSession, user: User, **inputs: Any) -> dict:
    from services.notification_dispatcher import dispatch

    message = inputs.get("message")
    channel = inputs.get("channel", "in_app")
    if not message:
        return {"error": "message vacío"}
    result = await dispatch(db, user, channel=channel, title="Mensaje de SOL", body=message)
    return result


async def _tool_get_user_channels(db: AsyncSession, user: User, **_: Any) -> dict:
    rows = (
        await db.execute(select(UserChannel).where(UserChannel.user_id == user.id))
    ).scalars().all()
    return {
        "items": [
            {
                "channel": c.channel,
                "address": c.address,
                "verified": c.verified,
            }
            for c in rows
        ]
    }


async def _tool_plan_route(db: AsyncSession, user: User, **inputs: Any) -> dict:
    from services.maps_service import plan_route

    try:
        return await plan_route(
            origin=inputs["origin"],
            stops=inputs["stops"],
            return_to_origin=inputs.get("return_to_origin", False),
        )
    except KeyError as e:
        return {"error": f"Campo obligatorio faltante: {e}"}
    except Exception as e:
        logger.exception("plan_route failed")
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════
# Identidad / preferencias del usuario
# ════════════════════════════════════════════════════════════════════
def _normalize_phone(phone: str) -> str:
    if not phone:
        return phone
    s = phone.strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return s
    if s.startswith("+"):
        return "+" + digits
    if len(digits) >= 10:
        return "+" + digits
    return digits


async def _tool_get_my_profile(db: AsyncSession, user: User, **_: Any) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "automation_prefs": user.automation_prefs or {},
        "onboarding_completed": user.onboarding_completed,
    }


async def _tool_set_my_phone(db: AsyncSession, user: User, **inputs: Any) -> dict:
    phone = inputs.get("phone", "").strip()
    if not phone:
        return {"error": "phone vacío"}
    normalized = _normalize_phone(phone)
    user.phone = normalized
    await db.commit()
    return {"ok": True, "phone": normalized}


async def _tool_set_automation_prefs(db: AsyncSession, user: User, **inputs: Any) -> dict:
    prefs = inputs.get("prefs")
    if not isinstance(prefs, dict):
        return {"error": "prefs debe ser un objeto"}
    current = dict(user.automation_prefs or {})
    current.update(prefs)
    user.automation_prefs = current
    await db.commit()
    return {"ok": True, "automation_prefs": current}


# ════════════════════════════════════════════════════════════════════
# Contactos
# ════════════════════════════════════════════════════════════════════
async def _tool_add_contact(db: AsyncSession, user: User, **inputs: Any) -> dict:
    name = (inputs.get("name") or "").strip()
    if not name:
        return {"error": "name vacío"}
    # Anti-duplicado por nombre exacto (case-insensitive)
    existing = (
        await db.execute(
            select(Contact).where(
                Contact.user_id == user.id,
                Contact.name.ilike(name),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {
            "already_exists": True,
            "id": str(existing.id),
            "name": existing.name,
            "phone": existing.phone,
            "email": existing.email,
            "role": existing.role,
        }
    c = Contact(
        user_id=user.id,
        name=name,
        phone=_normalize_phone(inputs.get("phone")) if inputs.get("phone") else None,
        email=inputs.get("email"),
        role=inputs.get("role"),
        notes=inputs.get("notes"),
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {
        "ok": True,
        "id": str(c.id),
        "name": c.name,
        "phone": c.phone,
        "email": c.email,
        "role": c.role,
    }


async def _tool_list_contacts(
    db: AsyncSession, user: User, q: str | None = None, limit: int = 50, **_: Any
) -> dict:
    qry = select(Contact).where(Contact.user_id == user.id)
    if q:
        like = f"%{q}%"
        qry = qry.where(or_(Contact.name.ilike(like), Contact.phone.ilike(like), Contact.email.ilike(like)))
    qry = qry.order_by(Contact.name.asc()).limit(min(max(limit, 1), 200))
    rows = (await db.execute(qry)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "phone": r.phone,
                "email": r.email,
                "role": r.role,
                "notes": r.notes,
            }
            for r in rows
        ],
    }


async def _tool_find_contact(db: AsyncSession, user: User, **inputs: Any) -> dict:
    name = (inputs.get("name") or "").strip()
    if not name:
        return {"error": "name vacío"}
    like = f"%{name}%"
    rows = list(
        (
            await db.execute(
                select(Contact)
                .where(Contact.user_id == user.id, Contact.name.ilike(like))
                .order_by(Contact.name.asc())
                .limit(5)
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return {"found": False}
    # Match más exacto: el primero (Postgres ordena alfabéticamente; igualmente el LLM puede pedir otro)
    best = rows[0]
    return {
        "found": True,
        "id": str(best.id),
        "name": best.name,
        "phone": best.phone,
        "email": best.email,
        "role": best.role,
        "alternatives": [
            {"id": str(r.id), "name": r.name, "phone": r.phone}
            for r in rows[1:]
        ],
    }


async def _tool_update_contact(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        cid = UUID(inputs["contact_id"])
    except (KeyError, ValueError):
        return {"error": "contact_id inválido"}
    c = await db.get(Contact, cid)
    if not c or c.user_id != user.id:
        return {"error": "contacto no encontrado"}
    for k in ("name", "email", "role", "notes"):
        if inputs.get(k) is not None:
            setattr(c, k, inputs[k])
    if inputs.get("phone") is not None:
        c.phone = _normalize_phone(inputs["phone"]) if inputs["phone"] else None
    await db.commit()
    await db.refresh(c)
    return {"ok": True, "id": str(c.id), "name": c.name, "phone": c.phone}


# ════════════════════════════════════════════════════════════════════
# Compartir docs / mensajes vía deep links (sin Twilio)
# ════════════════════════════════════════════════════════════════════
def _wa_link(phone: str | None, text: str) -> str | None:
    """Genera link wa.me. Si no hay phone, devuelve None (no se puede WA sin número).
    `phone` debe estar normalizado con + adelante; wa.me lo quiere SIN +.
    """
    if not phone:
        return None
    p = phone.lstrip("+")
    from urllib.parse import quote

    return f"https://wa.me/{p}?text={quote(text)}"


def _tg_share_link(text: str) -> str:
    """Telegram share link genérico — el usuario elige a quién mandárselo en Telegram.
    Si tenemos chat_id del contacto en Telegram, usaremos un sendMessage directo
    en una versión futura; por ahora, share URL alcanza para fricción cero.
    """
    from urllib.parse import quote

    return f"https://t.me/share/url?url=&text={quote(text)}"


async def _tool_share_pdf_with_contact(db: AsyncSession, user: User, **inputs: Any) -> dict:
    from services.document_service import generate_report

    try:
        cid = UUID(inputs["contact_id"])
    except (KeyError, ValueError):
        return {"error": "contact_id inválido"}
    contact = await db.get(Contact, cid)
    if not contact or contact.user_id != user.id:
        return {"error": "contacto no encontrado"}

    scope = inputs.get("scope", "project")
    title = inputs.get("title", "Resumen RE Expert")
    custom_message = inputs.get("custom_message")
    # 1. Generar PDF
    if scope == "budget":
        # budget no es un scope soportado todavía por document_service: lo mapeamos
        # al "full" para incluir todo.
        scope = "full"
    pdf = await generate_report(db, user, fmt="pdf", scope=scope, title=title)
    if pdf.get("error"):
        return pdf
    pdf_url = pdf["url"]

    # 2. Componer mensaje
    nombre = contact.name.split(" ")[0]
    base_msg = (
        custom_message
        if custom_message
        else f"Hola {nombre}, te paso el {title.lower()} del proyecto:"
    )
    full_text = f"{base_msg}\n{pdf_url}"

    # 3. Deep links
    wa = _wa_link(contact.phone, full_text)
    tg = _tg_share_link(full_text)

    return {
        "ok": True,
        "contact": {"id": str(contact.id), "name": contact.name, "phone": contact.phone},
        "pdf_url": pdf_url,
        "filename": pdf.get("filename"),
        "share_message": full_text,
        "whatsapp_link": wa,
        "telegram_link": tg,
        "preferred_channel": "whatsapp" if wa else "telegram",
        "instructions": "Abrí el link de WhatsApp (o Telegram) — se abre la app con el mensaje listo. Solo tenés que tocar 'Enviar'.",
    }


async def _tool_compose_message_to_contact(db: AsyncSession, user: User, **inputs: Any) -> dict:
    try:
        cid = UUID(inputs["contact_id"])
    except (KeyError, ValueError):
        return {"error": "contact_id inválido"}
    contact = await db.get(Contact, cid)
    if not contact or contact.user_id != user.id:
        return {"error": "contacto no encontrado"}
    msg = (inputs.get("message") or "").strip()
    if not msg:
        return {"error": "mensaje vacío"}
    wa = _wa_link(contact.phone, msg)
    tg = _tg_share_link(msg)
    return {
        "ok": True,
        "contact": {"id": str(contact.id), "name": contact.name, "phone": contact.phone},
        "message": msg,
        "whatsapp_link": wa,
        "telegram_link": tg,
        "preferred_channel": "whatsapp" if wa else "telegram",
    }


# ════════════════════════════════════════════════════════════════════
# Registry tool name → impl.
# ════════════════════════════════════════════════════════════════════
async def _tool_get_news(
    db: AsyncSession, user: User, category: str = "todas", limit: int = 6, **_: Any
) -> dict:
    """Titulares del mismo feed cacheado que usa la vista Noticias (sin red extra
    si el cache está caliente)."""
    from services.news_live import fetch_feed

    try:
        feed = await fetch_feed(category=category or "todas",
                                per_page=min(max(int(limit or 6), 1), 12))
    except Exception as e:  # noqa: BLE001 — SOL degrada con gracia
        logger.warning("get_news falló: %s", e)
        return {"error": "No pude traer las noticias ahora. Probá en un rato."}
    items = [
        {
            "titulo": it.get("title"),
            "fuente": it.get("source"),
            "categoria": it.get("category"),
            "resumen": (it.get("snippet") or "")[:220],
            "url": it.get("url"),
        }
        for it in (feed.get("items") or [])
    ]
    return {"count": len(items), "items": items}


async def _tool_search_chats(
    db: AsyncSession, user: User, query: str = "", limit: int = 5, **_: Any
) -> dict:
    """Búsqueda simple (ILIKE) en las conversaciones del PROPIO usuario."""
    from models.conversation import Conversation
    from models.message import Message

    q = (query or "").strip()
    if len(q) < 2:
        return {"error": "Necesito al menos 2 caracteres para buscar."}
    limit = min(max(int(limit or 5), 1), 10)
    rows = (
        await db.execute(
            select(Message, Conversation.title)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.user_id == user.id,
                Message.content.ilike(f"%{q}%"),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
    ).all()
    items = []
    for msg, conv_title in rows:
        content = msg.content or ""
        idx = content.lower().find(q.lower())
        start = max(0, idx - 120)
        snippet = ("…" if start > 0 else "") + content[start:start + 320] + (
            "…" if len(content) > start + 320 else ""
        )
        items.append({
            "conversacion": conv_title,
            "conversation_id": str(msg.conversation_id),
            "rol": msg.role,
            "fecha": msg.created_at.isoformat() if msg.created_at else None,
            "fragmento": snippet,
        })
    return {"count": len(items), "items": items}


async def _tool_get_opportunities(
    db: AsyncSession, user: User, limit: int = 10, **_: Any
) -> dict:
    from models.opportunity import Opportunity

    rows = list((
        await db.execute(
            select(Opportunity)
            .where(Opportunity.user_id == user.id)
            .order_by(Opportunity.updated_at.desc())
            .limit(min(max(int(limit or 10), 1), 20))
        )
    ).scalars().all())
    items = []
    for o in rows:
        fin = (o.analysis or {}).get("finanzas") or {}
        items.append({
            "id": str(o.id),
            "titulo": o.titulo,
            "zona": o.zona,
            "ciudad": o.ciudad,
            "tipo": o.tipo_inmueble,
            "estado_pipeline": o.estado_pipeline,
            "score": o.score,
            "recomendacion": o.recomendacion,
            "margen_neto_pct": fin.get("margen_neto_pct"),
            "tir_anual_pct": fin.get("tir_anual_pct"),
            "ultimo_analisis": o.last_analyzed_at.isoformat() if o.last_analyzed_at else None,
        })
    return {"count": len(items), "items": items}


TOOL_IMPLS = {
    "query_project_status": _tool_query_project_status,
    "query_payments": _tool_query_payments,
    "query_milestones": _tool_query_milestones,
    "query_materials": _tool_query_materials,
    "register_payment": _tool_register_payment,
    "register_milestone": _tool_register_milestone,
    "register_material_price": _tool_register_material_price,
    "schedule_reminder": _tool_schedule_reminder,
    "list_reminders": _tool_list_reminders,
    "cancel_reminder": _tool_cancel_reminder,
    "generate_pdf_report": _tool_generate_pdf_report,
    "generate_docx_report": _tool_generate_docx_report,
    "send_message_now": _tool_send_message_now,
    "get_user_channels": _tool_get_user_channels,
    "plan_route": _tool_plan_route,
    # Identidad / preferencias
    "get_my_profile": _tool_get_my_profile,
    "set_my_phone": _tool_set_my_phone,
    "set_automation_prefs": _tool_set_automation_prefs,
    # Contactos
    "add_contact": _tool_add_contact,
    "list_contacts": _tool_list_contacts,
    "find_contact": _tool_find_contact,
    "update_contact": _tool_update_contact,
    # Compartir docs / mensajes
    "share_pdf_with_contact": _tool_share_pdf_with_contact,
    "compose_message_to_contact": _tool_compose_message_to_contact,
    # Contexto Jarvis: noticias, chats pasados, deal room
    "get_news": _tool_get_news,
    "search_chats": _tool_search_chats,
    "get_opportunities": _tool_get_opportunities,
    "get_payments_summary": _tool_get_payments_summary,
}


async def run_tool(
    name: str, db: AsyncSession, user: User, inputs: dict[str, Any]
) -> dict:
    """Despacha la ejecución de la tool. Devuelve siempre un dict.

    Las acciones de escritura (WRITE_ACTIONS) NO se ejecutan directo: se validan
    server-side y se devuelve un preview firmado (needs_confirmation). La
    escritura real ocurre cuando el modelo llama confirm_action con ese token.
    """
    from services import agent_confirm as _confirm

    inputs = inputs or {}

    # 1) Confirmación → verificar token y ejecutar la escritura real.
    if name == "confirm_action":
        try:
            action, payload = _confirm.verify_token(inputs.get("confirm_token", ""))
        except _confirm.ValidationError as e:
            return {"error": str(e)}
        impl = TOOL_IMPLS.get(action)
        if impl is None:
            return {"error": f"Acción a confirmar desconocida: {action}"}
        try:
            res = await impl(db, user, **payload)
            if isinstance(res, dict):
                res.setdefault("confirmed", True)
            # Marcar el token como usado SOLO si la escritura salió bien: evita
            # re-ejecutar la misma acción (doble pago) si reaparece en el historial.
            if not (isinstance(res, dict) and res.get("error")):
                _confirm.mark_used(inputs.get("confirm_token", ""))
            return res
        except Exception as e:  # noqa: BLE001
            await db.rollback()  # no envenenar la sesión para las tools siguientes
            logger.exception("confirm_action(%s) falló", action)
            return {"error": f"No se pudo ejecutar {action}: {e}"}

    # 2) Write action sin confirmar → validar y devolver preview firmado.
    if name in _confirm.WRITE_ACTIONS:
        try:
            payload, resumen = _confirm.validate(name, inputs)
        except _confirm.ValidationError as e:
            return {"error": str(e)}
        return {
            "needs_confirmation": True,
            "action": name,
            "resumen": resumen,
            "confirm_token": _confirm.make_token(name, payload),
        }

    # 3) Tools de lectura / bajo riesgo → ejecución directa.
    impl = TOOL_IMPLS.get(name)
    if impl is None:
        return {"error": f"Tool desconocida: {name}"}
    try:
        return await impl(db, user, **inputs)
    except Exception as e:
        await db.rollback()  # una tool que falló no debe envenenar el resto del turno
        logger.exception("Tool %s raised", name)
        return {"error": f"Tool {name} falló: {e}"}
