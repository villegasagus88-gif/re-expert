"""
Tests de facturación: tarjetas guardadas y cobros rechazados.

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_billing_cards.py --import-mode=importlib -q

Lo más importante que se verifica acá es que **el número de tarjeta no pueda
entrar al backend**. El resto (auth, roles, gracia) es lógica de negocio.
"""
import pytest
from api.schemas.billing import CardTokenRequest
from fastapi.testclient import TestClient
from main import app
from pydantic import ValidationError

_UUID = "11111111-1111-1111-1111-111111111111"


# ═══ Lo que sostiene la declaración de los Términos ═══════════════════════


def test_el_modelo_no_tiene_ninguna_columna_de_datos_de_tarjeta():
    """Los T&C dicen que no recibimos ni almacenamos datos de tarjeta. Si alguien
    agrega una columna con el número, esa declaración pasa a ser falsa y el
    proyecto entra en alcance PCI-DSS completo."""
    from models.payment_method import PaymentMethod

    cols = set(PaymentMethod.__table__.columns.keys())
    prohibidas = {
        "card_number", "number", "pan", "cvv", "cvc", "security_code",
        "expiration_date", "cardholder_number",
    }
    assert not (cols & prohibidas), f"columnas con datos de tarjeta: {cols & prohibidas}"
    # Lo que SÍ debe estar: identificadores de la bóveda y datos de display.
    assert {"mp_customer_id", "mp_card_id", "brand", "last_four"} <= cols


def test_el_schema_de_entrada_solo_acepta_un_token():
    """El único dato de tarjeta que entra es el token que generó el SDK de MP."""
    campos = set(CardTokenRequest.model_fields.keys())
    assert campos == {"card_token"}, f"el schema acepta de más: {campos}"


def test_el_schema_rechaza_algo_que_parezca_un_numero_de_tarjeta():
    with pytest.raises(ValidationError):
        CardTokenRequest(card_token="4509")          # muy corto
    with pytest.raises(ValidationError):
        CardTokenRequest(card_token="x" * 129)       # muy largo


def test_no_se_loggea_el_token():
    """Un token en los logs del hosting es un dato de pago fuera de nuestro control."""
    import inspect

    from services import cards_service

    src = inspect.getsource(cards_service)
    for linea in src.splitlines():
        if "logger." in linea:
            assert "card_token" not in linea and "token" not in linea.split("logger.")[1], (
                f"el token se estaría loggeando: {linea.strip()}"
            )


# ═══ HTTP: auth ═══════════════════════════════════════════════════════════


@pytest.mark.parametrize("metodo,path,kw", [
    ("get", "/api/billing/cards", {}),
    ("post", "/api/billing/cards", {"json": {"card_token": "tok_de_prueba_123"}}),
    ("delete", f"/api/billing/cards/{_UUID}", {}),
    ("patch", f"/api/billing/cards/{_UUID}/principal", {}),
    ("post", "/api/billing/cards/reintentar", {"json": {"card_token": "tok_de_prueba_123"}}),
])
def test_todo_exige_sesion(metodo, path, kw):
    r = getattr(TestClient(app), metodo)(path, **kw)
    assert r.status_code == 401, f"{metodo.upper()} {path} devolvió {r.status_code}"


def test_las_tarjetas_no_estan_detras_del_gate_de_plan():
    """Alguien con el plan vencido tiene que poder cargar una tarjeta — es
    justamente lo que necesita para volver a estar al día."""
    for r in app.routes:
        if getattr(r, "path", "").startswith("/api/billing/cards"):
            deps = {d.call.__name__ for d in r.dependant.dependencies}
            assert "require_access" not in deps, f"{r.path} quedó tras el paywall"
            assert "get_current_user" in deps


# ═══ Roles: principal y respaldo ══════════════════════════════════════════


class _Tarjeta:
    def __init__(self, id_, role):
        self.id, self.role = id_, role


def test_la_primera_tarjeta_es_principal_y_la_segunda_respaldo():
    import inspect

    from services.cards_service import agregar

    src = inspect.getsource(agregar)
    assert "ROL_PRINCIPAL if not actuales else ROL_RESPALDO" in src


def test_hay_tope_de_dos_tarjetas():
    from services.cards_service import MAX_TARJETAS

    assert MAX_TARJETAS == 2


