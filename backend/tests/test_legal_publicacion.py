"""
Tests del Botón de Arrepentimiento y de la publicación de los legales.

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_legal_publicacion.py --import-mode=importlib -q

Lo que se protege acá es normativa, no comodidad: la Resolución 424/2020 exige
que el botón esté visible en la home y que inicie la revocación **sin ningún
otro trámite**. Cada test de abajo es una forma concreta de romper eso.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from main import app

_FRONT = Path(__file__).resolve().parents[2] / "frontend"


def _leer(nombre: str) -> str:
    return (_FRONT / nombre).read_text(encoding="utf-8")


# ═══ Res. 424/2020: el botón existe, es visible y no exige trámites ═══════


def test_el_boton_de_arrepentimiento_existe_como_pagina():
    assert (_FRONT / "arrepentimiento.html").exists()


def test_el_boton_esta_en_la_home():
    """La Resolución lo exige en la página de inicio, no escondido en otra."""
    home = _leer("index.html")
    assert "arrepentimiento.html" in home
    assert "Arrepentimiento" in home


def test_el_boton_esta_donde_se_contrata():
    """Pricing es donde el usuario pone la plata: ahí tiene que poder salir."""
    assert "arrepentimiento.html" in _leer("pricing.html")


def test_el_endpoint_no_exige_sesion():
    """Pedir login sería el 'trámite adicional' que la Resolución prohíbe."""
    for r in app.routes:
        if getattr(r, "path", None) == "/api/legal/arrepentimiento":
            deps = {d.call.__name__ for d in r.dependant.dependencies}
            assert "get_current_user" not in deps
            assert "require_admin" not in deps
            return
    raise AssertionError("no existe el endpoint de arrepentimiento")


def test_el_endpoint_no_esta_detras_del_gate_de_plan():
    """Alguien que ya no puede pagar tiene que poder revocar igual."""
    import inspect

    import main as main_mod

    src = inspect.getsource(main_mod)
    i = src.find("app.include_router(legal_router)")
    assert i > 0
    assert "dependencies=_paid" not in src[i:i + 120]


def test_el_formulario_no_exige_justificacion():
    """La ley prohíbe pedir motivo. Sólo el email puede ser obligatorio."""
    html = _leer("arrepentimiento.html")
    assert 'id="arrMotivo"' in html
    # El único `required` del formulario es el correo.
    import re
    requeridos = re.findall(r'<(?:input|textarea)[^>]*\brequired\b[^>]*>', html)
    assert len(requeridos) == 1, f"hay {len(requeridos)} campos obligatorios"
    assert 'id="arrEmail"' in requeridos[0]


def test_el_schema_no_exige_motivo_ni_nombre():
    from api.routes.legal import RevocacionRequest

    campos = RevocacionRequest.model_fields
    assert campos["email"].is_required()
    assert not campos["motivo"].is_required()
    assert not campos["nombre"].is_required()


def test_un_email_desconocido_no_se_rechaza():
    """Rebotar a quien tipeó distinto el correo, o compró con otro, sería
    mandarlo a hacer un trámite. Se registra igual."""
    import inspect

    from api.routes.legal import pedir_revocacion

    src = inspect.getsource(pedir_revocacion)
    assert "404" not in src and "no encontrada" not in src.lower()


def test_el_pedido_se_persiste_antes_de_avisar():
    """Si el pedido dependiera del mail, un Resend caído lo haría desaparecer.
    El commit va ANTES del aviso, a propósito."""
    import inspect

    from api.routes.legal import pedir_revocacion

    src = inspect.getsource(pedir_revocacion)
    assert src.index("await db.commit()") < src.index("await _avisar(")


def test_el_aviso_no_puede_tumbar_el_pedido():
    import inspect

    from api.routes.legal import _avisar

    src = inspect.getsource(_avisar)
    assert "except Exception" in src and "raise" not in src


def test_el_pedido_sobrevive_a_la_baja_de_la_cuenta():
    """Es la constancia de que alguien ejerció un derecho: CASCADE la borraría
    justo cuando más se necesita."""
    from models.revocation_request import RevocationRequest

    fk = next(iter(RevocationRequest.__table__.c.user_id.foreign_keys))
    assert fk.ondelete == "SET NULL"


def test_hay_rate_limit():
    """Un formulario público sin límite es un amplificador de mails."""
    import inspect

    from api.routes import legal

    assert "@limiter.limit" in inspect.getsource(legal)


# ═══ Ley 25.326 / 24.240: punto de aceptación en el registro ══════════════


def test_el_registro_tiene_checkbox_de_aceptacion():
    html = _leer("register.html")
    assert 'id="acceptTerms"' in html and 'type="checkbox"' in html


def test_el_checkbox_arranca_desmarcado():
    """Precargarlo invalida el consentimiento: no sería un acto del usuario."""
    import re

    html = _leer("register.html")
    tag = re.search(r'<input[^>]*id="acceptTerms"[^>]*>', html).group(0)
    assert "checked" not in tag


def test_el_checkbox_linkea_a_los_dos_documentos():
    html = _leer("register.html")
    i = html.find('id="acceptTerms"')
    bloque = html[i:i + 700]
    assert "terminos.html" in bloque and "privacidad.html" in bloque


def test_el_registro_se_bloquea_sin_aceptar():
    js = _leer("auth.js")
    i = js.find("async function handleRegister")
    bloque = js[i:i + 2000]
    assert "acceptTerms" in bloque and "acceptErr" in bloque
    # y el guard de retorno tiene que incluirlo
    assert "|| acceptErr" in bloque or "|| acceptErr)" in bloque


def test_el_checkbox_no_rompe_el_login():
    """`handleRegister` es sólo del registro, pero el guard usa byId: si el
    elemento no existe (otro form), no puede bloquear."""
    js = _leer("auth.js")
    i = js.find("async function handleRegister")
    bloque = js[i:i + 2000]
    assert "accept && !accept.checked" in bloque


# ═══ Las páginas legales existen y no publican placeholders ═══════════════


@pytest.mark.parametrize("pagina", ["privacidad.html", "terminos.html", "cookies.html"])
def test_las_paginas_legales_existen(pagina):
    assert (_FRONT / pagina).exists()


@pytest.mark.parametrize("pagina", ["privacidad.html", "terminos.html", "cookies.html"])
def test_las_paginas_no_traen_el_documento_embebido(pagina):
    """El contenido se sirve sólo cuando hay datos del titular. Si estuviera
    pegado en el HTML, el gate no serviría de nada."""
    html = _leer(pagina)
    assert "CONFIRMAR CON TITULAR" not in html
    assert "REVISIÓN LEGAL" not in html


def test_los_documentos_publicables_existen():
    """Los genera scripts/publicar_legales.py; sin ellos las páginas no cargan."""
    for slug in ("terminos-y-condiciones", "politica-de-privacidad", "politica-de-cookies"):
        assert (_FRONT / "legal" / f"{slug}.md").exists(), slug


@pytest.mark.parametrize("slug", [
    "terminos-y-condiciones", "politica-de-privacidad", "politica-de-cookies",
])
def test_lo_publicado_no_filtra_notas_internas(slug):
    """`[REVISIÓN LEGAL]` y `[LÍMITE LEGAL]` son nuestro registro de hasta dónde
    llega cada cláusula. Publicarlos sería mostrarle a la contraparte dónde
    están nuestras defensas más débiles."""
    md = (_FRONT / "legal" / f"{slug}.md").read_text(encoding="utf-8")
    for marcador in ("REVISIÓN LEGAL", "LÍMITE LEGAL", "CONFIRMAR CON TITULAR",
                     "BORRADOR", "Anexo"):
        assert marcador not in md, f"{slug} filtra «{marcador}»"


def test_los_datos_del_titular_viajan_como_tokens():
    """No hardcodeados: se sustituyen desde legal-config.js en el navegador."""
    md = (_FRONT / "legal" / "terminos-y-condiciones.md").read_text(encoding="utf-8")
    for token in ("{{titular}}", "{{cuit}}", "{{domicilio}}", "{{email}}"):
        assert token in md, f"falta {token}"


def test_el_conversor_falla_si_algo_se_le_escapa():
    """La red de seguridad busca el marcador SIN el corchete de cierre: la
    primera versión pedía `[CONFIRMAR CON TITULAR]` literal y dejó pasar una
    nota inline con texto adentro."""
    src = (Path(__file__).resolve().parents[2] / "scripts" / "publicar_legales.py"
           ).read_text(encoding="utf-8")
    assert 'm.rstrip("]") in salida' in src


def test_hoy_los_datos_del_titular_estan_vacios():
    """Si esto falla, alguien los cargó: hay que sacar el aviso preliminar de
    los docs y avisar que el paquete quedó cerrado."""
    js = _leer("legal-config.js")
    import re
    for campo in ("titular", "cuit", "domicilio", "email", "vigenciaDesde"):
        m = re.search(rf"^\s*{campo}:\s*'([^']*)'", js, re.M)
        assert m and m.group(1) == "", f"{campo} ya tiene valor"


def test_lo_que_falta_se_marca_en_vez_de_desaparecer():
    """Un dato faltante que se borra silenciosamente deja una cláusula que
    parece completa y no lo está."""
    js = _leer("legal.js")
    assert "— pendiente]" in js
    assert "function sustituir" in js


def test_el_documento_se_muestra_aunque_falten_datos():
    """No publicar las condiciones es un incumplimiento en sí mismo: el
    documento se renderiza siempre y el hueco se declara."""
    js = _leer("legal.js")
    i = js.find("function render(")
    bloque = js[i:i + 900]
    assert "RE_LEGAL_LISTO" not in bloque, "no puede esconder el documento"
    assert "fetch('legal/'" in bloque


def test_el_render_sanitiza_el_markdown():
    js = _leer("legal.js")
    assert "DOMPurify.sanitize" in js
    # y es fail-closed: sin las librerías, texto plano en vez de HTML crudo
    assert "if (!window.marked || !window.DOMPurify)" in js


def test_el_panel_de_ayuda_ya_no_dice_proximamente_en_lo_legal():
    app_html = _leer("app.html")
    assert "legalRenderPane" in app_html
    i = app_html.find("function acctRenderPane")
    bloque = app_html[i:i + 900]
    assert "item.id==='privacidad'||item.id==='terminos'" in bloque


# ═══ La migración es aditiva ══════════════════════════════════════════════


def test_la_migracion_no_toca_tablas_existentes():
    ruta = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    src = (ruta / "0039_add_revocation_requests.py").read_text(encoding="utf-8")
    assert 'op.create_table(\n        "revocation_requests"' in src
    for peligroso in ("drop_column", "alter_column", "op.execute("):
        assert peligroso not in src.split("def downgrade")[0], peligroso


def test_la_cadena_de_migraciones_no_se_bifurca():
    ruta = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    src = (ruta / "0039_add_revocation_requests.py").read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0038_add_payment_methods"' in src


# ═══ Nada de esto rompe lo que ya andaba ═════════════════════════════════


def test_las_rutas_viejas_siguen_registradas():
    paths = {getattr(r, "path", "") for r in app.routes}
    for p in ("/api/billing/status", "/api/bugs", "/api/account/export", "/health"):
        assert p in paths, f"desapareció {p}"


def test_el_cliente_arranca():
    """Smoke: la app monta con el router nuevo incluido."""
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200


# ═══ La aceptación queda REGISTRADA, no sólo validada en el navegador ═════
# Es lo que le da respaldo probatorio (riesgo R18): un checkbox que sólo vive
# en el cliente no prueba nada el día que alguien discute el contrato.


def test_el_registro_acepta_el_campo_de_aceptacion():
    from api.schemas.auth import RegisterRequest

    campos = RegisterRequest.model_fields
    assert "accepted_terms" in campos


def test_el_campo_es_opcional_para_no_romper_un_frontend_cacheado():
    """Netlify cachea HTML y JS por separado: durante el deploy puede haber un
    register.html viejo contra el backend nuevo. Rechazarlo dejaría a gente
    real sin poder crear cuenta."""
    from api.schemas.auth import RegisterRequest

    r = RegisterRequest(email="a@b.com", password="Password1", full_name="A B")
    assert r.accepted_terms is False


def test_la_aceptacion_se_persiste_con_fecha():
    import inspect

    from services.auth_service import register_user

    src = inspect.getsource(register_user)
    assert "terms_accepted_at" in src
    assert "if accepted_terms else None" in src, (
        "sin aceptación no puede inventarse una fecha"
    )


def test_el_frontend_manda_la_aceptacion():
    js = _leer("auth.js")
    i = js.find("async function handleRegister")
    bloque = js[i:i + 2500]
    assert "accepted_terms" in bloque


def test_la_columna_es_nullable_para_las_cuentas_viejas():
    from models.user import User

    assert User.__table__.c.terms_accepted_at.nullable is True


def test_la_migracion_agrega_la_columna_sin_reescribir_filas():
    ruta = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    src = (ruta / "0039_add_revocation_requests.py").read_text(encoding="utf-8")
    up = src.split("def downgrade")[0]
    assert 'op.add_column(\n        "profiles"' in up
    assert "terms_accepted_at" in up
    assert "nullable=True" in up
    assert "server_default" not in up.split("revocation_requests")[0]
