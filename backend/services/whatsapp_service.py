"""
WhatsApp service vía Twilio (https://www.twilio.com/whatsapp).

Si las credenciales de Twilio no están configuradas, send_whatsapp NO falla:
devuelve {"ok": False, "detail": "whatsapp_not_configured"} para que el caller
(notification_dispatcher) degrade a in_app.

Para activarlo: setear TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_FROM
(ej. "whatsapp:+14155238886") en backend/.env.
"""
import logging

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 15


def is_configured() -> bool:
    return bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_WHATSAPP_FROM
    )


def _wa_addr(phone: str) -> str:
    """Normaliza un número al formato 'whatsapp:+54...' que espera Twilio."""
    p = (phone or "").strip()
    return p if p.startswith("whatsapp:") else f"whatsapp:{p}"


async def send_whatsapp(to_phone: str, body: str) -> dict:
    """
    Manda un WhatsApp vía Twilio. Devuelve {"ok": bool, ...}. Nunca lanza:
    ante credenciales faltantes o error de red devuelve ok=False con detalle.
    """
    if not is_configured():
        logger.warning("Twilio no configurado: WhatsApp a %s no enviado", to_phone)
        return {"ok": False, "detail": "whatsapp_not_configured"}
    if not to_phone:
        return {"ok": False, "detail": "no_destination_phone"}

    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    )
    data = {
        "From": _wa_addr(settings.TWILIO_WHATSAPP_FROM),
        "To": _wa_addr(to_phone),
        "Body": body,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as cli:
            r = await cli.post(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                data=data,
            )
        if r.status_code >= 400:
            logger.error("Twilio WhatsApp error %s: %s", r.status_code, r.text[:300])
            return {"ok": False, "detail": f"twilio_error_{r.status_code}"}
        payload = r.json()
        return {"ok": True, "sid": payload.get("sid")}
    except Exception as e:
        logger.exception("Twilio WhatsApp exception: %s", e)
        return {"ok": False, "detail": "twilio_exception"}
