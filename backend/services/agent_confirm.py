"""
Confirmación y validación server-side de las acciones de escritura de SOL.

Patrón "preview + confirm" (elegido por el usuario, sin tabla nueva):

  1. El modelo llama una tool de escritura (ej. register_payment).
  2. run_tool NO ejecuta: valida y normaliza los inputs SERVER-SIDE (montos,
     fechas, enums, teléfono), arma un resumen humano y firma el payload con
     HMAC. Devuelve {needs_confirmation, action, resumen, confirm_token}.
  3. El modelo le muestra el resumen al usuario y espera un "sí" EXPLÍCITO.
  4. En un turno POSTERIOR, el modelo llama confirm_action(confirm_token).
  5. run_tool verifica el HMAC (integridad + procedencia) y recién ahí ejecuta
     la escritura con el payload firmado (que el modelo NO pudo alterar).

Garantías server-side (no dependen del prompt):
  - Validación de valores: montos > 0 y con tope, enums, fechas, teléfono.
    Un typo del modelo ($100.000.000) se rechaza ANTES del preview.
  - Integridad: el payload ejecutado es EXACTAMENTE el validado (HMAC), el
    modelo no puede cambiar el monto entre el preview y la confirmación.
  - Human-in-the-loop: run_agent rechaza un confirm_action cuyo token se
    emitió en el MISMO turno (ver agent_service) → obliga a que la
    confirmación venga tras un nuevo mensaje del usuario.

Lo único que queda fuera del enforcement server-side puro es que el modelo
respete "esperá el sí" en el texto; el corte por turno lo cubre en la
práctica y el system prompt lo refuerza.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import date as Date
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from config.settings import settings

# Tools de escritura que exigen confirmación de dos pasos. Las de bajo riesgo
# (set_my_phone, set_automation_prefs, send_message_now al propio usuario,
# share/compose que ya son human-in-the-loop) quedan fuera a propósito.
WRITE_ACTIONS: frozenset[str] = frozenset({
    "register_payment",
    "register_milestone",
    "register_material_price",
    "schedule_reminder",
    "add_contact",
    "update_contact",
})

# Topes de sanidad: cortan typos del modelo antes de tocar la DB.
_MONTO_MAX = Decimal("9999999999")  # 10 díg. — acorde a Numeric(12,2)
_PAY_ESTADOS = {"pagado", "pendiente", "cancelado"}
_MS_ESTADOS = {"planned", "in_progress", "done", "delayed"}
_REMINDER_CHANNELS = {"in_app", "telegram"}  # los únicos que HOY entregan
_CURRENCIES = {"ARS", "USD"}


class ValidationError(Exception):
    """Input inválido; el mensaje va al modelo como {'error': ...}."""


# ── Validadores por acción: (inputs) -> (payload_normalizado, resumen) ──
# El payload normalizado usa tipos serializables (str/float/…) porque viaja
# firmado y se re-hidrata en el executor.

def _money(v: Any, campo: str) -> float:
    try:
        d = Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValidationError(f"{campo} no es un número válido: {v!r}") from e
    if d <= 0:
        raise ValidationError(f"{campo} tiene que ser mayor a 0 (vino {d}).")
    if d > _MONTO_MAX:
        raise ValidationError(
            f"{campo} = {d} supera el máximo permitido. Si es correcto, cargalo manualmente."
        )
    return float(d)


def _iso_date(v: Any, campo: str) -> str:
    try:
        return Date.fromisoformat(str(v)).isoformat()
    except (ValueError, TypeError) as e:
        raise ValidationError(f"{campo} no es una fecha válida (YYYY-MM-DD): {v!r}") from e


def _str(inputs: dict, key: str, *, required: bool = False, maxlen: int = 500) -> str | None:
    v = inputs.get(key)
    if v is None or (isinstance(v, str) and not v.strip()):
        if required:
            raise ValidationError(f"Falta el campo obligatorio '{key}'.")
        return None
    return str(v).strip()[:maxlen]


def _v_register_payment(inputs: dict) -> tuple[dict, str]:
    concepto = _str(inputs, "concepto", required=True)
    monto = _money(inputs.get("monto"), "monto")
    fecha = _iso_date(inputs.get("fecha"), "fecha")
    estado = _str(inputs, "estado", required=True)
    if estado not in _PAY_ESTADOS:
        raise ValidationError(f"estado inválido: {estado}. Debe ser {sorted(_PAY_ESTADOS)}.")
    payload = {
        "concepto": concepto, "monto": monto, "fecha": fecha, "estado": estado,
        "proveedor": _str(inputs, "proveedor", maxlen=255),
        "categoria": _str(inputs, "categoria", maxlen=100),
        "notas": _str(inputs, "notas", maxlen=2000),
    }
    prov = f" a {payload['proveedor']}" if payload["proveedor"] else ""
    resumen = (f"Registrar pago **{estado}** de **${monto:,.2f}**{prov} — "
               f"«{concepto}», fecha {fecha}.")
    return payload, resumen


def _v_register_milestone(inputs: dict) -> tuple[dict, str]:
    name = _str(inputs, "name", required=True, maxlen=255)
    estado = _str(inputs, "status") or "planned"
    if estado not in _MS_ESTADOS:
        raise ValidationError(f"status inválido: {estado}. Debe ser {sorted(_MS_ESTADOS)}.")
    due = _iso_date(inputs["due_date"], "due_date") if inputs.get("due_date") else None
    payload = {"name": name, "description": _str(inputs, "description", maxlen=2000),
               "status": estado, "due_date": due}
    resumen = f"Registrar hito **«{name}»** (estado {estado}{', vence ' + due if due else ''})."
    return payload, resumen


def _v_register_material_price(inputs: dict) -> tuple[dict, str]:
    name = _str(inputs, "name", required=True, maxlen=255)
    unit = _str(inputs, "unit", required=True, maxlen=20)
    price = _money(inputs.get("unit_price"), "unit_price")
    currency = (_str(inputs, "currency") or "ARS").upper()
    if currency not in _CURRENCIES:
        raise ValidationError(f"currency inválida: {currency}. Debe ser {sorted(_CURRENCIES)}.")
    quoted = _iso_date(inputs["quoted_at"], "quoted_at") if inputs.get("quoted_at") else None
    payload = {"name": name, "unit": unit, "unit_price": price, "currency": currency,
               "supplier": _str(inputs, "supplier", maxlen=255), "quoted_at": quoted,
               "notes": _str(inputs, "notes", maxlen=2000)}
    resumen = f"Registrar precio de **{name}**: {currency} {price:,.2f} por {unit}."
    return payload, resumen


def _v_schedule_reminder(inputs: dict) -> tuple[dict, str]:
    title = _str(inputs, "title", required=True, maxlen=300)
    raw = inputs.get("due_at")
    try:
        due = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
        raise ValidationError(f"due_at no es una fecha-hora ISO válida: {raw!r}") from e
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    if due <= datetime.now(timezone.utc):
        raise ValidationError("due_at tiene que estar en el futuro.")
    channel = _str(inputs, "channel") or "in_app"
    if channel not in _REMINDER_CHANNELS:
        raise ValidationError(
            f"El canal '{channel}' todavía no está disponible para recordatorios. "
            f"Usá uno de: {sorted(_REMINDER_CHANNELS)}."
        )
    payload = {"title": title, "body": _str(inputs, "body", maxlen=4000),
               "due_at": due.isoformat(), "channel": channel}
    cuando = due.astimezone().strftime("%d/%m/%Y %H:%M")
    resumen = f"Agendar recordatorio **«{title}»** para el **{cuando}** (canal {channel})."
    return payload, resumen


def _norm_phone(v: str | None) -> str | None:
    """Normaliza a formato tipo +54… — solo dígitos y un '+' inicial opcional."""
    if not v:
        return None
    s = "".join(ch for ch in str(v) if ch.isdigit() or ch == "+")
    s = "+" + s.replace("+", "") if s.startswith("+") else s.replace("+", "")
    digits = s.lstrip("+")
    if not (8 <= len(digits) <= 15):
        raise ValidationError(
            f"El teléfono '{v}' no parece válido (esperado 8-15 dígitos, formato internacional)."
        )
    return s


def _v_add_contact(inputs: dict) -> tuple[dict, str]:
    name = _str(inputs, "name", required=True, maxlen=255)
    phone = _norm_phone(_str(inputs, "phone"))
    payload = {"name": name, "phone": phone, "email": _str(inputs, "email", maxlen=255),
               "role": _str(inputs, "role", maxlen=100), "notes": _str(inputs, "notes", maxlen=2000)}
    resumen = f"Agregar contacto **{name}**{' (' + phone + ')' if phone else ''} a tu agenda."
    return payload, resumen


def _v_update_contact(inputs: dict) -> tuple[dict, str]:
    cid = _str(inputs, "contact_id", required=True, maxlen=64)
    payload: dict[str, Any] = {"contact_id": cid}
    if inputs.get("phone") is not None:
        payload["phone"] = _norm_phone(_str(inputs, "phone"))
    for k, ml in (("name", 255), ("email", 255), ("role", 100), ("notes", 2000)):
        if inputs.get(k) is not None:
            payload[k] = _str(inputs, k, maxlen=ml)
    cambios = ", ".join(k for k in payload if k != "contact_id") or "(nada)"
    resumen = f"Actualizar contacto {cid[:8]}… — campos: {cambios}."
    return payload, resumen


_VALIDATORS = {
    "register_payment": _v_register_payment,
    "register_milestone": _v_register_milestone,
    "register_material_price": _v_register_material_price,
    "schedule_reminder": _v_schedule_reminder,
    "add_contact": _v_add_contact,
    "update_contact": _v_update_contact,
}


def validate(action: str, inputs: dict) -> tuple[dict, str]:
    """Valida+normaliza los inputs de una write action. Raises ValidationError."""
    fn = _VALIDATORS.get(action)
    if fn is None:
        raise ValidationError(f"Acción desconocida: {action}")
    return fn(inputs or {})


# ── Token HMAC: firma el (action, payload) para garantizar integridad ──

def _secret() -> bytes:
    return settings.JWT_SECRET.encode("utf-8")


# TTL: un token viejo (que quedó en el historial de un turno anterior) no puede
# reusarse para re-ejecutar la acción. Ventana holgada para que el usuario
# confirme con calma, pero acotada.
TOKEN_TTL_SECONDS = 1800  # 30 min

# Anti-reuso dentro del proceso: un token ya confirmado no se vuelve a ejecutar
# (cubre la reconfirmación en la misma sesión; el TTL cubre el resto). Acotado.
_USED_TOKENS: set[str] = set()
_USED_ORDER: list[str] = []
_USED_MAX = 5000


def make_token(action: str, payload: dict, *, now: int | None = None) -> str:
    """Devuelve '<b64(body)>.<hexsig>' donde body = {action, payload, ts}."""
    ts = now if now is not None else int(__import__("time").time())
    body = json.dumps({"a": action, "p": payload, "t": ts}, ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(body).decode("ascii")
    sig = hmac.new(_secret(), b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def verify_token(token: str, *, now: int | None = None) -> tuple[str, dict]:
    """Valida firma + TTL + no-reuso y devuelve (action, payload).
    Raises ValidationError. NO marca el token como usado (eso lo hace
    mark_used tras ejecutar OK)."""
    try:
        b64, sig = str(token).split(".", 1)
    except (ValueError, AttributeError) as e:
        raise ValidationError("Token de confirmación con formato inválido.") from e
    expected = hmac.new(_secret(), b64.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValidationError("Token de confirmación inválido o adulterado.")
    try:
        data = json.loads(base64.urlsafe_b64decode(b64.encode("ascii")).decode("utf-8"))
    except (ValueError, TypeError) as e:
        raise ValidationError("Token de confirmación corrupto.") from e
    ts = int(data.get("t", 0))
    cur = now if now is not None else int(__import__("time").time())
    if cur - ts > TOKEN_TTL_SECONDS:
        raise ValidationError(
            "La confirmación venció (pasaron más de 30 min). Pedime la acción de nuevo."
        )
    if token in _USED_TOKENS:
        raise ValidationError("Esa acción ya se ejecutó; no la repito.")
    return data["a"], data["p"]


def mark_used(token: str) -> None:
    """Marca un token como consumido tras ejecutar la acción OK."""
    _USED_TOKENS.add(token)
    _USED_ORDER.append(token)
    if len(_USED_ORDER) > _USED_MAX:
        _USED_TOKENS.discard(_USED_ORDER.pop(0))