def test_no_se_puede_quedar_sin_principal():
    """Si se borra la principal, la de respaldo asciende. Nunca quedar sin
    tarjeta de cobro con la suscripción viva."""
    import inspect

    from services.cards_service import quitar

    src = inspect.getsource(quitar)
    assert "era_principal" in src and "ROL_PRINCIPAL" in src


def test_no_se_borra_la_unica_tarjeta_con_suscripcion_activa():
    import inspect

    from services.cards_service import quitar

    src = inspect.getsource(quitar)
    assert 'user.plan == "pro"' in src and "409" in src


# ═══ Cobros rechazados ════════════════════════════════════════════════════


def test_los_motivos_de_rechazo_se_explican_en_criollo():
    from services.billing_issues import explicar

    assert explicar("cc_rejected_insufficient_amount") == "La tarjeta no tenía fondos suficientes."
    assert explicar("cc_rejected_expired_card") == "La tarjeta está vencida."
    # Un motivo desconocido no puede romper ni filtrar el código interno de MP.
    generico = explicar("cc_rejected_algo_nuevo_de_mp")
    assert "cc_rejected" not in generico and len(generico) > 10
    assert explicar(None) == generico


def test_hay_periodo_de_gracia():
    """Cortar el acceso en el primer rechazo castiga a un cliente que quiere pagar."""
    from services.billing_issues import DIAS_DE_GRACIA

    assert DIAS_DE_GRACIA >= 3


def test_un_cobro_rechazado_no_cambia_el_plan_del_usuario():
    """El acceso lo gobierna subscription_preapproval, no un rechazo puntual."""
    import inspect

    from services.mercadopago_service import _apply_recurring_payment

    src = inspect.getsource(_apply_recurring_payment)
    assert "abrir_issue" in src
    assert "plan =" not in src and "_apply_status_to_user" not in src, (
        "el rechazo de un cobro no debe tocar el plan"
    )


def test_un_cobro_aprobado_cierra_los_pendientes():
    import inspect

    from services.mercadopago_service import _apply_recurring_payment

    src = inspect.getsource(_apply_recurring_payment)
    assert "cerrar_issues" in src and 'estado == "approved"' in src


def test_abrir_issue_es_idempotente():
    """MP reintenta los webhooks: no puede abrirse un issue por cada reintento."""
    import inspect

    from services.billing_issues import abrir_issue

    src = inspect.getsource(abrir_issue)
    assert "existente" in src and "return" in src


def test_el_reintento_no_cierra_el_issue_por_su_cuenta():
    """Recién se cierra cuando MP confirma el cobro aprobado. Decir 'resuelto'
    antes sería mentirle al usuario."""
    import inspect

    from services.billing_issues import resolver_con_respaldo

    src = inspect.getsource(resolver_con_respaldo)
    assert "cerrar_issues" not in src


# ═══ El webhook existente no se rompió ════════════════════════════════════


def test_el_dispatch_del_webhook_sigue_usando_match_exacto():
    """Un match por substring mandaría subscription_authorized_payment al
    handler de pagos de curso. El comentario del código lo advierte."""
    import inspect

    from services.mercadopago_service import handle_webhook

    src = inspect.getsource(handle_webhook)
    assert 'if t == "payment":' in src
    assert 't in ("preapproval", "subscription_preapproval")' in src
    assert 't == "subscription_authorized_payment"' in src


def test_el_webhook_sigue_sin_auth_jwt_pero_valida_firma():
    for r in app.routes:
        if getattr(r, "path", None) == "/api/billing/mp/webhook":
            deps = {d.call.__name__ for d in r.dependant.dependencies}
            assert "get_current_user" not in deps, "MP pega sin JWT"
            return
    raise AssertionError("no existe el webhook de MP")


# ═══ Sin credenciales de MP, todo es inerte ═══════════════════════════════


def test_sin_mp_configurado_el_modulo_no_rompe():
    from services.cards_service import mp_enabled

    # En los tests no hay credenciales: mp_enabled debe ser False y no explotar.
    assert mp_enabled() is False


def test_listar_tarjetas_informa_si_mp_esta_apagado():
    """El front necesita saberlo para no mostrar un formulario que no va a andar."""
    import inspect

    from api.routes.billing import listar_tarjetas

    assert "mp_enabled" in inspect.getsource(listar_tarjetas)


