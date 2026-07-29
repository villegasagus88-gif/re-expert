"""
Tests de Cuenta / seguridad (/api/auth/account/*, /api/auth/2fa/*, email-change).

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_account_security.py --import-mode=importlib -q

Capas:
  - TOTP contra los vectores oficiales del RFC 6238 (SHA-1).
  - HTTP: auth obligatoria; /2fa/verify y /login abiertos (pre-login).
  - Gate: NINGÚN endpoint de cuenta va detrás del gate de plan (derechos sobre
    los propios datos), verificado sobre el grafo de dependencias real.
  - Login: challenge 2FA solo cambia la respuesta si el usuario activó 2FA.
  - Schemas: validación de teléfono y códigos.
"""
import pytest
from api.schemas.auth import (
    CodeRequest,
    DeleteAccountRequest,
    EmailChangeRequest,
    PhoneRequest,
    TwoFAVerifyRequest,
)
from fastapi.testclient import TestClient
from main import app
from pydantic import ValidationError
from services.jwt_service import create_2fa_challenge, decode_2fa_challenge
from services.totp_service import generate_secret, otpauth_uri, totp_at, verify_totp


# ───────────────────────────────── TOTP: vectores RFC 6238 ──

# Secret del RFC (ASCII "12345678901234567890" en base32) y códigos esperados
# para SHA-1. El RFC publica 8 dígitos; nosotros usamos los últimos 6 (así
# derivan todas las apps: el truncamiento es el mismo módulo 10^6).
_RFC_SECRET_B32 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
_RFC_VECTORES = [
    (59, "94287082"),
    (1111111109, "07081804"),
    (1111111111, "14050471"),
    (1234567890, "89005924"),
    (2000000000, "69279037"),
    (20000000000, "65353130"),
]


@pytest.mark.parametrize("t,codigo8", _RFC_VECTORES)
def test_totp_vectores_oficiales_rfc6238(t, codigo8):
    assert totp_at(_RFC_SECRET_B32, t) == codigo8[-6:]


def test_totp_verify_acepta_ventana_de_un_periodo():
    """El código del período anterior/siguiente vale (relojes desincronizados)."""
    t = 1111111111
    codigo = totp_at(_RFC_SECRET_B32, t)
    assert verify_totp(_RFC_SECRET_B32, codigo, at=t)
    assert verify_totp(_RFC_SECRET_B32, codigo, at=t + 30)      # 1 período después
    assert verify_totp(_RFC_SECRET_B32, codigo, at=t - 30)      # 1 período antes
    assert not verify_totp(_RFC_SECRET_B32, codigo, at=t + 61)  # 2+ períodos: no


@pytest.mark.parametrize("malo", ["", "12345", "1234567", "abcdef", "12 34 5", None, "000000\n"])
def test_totp_verify_rechaza_basura_sin_explotar(malo):
    assert verify_totp(_RFC_SECRET_B32, malo, at=59) is False


def test_totp_secret_nuevo_es_base32_y_unico():
    a, b = generate_secret(), generate_secret()
    assert a != b and len(a) == 32
    import base64
    base64.b32decode(a)   # no explota → base32 válido


def test_otpauth_uri_formato_estandar():
    uri = otpauth_uri("ABC234DEF345", "mati@re.app")
    assert uri.startswith("otpauth://totp/RE%20Expert%3Amati%40re.app?")
    assert "secret=ABC234DEF345" in uri
    assert "issuer=RE%20Expert" in uri and "digits=6" in uri and "period=30" in uri


# ───────────────────────────────── challenge de login ──

def test_challenge_2fa_va_y_vuelve():
    from uuid import uuid4
    uid = uuid4()
    tok = create_2fa_challenge(uid, token_version=3)
    payload = decode_2fa_challenge(tok)
    assert payload and payload["sub"] == str(uid) and payload["tv"] == 3


def test_un_access_token_no_sirve_como_challenge():
    """type='access' ≠ type='2fa': un token robado no saltea el segundo factor."""
    from uuid import uuid4
    from services.jwt_service import create_access_token
    assert decode_2fa_challenge(create_access_token(uuid4())) is None


def test_un_challenge_no_sirve_como_access_token():
    """El camino inverso tampoco: el challenge no autentica requests."""
    from uuid import uuid4
    tok = create_2fa_challenge(uuid4())
    r = TestClient(app).get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


# ───────────────────────────────── HTTP: auth obligatoria ──

@pytest.mark.parametrize("metodo,path,kw", [
    ("get", "/api/auth/account/security", {}),
    ("post", "/api/auth/email-change/request",
     {"json": {"new_email": "x@y.com", "password": "a"}}),
    ("post", "/api/auth/email-change/confirm", {"json": {"code": "123456"}}),
    ("put", "/api/auth/phone", {"json": {"phone": "+54 9 261 5551234"}}),
    ("post", "/api/auth/2fa/totp/start", {"json": {"password": "a"}}),
    ("post", "/api/auth/2fa/totp/confirm", {"json": {"code": "123456"}}),
    ("post", "/api/auth/2fa/email/start", {"json": {"password": "a"}}),
    ("post", "/api/auth/2fa/email/send-code", {}),
    ("post", "/api/auth/2fa/email/confirm", {"json": {"code": "123456"}}),
    ("post", "/api/auth/2fa/disable", {"json": {"password": "a", "code": "123456"}}),
    ("post", "/api/auth/account/delete", {"json": {"password": "a"}}),
])
def test_todo_exige_sesion(metodo, path, kw):
    r = getattr(TestClient(app), metodo)(path, **kw)
    assert r.status_code == 401, f"{metodo.upper()} {path} devolvió {r.status_code}"


