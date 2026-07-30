"""
Tests de los arreglos derivados de la auditoría legal (legal/RIESGOS-TECNICOS.md).

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_hardening_legal.py --import-mode=importlib -q

Cubre:
  R3  — enlaces firmados para los reportes (antes: públicos y enumerables)
  R5  — cifrado en reposo del secreto TOTP (antes: en claro)
  R7  — filtro determinista de datos financieros en la memoria automática
  R9  — Sentry sin variables locales (antes: podía mandar la contraseña)
  R11 — endpoint de exportación de datos (Ley 25.326 art. 14)
  R15 — coordenadas redondeadas antes de salir a un tercero
  R19 — el logout limpia la memoria de voz del navegador
"""
import time

import pytest
from fastapi.testclient import TestClient
from main import app

# ═══ R3 — enlaces firmados ═══════════════════════════════════════════════


def test_reporte_sin_firma_no_se_sirve():
    """Antes cualquiera con el nombre del archivo se bajaba el informe."""
    r = TestClient(app).get("/static/reports/project-2026-07-30-a1b2c3d4.pdf")
    assert r.status_code == 404


def test_reporte_con_firma_invalida_no_se_sirve():
    r = TestClient(app).get(
        "/static/reports/project-2026-07-30-a1b2c3d4.pdf",
        params={"exp": str(int(time.time()) + 3600), "sig": "0" * 32},
    )
    assert r.status_code == 404


def test_la_firma_es_valida_solo_para_su_archivo():
    """No se puede tomar la firma de un archivo propio y moverla a otro."""
    from core.signed_files import firmar_query, verificar
    from urllib.parse import parse_qs

    q = parse_qs(firmar_query("mio-2026-07-30-aaaaaaaa.pdf"))
    exp, sig = q["exp"][0], q["sig"][0]
    assert verificar("mio-2026-07-30-aaaaaaaa.pdf", exp, sig) is True
    assert verificar("ajeno-2026-07-30-bbbbbbbb.pdf", exp, sig) is False


def test_la_firma_vence():
    from core.signed_files import _firma, verificar

    pasado = int(time.time()) - 10
    assert verificar("x.pdf", str(pasado), _firma("x.pdf", pasado)) is False


def test_no_se_puede_estirar_el_vencimiento():
    """El exp está dentro de la firma: cambiarlo la invalida."""
    from core.signed_files import firmar_query, verificar
    from urllib.parse import parse_qs

    q = parse_qs(firmar_query("x.pdf"))
    assert verificar("x.pdf", str(int(q["exp"][0]) + 99999), q["sig"][0]) is False


@pytest.mark.parametrize("mal", ["", "abc", None])
def test_la_verificacion_no_explota_con_basura(mal):
    from core.signed_files import verificar

    assert verificar("x.pdf", mal, mal) is False


def test_no_hay_path_traversal_en_los_reportes():
    c = TestClient(app)
    for ruta in ("/static/reports/..%2f..%2fmain.py", "/static/reports/sub/dir/x.pdf"):
        assert c.get(ruta).status_code in (404, 405)


def test_los_reportes_ya_no_se_montan_con_staticfiles():
    """StaticFiles servía el directorio entero sin control de acceso."""
    from fastapi.staticfiles import StaticFiles

    for r in app.routes:
        assert not isinstance(getattr(r, "app", None), StaticFiles), (
            "volvió el mount de StaticFiles: los informes quedan públicos otra vez"
        )


# ═══ R5 — el secreto TOTP se guarda cifrado ══════════════════════════════


def test_el_secreto_cifrado_no_contiene_el_original():
    from core.secret_box import cifrar
    from services.totp_service import generate_secret

    s = generate_secret()
    assert s not in cifrar(s)


def test_ida_y_vuelta_del_cifrado():
    from core.secret_box import cifrar, descifrar

    assert descifrar(cifrar("GEZDGNBVGY3TQOJQ")) == "GEZDGNBVGY3TQOJQ"


def test_cifrar_dos_veces_da_distinto():
    """Nonce aleatorio: dos usuarios con el mismo secreto no son correlacionables."""
    from core.secret_box import cifrar

    assert cifrar("MISMO") != cifrar("MISMO")


def test_el_ciphertext_manipulado_se_rechaza():
    """Encrypt-then-MAC: se verifica el tag ANTES de descifrar."""
    from core.secret_box import cifrar, descifrar

    c = cifrar("SECRETO")
    v, nonce, ct, tag = c.split(".")
    assert descifrar(f"{v}.{nonce}.{'A' * len(ct)}.{tag}") is None   # ct alterado
    assert descifrar(f"{v}.{nonce}.{ct}.{'A' * len(tag)}") is None   # tag alterado


@pytest.mark.parametrize("mal", ["", "cualquier cosa", "v9.a.b.c", "v1.no-base64!.x.y"])
def test_descifrar_basura_devuelve_none(mal):
    from core.secret_box import descifrar

    assert descifrar(mal) is None


def test_los_secretos_viejos_en_claro_siguen_funcionando():
    """Migración transparente: nadie tiene que volver a enrolar su app."""
    from core.secret_box import descifrar_o_plano, cifrar

    plano = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    assert descifrar_o_plano(plano) == plano          # heredado
    assert descifrar_o_plano(cifrar(plano)) == plano  # nuevo


def test_el_totp_valida_con_el_secreto_descifrado():
    """El cifrado no rompe la verificación end-to-end del segundo factor."""
    from core.secret_box import cifrar, descifrar_o_plano
    from services.totp_service import generate_secret, totp_at, verify_totp

    s = generate_secret()
    ahora = int(time.time())
    assert verify_totp(descifrar_o_plano(cifrar(s)), totp_at(s, ahora), at=ahora)


