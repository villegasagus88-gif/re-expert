"""
Email service vía Resend (https://resend.com).

Si RESEND_API_KEY está vacío, send_email NO falla: loguea y devuelve
{"ok": False, "detail": "email_not_configured"} para que el caller degrade con
gracia (p.ej. el flujo de forgot-password responde 200 igual, sin revelar nada).

Para activarlo: crear una API key en https://resend.com/api-keys, verificar el
dominio del remitente, y setear RESEND_API_KEY (+ opcionalmente RESEND_FROM) en
backend/.env. Sin más cambios de código, los emails empiezan a salir.
"""
import logging

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_TIMEOUT_SECONDS = 10


def is_configured() -> bool:
    """True si hay una API key de Resend cargada."""
    return bool(settings.RESEND_API_KEY)


async def send_email(
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
) -> dict:
    """
    Envía un email vía Resend. Devuelve {"ok": bool, ...}.

    Nunca lanza: ante key faltante o error de red devuelve ok=False con detalle,
    así los callers (reset de contraseña, notificaciones) deciden cómo degradar.
    """
    if not settings.RESEND_API_KEY:
        logger.warning(
            "RESEND_API_KEY vacío: email a %s no enviado (subject=%r)", to, subject
        )
        return {"ok": False, "detail": "email_not_configured"}

    payload: dict = {
        "from": settings.RESEND_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                _RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json=payload,
            )
        if resp.status_code >= 400:
            logger.error("Resend error %s: %s", resp.status_code, resp.text[:300])
            return {"ok": False, "detail": f"resend_error_{resp.status_code}"}
        data = resp.json()
        return {"ok": True, "id": data.get("id")}
    except Exception as e:
        logger.exception("Fallo enviando email vía Resend: %s", e)
        return {"ok": False, "detail": "resend_exception"}