def test_2fa_verify_es_publico_pero_rechaza_challenge_invalido():
    r = TestClient(app).post(
        "/api/auth/2fa/verify",
        json={"challenge_token": "x" * 20, "code": "123456"},
    )
    assert r.status_code == 401   # público (sin token) pero challenge inválido


# ───────────────────────────────── gate de plan: NO va acá ──

def _deps(path: str, metodo: str) -> set[str]:
    for r in app.routes:
        if getattr(r, "path", None) == path and metodo in getattr(r, "methods", set()):
            return {d.call.__name__ for d in r.dependant.dependencies}
    raise AssertionError(f"ruta no encontrada: {metodo} {path}")


@pytest.mark.parametrize("path,metodo", [
    ("/api/auth/account/security", "GET"),
    ("/api/auth/account/delete", "POST"),
    ("/api/auth/2fa/totp/start", "POST"),
    ("/api/auth/email-change/request", "POST"),
    ("/api/auth/phone", "PUT"),
])
def test_cuenta_sin_gate_de_plan(path, metodo):
    """Un usuario con trial vencido TIENE que poder gestionar su cuenta y
    pedir la baja (la suscripción activa se valida en el servicio, no acá)."""
    d = _deps(path, metodo)
    assert "require_access" not in d, f"{metodo} {path} quedó detrás del paywall"
    assert "get_current_user" in d, f"{metodo} {path} debe exigir sesión"


# ───────────────────────────────── schemas ──

def test_phone_normaliza_y_valida():
    assert PhoneRequest(phone="  +54 9 261 555-1234 ").phone == "+54 9 261 555-1234"
    assert PhoneRequest(phone="   ").phone is None
    assert PhoneRequest(phone=None).phone is None
    with pytest.raises(ValidationError):
        PhoneRequest(phone="no-es-un-telefono")
    with pytest.raises(ValidationError):
        PhoneRequest(phone="+54; DROP TABLE--")


def test_email_change_valida_el_email():
    with pytest.raises(ValidationError):
        EmailChangeRequest(new_email="no-es-email", password="x")
    ok = EmailChangeRequest(new_email="nuevo@re.app", password="x")
    assert ok.new_email == "nuevo@re.app"


def test_code_request_acota_largo():
    with pytest.raises(ValidationError):
        CodeRequest(code="123")                  # muy corto
    with pytest.raises(ValidationError):
        CodeRequest(code="1" * 17)               # muy largo
    assert CodeRequest(code="AB12-CD34").code == "AB12-CD34"   # recovery code entra


def test_delete_request_el_codigo_es_opcional():
    assert DeleteAccountRequest(password="x").code is None
    assert DeleteAccountRequest(password="x", code="123456").code == "123456"


def test_verify_request_exige_challenge():
    with pytest.raises(ValidationError):
        TwoFAVerifyRequest(challenge_token="corto", code="123456")


# ───────────────────────────────── login: contrato intacto sin 2FA ──

def test_login_sin_response_model_para_soportar_el_desafio():
    """/login no puede tener response_model=AuthResponse: la respuesta de
    desafío 2FA ({twofa_required,...}) no trae tokens y un response_model con
    campos obligatorios la rompería con 500. Si alguien lo re-agrega, esto falla."""
    for r in app.routes:
        if getattr(r, "path", None) == "/api/auth/login" and "POST" in getattr(r, "methods", set()):
            assert r.response_model is None, (
                "/login recuperó un response_model estricto: los logins con 2FA van a dar 500"
            )
            return
    raise AssertionError("no encontré POST /api/auth/login")


def test_la_rama_2fa_del_login_no_toca_el_camino_comun():
    """La rama nueva de login_user está guardada por twofa_method: sin 2FA el
    flujo es el histórico (tokens directos y cancelación de baja pendiente)."""
    import inspect
    from services.auth_service import login_user
    src = inspect.getsource(login_user)
    assert 'getattr(user, "twofa_method", None)' in src
    assert "deletion_requested_at" in src           # el login cancela la baja


# ───────────────────────────────── segundo factor: replay y recovery ──

class _FakeUser:
    """Solo los atributos que _verify_second_factor toca. Sin DB."""

    def __init__(self, **kw):
        self.id = "11111111-1111-1111-1111-111111111111"
        self.twofa_method = kw.get("twofa_method")
        self.twofa_secret = kw.get("twofa_secret")
        self.twofa_recovery = kw.get("twofa_recovery", [])
        self.twofa_code_hash = None
        self.twofa_code_expires_at = None
        self.twofa_code_attempts = 0