# ═══ Cambiar la tarjeta de cobro se hace CONTRA Mercado Pago ═══════════════
# Escribir un rol en nuestra tabla no cambia con qué tarjeta cobra MP: el
# preapproval sigue apuntando a la anterior. Si la pantalla dice "se cobra con
# esta", tiene que ser verdad.


class _Res:
    def __init__(self, filas):
        self._filas = list(filas)

    def scalars(self):
        return self

    def all(self):
        return list(self._filas)

    def first(self):
        return self._filas[0] if self._filas else None

    def scalar_one_or_none(self):
        return self._filas[0] if self._filas else None


class _DB:
    def __init__(self, filas=()):
        self.filas = list(filas)
        self.commits = 0

    async def execute(self, stmt):
        return _Res(self.filas)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        pass

    def add(self, obj):
        self.filas.append(obj)


class _Usuario:
    def __init__(self, plan="pro"):
        from uuid import uuid4

        self.id = uuid4()
        self.plan = plan
        self.email = "test@example.com"
        self.full_name = "Test"


def _dos_tarjetas():
    from uuid import uuid4

    from services.cards_service import ROL_PRINCIPAL, ROL_RESPALDO

    class _T:
        def __init__(self, rol, mp_id):
            self.id = uuid4()
            self.role = rol
            self.mp_card_id = mp_id

    return [_T(ROL_PRINCIPAL, "card_A"), _T(ROL_RESPALDO, "card_B")]


@pytest.mark.asyncio
async def test_cambiar_la_principal_con_suscripcion_viva_exige_el_token(monkeypatch):
    """Sin CVV no hay token, y sin token MP no cambia nada: 422, no un 200 mentiroso."""
    from fastapi import HTTPException
    from services import cards_service as cs

    async def _fake_buscar(user):
        return "pre_123"

    tarjetas = _dos_tarjetas()
    monkeypatch.setattr(cs, "mp_enabled", lambda: True)
    monkeypatch.setattr("services.mercadopago_service.buscar_preapproval_id", _fake_buscar)

    with pytest.raises(HTTPException) as e:
        await cs.marcar_principal(_DB(tarjetas), _Usuario("pro"), tarjetas[1].id)
    assert e.value.status_code == 422
    # y los roles quedaron como estaban
    assert tarjetas[0].role == cs.ROL_PRINCIPAL and tarjetas[1].role == cs.ROL_RESPALDO


@pytest.mark.asyncio
async def test_cambiar_la_principal_apunta_el_preapproval_antes_de_guardar(monkeypatch):
    from services import cards_service as cs

    tarjetas = _dos_tarjetas()
    llamadas = []

    async def _fake_cambio(pre_id, token):
        llamadas.append((pre_id, token))

    async def _fake_buscar(user):
        return "pre_123"

    monkeypatch.setattr(cs, "mp_enabled", lambda: True)
    monkeypatch.setattr(cs, "cambiar_medio_de_pago", _fake_cambio)
    monkeypatch.setattr("services.mercadopago_service.buscar_preapproval_id", _fake_buscar)

    db = _DB(tarjetas)
    await cs.marcar_principal(db, _Usuario("pro"), tarjetas[1].id, "tok_abc")

    assert llamadas == [("pre_123", "tok_abc")], "no se avisó a MP del cambio"
    assert tarjetas[1].role == cs.ROL_PRINCIPAL and tarjetas[0].role == cs.ROL_RESPALDO


@pytest.mark.asyncio
async def test_si_mp_rechaza_el_cambio_el_rol_no_se_toca(monkeypatch):
    """Lo peor sería mostrar 'se cobra con esta' sobre una tarjeta que MP no cobra."""
    from fastapi import HTTPException
    from services import cards_service as cs

    tarjetas = _dos_tarjetas()

    async def _falla(pre_id, token):
        raise HTTPException(status_code=502, detail="MP dijo que no")

    async def _fake_buscar(user):
        return "pre_123"

    monkeypatch.setattr(cs, "mp_enabled", lambda: True)
    monkeypatch.setattr(cs, "cambiar_medio_de_pago", _falla)
    monkeypatch.setattr("services.mercadopago_service.buscar_preapproval_id", _fake_buscar)

    db = _DB(tarjetas)
    with pytest.raises(HTTPException) as e:
        await cs.marcar_principal(db, _Usuario("pro"), tarjetas[1].id, "tok_abc")
    assert e.value.status_code == 502
    assert tarjetas[0].role == cs.ROL_PRINCIPAL, "el rol se guardó igual"
    assert db.commits == 0