def test_el_enrolamiento_guarda_cifrado():
    """Verifica sobre el código real que totp_start no persiste el secreto plano."""
    import inspect
    from services.account_security_service import totp_start

    src = inspect.getsource(totp_start)
    assert "cifrar(secret)" in src, "el secreto se estaría guardando en claro"


# ═══ R7 — filtro de datos financieros en la memoria automática ═══════════


@pytest.mark.parametrize("texto,esperado", [
    ("mi cbu es 0170059920000012345678", "CBU/CVU"),
    ("transferí a 0170 0599 2000 0012 3456 78", "CBU/CVU"),
    ("mi alias es mati.re.expert", "alias bancario"),
    ("pago con 4509 9535 6623 3704", "número de tarjeta"),
    ("el cvv es 737", "código de seguridad de tarjeta"),
    ("mi contraseña es Perro1234", "contraseña"),
])
def test_bloquea_datos_financieros(texto, esperado):
    from core.pii_guard import detectar_dato_financiero

    assert detectar_dato_financiero(texto) == esperado


@pytest.mark.parametrize("texto", [
    "el presupuesto es 45000000 pesos",
    "la superficie es 12500 m2",
    "expediente 1234567890 del municipio",
    "mi telefono es +54 9 261 5551234",
    "FOT 1.2 y FOS 60% en la zona R2",
    "lat -32.8908 lon -68.8272",
    "en 2026 el m2 vale 1850 usd",
    "cuit 20-12345678-9",
    "el cliente se llama Juan y quiere un duplex",
    "",
])
def test_no_bloquea_datos_legitimos(texto):
    """Falsos positivos: un filtro que traba el uso normal se termina apagando."""
    from core.pii_guard import detectar_dato_financiero

    assert detectar_dato_financiero(texto) is None


def test_el_guard_revisa_clave_y_valor():
    from core.pii_guard import texto_seguro_para_memoria

    assert texto_seguro_para_memoria("zona", "Godoy Cruz") == (True, None)
    ok, tipo = texto_seguro_para_memoria("cbu del proveedor", "0170059920000012345678")
    assert ok is False and tipo == "CBU/CVU"


def test_la_memoria_automatica_usa_el_filtro():
    """Sobre el código real: el INSERT no puede correr sin pasar por el guard."""
    import inspect
    from api.routes.chat import _persist_memory_item

    src = inspect.getsource(_persist_memory_item)
    assert "texto_seguro_para_memoria" in src
    # El guard tiene que estar ANTES de tocar la base.
    assert src.index("texto_seguro_para_memoria") < src.index("db.add")


# ═══ R9 — Sentry no manda variables locales ══════════════════════════════


def test_sentry_no_envia_variables_locales():
    """Sin esto, una excepción en login_user(email, password) mandaba la
    contraseña en claro a un tercero. El default del SDK es True."""
    import inspect

    import main

    src = inspect.getsource(main)
    assert "include_local_variables=False" in src


# ═══ R11 — exportación de datos (Ley 25.326 art. 14) ════════════════════


def test_export_exige_sesion():
    assert TestClient(app).get("/api/account/export").status_code == 401


def test_export_no_esta_detras_del_gate_de_plan():
    """Ejercer derechos sobre los propios datos no depende de estar al día."""
    for r in app.routes:
        if getattr(r, "path", None) == "/api/account/export":
            deps = {d.call.__name__ for d in r.dependant.dependencies}
            assert "require_access" not in deps
            assert "get_current_user" in deps
            return
    raise AssertionError("no existe GET /api/account/export")


def test_el_export_no_incluye_credenciales_ni_bytes():
    """Exportar hashes o secretos de 2FA sería crear una vía de fuga."""
    import inspect

    from api.routes import account_data

    src = inspect.getsource(account_data)
    assert 'excluir={"file_data"}' in src, "el export bajaría los planos completos"
    for prohibido in ("password_hash", "twofa_secret", "twofa_recovery"):
        assert f'"{prohibido}"' not in src.split('"cuenta"')[1].split("}")[0], (
            f"{prohibido} no debe exportarse"
        )


# ═══ R15 — minimización de la ubicación ═════════════════════════════════


def test_las_coordenadas_se_redondean_antes_de_salir():
    """Con zoom=13 sólo se resuelve la ciudad: el GPS crudo exponía el domicilio."""
    import inspect

    from services.corralones import reverse_geocode

    src = inspect.getsource(reverse_geocode)
    assert "round(float(lat), 3)" in src and "round(float(lon), 3)" in src


# ═══ R19 — el logout limpia la memoria de voz ═══════════════════════════


def test_el_logout_borra_la_memoria_de_voz():
    """Contenido personal que quedaba en el navegador tras cerrar sesión."""
    from pathlib import Path

    js = (Path(__file__).resolve().parents[2] / "frontend" / "authService.js").read_text(
        encoding="utf-8"
    )
    assert "re_voice_memory" in js
    # Tiene que limpiarse en los tres caminos de salida.
    assert js.count("removeItem(STORAGE_VOZ)") >= 3, (
        "falta limpiarla en logout, logoutAll o redirectToLogin"
    )


# ═══ R8 — la purga anonimiza los reportes de error ══════════════════════


def test_la_purga_anonimiza_los_reportes_de_error():
    """La app promete borrar 'todos tus datos'; el email sobrevivía a propósito."""
    import inspect

    from services.scheduler_service import _run_daily_cleanup

    src = inspect.getsource(_run_daily_cleanup)
    assert "BugReport" in src and 'reporter_email=""' in src
    # Y el email ya no se escribe en los logs justo al borrar la cuenta.
    assert "uemail" not in src.split("users_purged += 1")[1][:200]
