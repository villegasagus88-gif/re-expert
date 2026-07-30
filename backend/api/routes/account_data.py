"""
Derechos del titular de los datos (Ley 25.326): acceso y portabilidad.

El art. 14 da 10 días corridos para responder un pedido de acceso, y hasta ahora
había que armarlo a mano contra la base — un proceso manual que no escala y que
en la práctica se incumple. Este endpoint lo resuelve self-service.

Qué exporta: todo lo que se borraría si el usuario diera de baja la cuenta, o
sea el mapa de FK `ondelete=CASCADE` que cuelga de `profiles`. Formato JSON,
legible por máquina y por persona, que es lo que pide la portabilidad.

Qué NO incluye, a propósito:
  - Los bytes de los planos: pesan hasta 8 MB cada uno y ya se bajan de a uno
    desde Configuración → Almacenamiento. Se exporta el metadato con su id.
  - Hashes de contraseña, secretos de 2FA y códigos de recuperación: son
    credenciales, no datos del titular en el sentido del art. 14, y exportarlos
    sería crear una vía de fuga.

Sin gate de plan: ejercer derechos sobre los propios datos no depende de estar
al día con la suscripción.
"""
import logging
from datetime import UTC, datetime

from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from models.base import get_db
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/account", tags=["account-data"])


def _val(v):
    """Serializa lo que JSON no sabe (fechas, UUID, Decimal)."""
    from decimal import Decimal
    from uuid import UUID as _UUID

    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, _UUID):
        return str(v)
    if isinstance(v, Decimal):
        return float(v)
    if hasattr(v, "isoformat"):        # date
        return v.isoformat()
    return v


def _filas(rows, excluir: set[str] | None = None) -> list[dict]:
    """Filas ORM → lista de dicts, salteando columnas sensibles o pesadas."""
    excluir = excluir or set()
    out = []
    for r in rows:
        d = {}
        for col in r.__table__.columns.keys():
            if col in excluir:
                continue
            d[col] = _val(getattr(r, col, None))
        out.append(d)
    return out


@router.get("/export", summary="Exportar todos mis datos (Ley 25.326, art. 14)")
@limiter.limit("3/hour")
async def export_my_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Descarga un JSON con todos los datos asociados a la cuenta."""
    from models.contact import Contact
    from models.conversation import Conversation
    from models.message import Message
    from models.opportunity import Opportunity
    from models.payment import Payment
    from models.plan_analysis import PlanFile, PlanProject
    from models.project import Project
    from models.reminder import Reminder
    from models.user_channel import UserChannel
    from models.user_location import UserLocation
    from models.workspace import UserProfileGlobal, Workspace, WorkspaceMemory

    uid = user.id

    async def traer(modelo, filtro=None, excluir=None):
        q = select(modelo).where(filtro if filtro is not None else modelo.user_id == uid)
        return _filas((await db.execute(q)).scalars().all(), excluir)

    # Conversaciones + sus mensajes (el contenido del chat es el dato más
    # importante para el titular).
    convs = (await db.execute(
        select(Conversation).where(Conversation.user_id == uid)
    )).scalars().all()
    conv_ids = [c.id for c in convs]
    mensajes = []
    if conv_ids:
        mensajes = _filas((await db.execute(
            select(Message).where(Message.conversation_id.in_(conv_ids))
        )).scalars().all())

    # Workspaces + su memoria
    wss = (await db.execute(select(Workspace).where(Workspace.user_id == uid))).scalars().all()
    ws_ids = [w.id for w in wss]
    memoria_ws = []
    if ws_ids:
        memoria_ws = _filas((await db.execute(
            select(WorkspaceMemory).where(WorkspaceMemory.workspace_id.in_(ws_ids))
        )).scalars().all())

    datos = {
        "_meta": {
            "generado_el": datetime.now(UTC).isoformat(),
            "titular": user.email,
            "norma": "Ley 25.326 de Protección de los Datos Personales (Argentina), art. 14",
            "nota": (
                "Incluye todos los datos asociados a tu cuenta. No se incluyen "
                "credenciales (contraseña, secretos de doble factor) por seguridad, "
                "ni el contenido binario de los planos, que podés descargar uno por "
                "uno desde Configuración → Almacenamiento."
            ),
        },
        "cuenta": {
            "id": str(user.id),
            "email": user.email,
            "nombre": user.full_name,
            "telefono": user.phone,
            "plan": user.plan,
            "doble_factor": user.twofa_method or "desactivado",
            "onboarding_completado": user.onboarding_completed,
            "ultimo_acceso": _val(user.last_login),
            "creada_el": _val(user.created_at),
            "preferencias_automatizacion": user.automation_prefs,
        },
        "conversaciones": _filas(convs),
        "mensajes": mensajes,
        "proyectos_de_obra": await traer(Project),
        "pagos_de_obra": await traer(Payment),
        "proyectos_de_planos": await traer(PlanProject),
        # file_data = los bytes del plano: se excluye a propósito (ver docstring)
        "planos": await traer(PlanFile, excluir={"file_data"}),
        "workspaces": _filas(wss),
        "memoria_de_workspace": memoria_ws,
        "memoria_de_perfil": await traer(UserProfileGlobal),
        "contactos": await traer(Contact),
        "oportunidades": await traer(Opportunity),
        "recordatorios": await traer(Reminder),
        "canales_de_notificacion": await traer(UserChannel),
        "ubicaciones": await traer(UserLocation),
    }

    logger.info("Export de datos generado para user %s", uid)
    fecha = datetime.now(UTC).strftime("%Y-%m-%d")
    return JSONResponse(
        content=datos,
        headers={
            "Content-Disposition": f'attachment; filename="re-expert-mis-datos-{fecha}.json"',
            "Cache-Control": "private, no-store",
        },
    )