@pytest.mark.asyncio
async def test_sin_suscripcion_viva_el_rol_se_cambia_sin_token(monkeypatch):
    """No hay preapproval que actualizar: el rol es sólo una preferencia."""
    from services import cards_service as cs

    tarjetas = _dos_tarjetas()
    monkeypatch.setattr(cs, "mp_enabled", lambda: True)
    db = _DB(tarjetas)
    await cs.marcar_principal(db, _Usuario("inactive"), tarjetas[1].id)
    assert tarjetas[1].role == cs.ROL_PRINCIPAL and db.commits == 1


def test_el_front_recibe_el_id_de_la_tarjeta_en_mp_para_poder_tokenizar():
    """Sin `mp_card_id` en el navegador, el SDK no puede pedir un token de una
    tarjeta guardada y el reintento con la de respaldo es inejecutable."""
    from services.cards_service import a_dict

    class _T:
        id = "uuid-interno"
        mp_card_id = "card_A"
        brand = "visa"
        last_four = "1234"
        exp_month = 5
        exp_year = 2030
        holder_name = "Test"
        role = "principal"
        created_at = None

    d = a_dict(_T())
    assert d["mp_card_id"] == "card_A"
    # y sigue sin exponer nada del plástico más allá de lo que se muestra
    prohibidos = {"number", "cvv", "security_code", "mp_customer_id", "token"}
    assert not (set(d) & prohibidos)


# ═══ El frontend tokeniza la tarjeta guardada con la API que corresponde ═══


def _app_html():
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / "frontend" / "app.html"
    return p.read_text(encoding="utf-8")


def test_el_front_usa_fields_createcardtoken_con_cardid():
    """`cardForm` tokeniza a partir del número tipeado: para una tarjeta ya
    guardada hay que usar fields.createCardToken({cardId}). Con la API
    equivocada el reintento no genera token y la feature entera no corre."""
    html = _app_html()
    assert "fields.createCardToken({cardId:" in html.replace(" ", "")
    assert "mp.fields.create('securityCode'" in html


def test_el_formulario_de_pago_no_puede_recargar_la_app():
    """Si el SDK no carga, el submit sin handler navega y se pierde todo el
    estado de la app. El preventDefault se registra antes del primer await."""
    html = _app_html()
    i = html.find("async function facAbrirForm")
    j = html.find("await facCargarSDK()", i)
    assert i > 0 and j > i
    assert "addEventListener('submit',e=>e.preventDefault())" in html[i:j].replace(" ", "")


def test_no_se_pueden_montar_dos_formularios_de_tarjeta():
    """Dos clics seguidos duplicaban ids (facForm, facCvv, facGuardar…)."""
    html = _app_html()
    i = html.find("async function facAbrirForm")
    assert "if(document.querySelector('.fac-form'))return;" in html[i:i + 600]


# ═══ La gracia gobierna el acceso, no es un cartel ════════════════════════


@pytest.mark.asyncio
async def test_si_mp_pausa_dentro_de_la_gracia_no_se_corta_el_acceso():
    from datetime import UTC, datetime, timedelta

    from services import mercadopago_service as mps

    class _Issue:
        grace_until = datetime.now(UTC) + timedelta(days=3)
        pending_downgrade = False

    user = _Usuario("pro")
    issue = _Issue()

    class _DBMixto(_DB):
        async def execute(self, stmt):
            if "billing_issues" in str(stmt).lower():
                return _Res([issue])
            return _Res([user])

    await mps._apply_status_to_user(_DBMixto(), str(user.id), "paused")
    assert user.plan == "pro", "se cortó el acceso durante la gracia prometida"
    assert issue.pending_downgrade is True, "el corte quedó sin agendar"


@pytest.mark.asyncio
async def test_una_baja_explicita_corta_igual():
    """`cancelled` no se difiere nunca: el usuario pidió irse."""
    from services import mercadopago_service as mps

    user = _Usuario("pro")
    await mps._apply_status_to_user(_DB([user]), str(user.id), "cancelled")
    assert user.plan == "inactive"