def test_totp_no_se_puede_reusar_el_mismo_codigo():
    """Anti-replay: el código que ya entró no vale una segunda vez."""
    import time
    from services.account_security_service import _verify_second_factor
    u = _FakeUser(twofa_method="totp", twofa_secret=_RFC_SECRET_B32)
    codigo = totp_at(_RFC_SECRET_B32, int(time.time()))
    assert _verify_second_factor(u, codigo) is True     # primera vez: entra
    assert _verify_second_factor(u, codigo) is False    # replay: NO
    assert u.twofa_code_hash is not None                # quedó registrado


def test_recovery_code_es_de_un_solo_uso():
    import hashlib
    from services.account_security_service import _verify_second_factor
    h = hashlib.sha256(b"AB12CD34").hexdigest()
    u = _FakeUser(twofa_method="totp", twofa_secret=_RFC_SECRET_B32, twofa_recovery=[h])
    assert _verify_second_factor(u, "ab12-cd34") is True    # case/guiones tolerados
    assert u.twofa_recovery == []                           # consumido
    assert _verify_second_factor(u, "ab12-cd34") is False   # segunda vez: NO


def test_sin_2fa_activo_nada_pasa():
    from services.account_security_service import _verify_second_factor
    u = _FakeUser(twofa_method=None)
    assert _verify_second_factor(u, "123456") is False


def test_el_codigo_se_quema_tras_N_intentos_fallidos():
    """Throttling POR CUENTA: el rate limit de la ruta es por IP y no frena un
    ataque distribuido recorriendo los 10^6 códigos dentro de la ventana."""
    import hashlib
    from datetime import UTC, datetime, timedelta

    from services.account_security_service import MAX_CODE_ATTEMPTS, _verify_second_factor
    u = _FakeUser(twofa_method="email")
    u.twofa_code_hash = hashlib.sha256(b"424242").hexdigest()
    u.twofa_code_expires_at = datetime.now(UTC) + timedelta(minutes=10)

    for _ in range(MAX_CODE_ATTEMPTS):
        assert _verify_second_factor(u, "000000") is False
    assert u.twofa_code_hash is None, "el código debería haberse quemado"
    # Ni siquiera el código CORRECTO sirve ya: hay que pedir uno nuevo.
    assert _verify_second_factor(u, "424242") is False


# ───────────────────────────────── enrolar 2FA exige contraseña ──

def test_enrolar_2fa_pide_contrasena():
    """Sin esto, una sesión robada activaba 2FA en la cuenta ajena y dejaba al
    dueño afuera PARA SIEMPRE: el reset de contraseña no limpia el 2FA, así que
    ni recuperando la clave podía volver a entrar."""
    import inspect
    from services.account_security_service import email_2fa_start, totp_start
    for fn in (totp_start, email_2fa_start):
        assert "password" in inspect.signature(fn).parameters, f"{fn.__name__} sin password"
        assert "_require_password" in inspect.getsource(fn), f"{fn.__name__} no valida la contraseña"


def test_totp_confirm_no_puede_pisar_un_2fa_activo():
    """Un pending_secret viejo no puede cambiar el método ni regenerar los
    recovery codes sin pasar por disable_2fa (que exige contraseña + código)."""
    import inspect
    from services.account_security_service import totp_confirm
    assert "if user.twofa_method:" in inspect.getsource(totp_confirm)


def test_cambio_de_email_exige_segundo_factor_si_hay_2fa():
    """Cambiar el email redirige los códigos de login: sin este control, sesión
    robada + contraseña alcanzaban para neutralizar el 2FA por email."""
    import inspect
    from services.account_security_service import request_email_change
    src = inspect.getsource(request_email_change)
    assert "user.twofa_method" in src and "_verify_second_factor" in src


def test_los_emails_escapan_el_nombre_del_usuario():
    """full_name es texto libre: sin escapar, alguien pone un <a> en su nombre y
    pide un cambio de email hacia la casilla de una víctima → phishing enviado
    desde nuestro remitente legítimo."""
    from services.account_security_service import _email_code_html
    html_out = _email_code_html('<a href="https://evil.example">Hacé click</a>', "123456", "motivo")
    assert "<a href" not in html_out
    assert "&lt;a href" in html_out


def test_la_purga_usa_la_misma_constante_que_le_prometemos_al_usuario():
    """Dos fuentes de verdad = borrar cuentas antes de la fecha prometida."""
    import inspect
    from services.scheduler_service import _run_daily_cleanup
    src = inspect.getsource(_run_daily_cleanup)
    assert "DELETION_GRACE_DAYS" in src
    assert "timedelta(days=30)" not in src.split("deletion_requested_at")[0][-300:]


# ───────────────────────────────── purga: el cleanup la incluye ──

def test_cleanup_diario_incluye_la_purga_de_cuentas():
    """El job existe y respeta el doble cinturón (plan != 'pro')."""
    import inspect
    from services.scheduler_service import _run_daily_cleanup
    src = inspect.getsource(_run_daily_cleanup)
    assert "deletion_requested_at" in src, "la purga no está en el cleanup diario"
    assert 'User.plan != "pro"' in src, "falta el cinturón anti-purga de suscriptos"