@pytest.mark.asyncio
async def test_al_vencer_la_gracia_el_acceso_se_corta():
    from datetime import UTC, datetime, timedelta

    from services.billing_issues import aplicar_downgrades_vencidos

    class _Issue:
        user_id = "u1"
        grace_until = datetime.now(UTC) - timedelta(hours=1)
        pending_downgrade = True
        resolved = False

    user = _Usuario("pro")
    issue = _Issue()

    class _DBMixto(_DB):
        async def execute(self, stmt):
            if "billing_issues" in str(stmt).lower():
                return _Res([issue])
            return _Res([user])

    cortados = await aplicar_downgrades_vencidos(_DBMixto())
    assert cortados == 1 and user.plan == "inactive"
    assert issue.pending_downgrade is False, "quedaría cortando en cada corrida"


def test_el_scheduler_aplica_las_gracias_vencidas():
    """Diferir el corte sin nadie que lo aplique sería regalar el servicio."""
    import inspect

    from services.scheduler_service import _run_daily_cleanup

    assert "aplicar_downgrades_vencidos" in inspect.getsource(_run_daily_cleanup)


# ═══ Avisos: lo que prometen los Términos ═════════════════════════════════


def test_el_cobro_rechazado_se_avisa_por_mail_y_no_solo_en_la_app():
    import inspect

    from services.billing_issues import abrir_issue

    assert "_avisar_cobro_rechazado" in inspect.getsource(abrir_issue)


def test_el_aviso_de_renovacion_sale_con_3_dias_completos():
    """Los Términos dicen 'al menos 3 días de anticipación': una ventana
    `<= ahora+3d` avisa el día 2 y los incumple."""
    import inspect

    from services.scheduler_service import _avisar_proximos_cobros

    src = inspect.getsource(_avisar_proximos_cobros)
    assert "next_charge_at >= desde" in src and "next_charge_at < hasta" in src
    assert "next_charge_at <= limite" not in src


def test_el_aviso_de_renovacion_dice_el_importe_y_no_usa_la_plantilla_de_codigos():
    import inspect

    from services.scheduler_service import _avisar_proximos_cobros

    src = inspect.getsource(_avisar_proximos_cobros)
    assert "next_charge_amount" in src, "los Términos prometen el importe"
    assert "_email_code_html" not in src, "esa plantilla habla de códigos que vencen"


def test_el_webhook_de_cobro_recurrente_commitea():
    """`_record_mp_event` sólo hace flush: sin commit se pierde la idempotencia
    de entrega y MP puede reprocesar la misma notificación."""
    import inspect

    from services.mercadopago_service import handle_webhook

    src = inspect.getsource(handle_webhook)
    i = src.find('t == "subscription_authorized_payment"')
    assert i > 0 and "await db.commit()" in src[i:i + 400]


def test_abrir_issue_no_explota_si_quedaron_dos_abiertos():
    """`scalar_one_or_none` levanta MultipleResultsFound y dejaría el webhook
    devolviendo 500 en loop."""
    import inspect

    from services.billing_issues import abrir_issue

    src = inspect.getsource(abrir_issue)
    codigo = "\n".join(
        ln for ln in src.splitlines() if not ln.lstrip().startswith("#")
    )
    assert ".scalars().first()" in codigo
    assert "scalar_one_or_none()" not in codigo
    assert "IntegrityError" in codigo


def test_hay_un_solo_cobro_pendiente_por_usuario_en_la_base():
    from models.payment_method import BillingIssue

    idx = next((i for i in BillingIssue.__table__.indexes
                if i.name == "ix_billing_issues_uno_abierto"), None)
    assert idx is not None and idx.unique is True


def test_el_reintento_deja_constancia_para_no_repetir_el_cartel_rojo():
    import inspect

    from services.billing_issues import obtener_issue_abierto, resolver_con_respaldo

    assert "retry_requested_at" in inspect.getsource(resolver_con_respaldo)
    assert "reintento_pedido" in inspect.getsource(obtener_issue_abierto)


def test_el_front_muestra_el_mensaje_del_backend_tras_el_reintento():
    """El reintento no es instantáneo: descartar el mensaje dejaba al usuario
    mirando el mismo cartel de error."""
    html = _app_html()
    i = html.find("async function facEnviarToken")
    assert i > 0
    bloque = html[i:i + 2000]
    assert "d.message" in bloque and "facIssueMsg" in bloque
