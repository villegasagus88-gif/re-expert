"""
Tests de reportes de error (/api/bugs/* + /api/admin/bugs/*).

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_bugs.py --import-mode=importlib -q

Tres capas:
  - HTTP: auth obligatoria en usuario, admin obligatorio en la bandeja.
  - Validación: los schemas rechazan basura antes de tocar la DB.
  - Unit: acotado del contexto técnico (input del cliente que va a JSONB).
"""
import pytest
from api.schemas.bug_report import CreateBugReportRequest, UpdateBugReportRequest
from api.routes.bugs import _clean_context
from fastapi.testclient import TestClient
from main import app
from pydantic import ValidationError

_OK = {"title": "No carga el panel", "description": "Entro a Planos y queda cargando para siempre."}


# ───────────────────────────────── HTTP: auth / admin ──

def test_crear_requiere_auth():
    assert TestClient(app).post("/api/bugs", json=_OK).status_code == 401


def test_mis_reportes_requiere_auth():
    assert TestClient(app).get("/api/bugs/mine").status_code == 401


def test_bandeja_admin_requiere_auth():
    assert TestClient(app).get("/api/admin/bugs").status_code == 401


def test_contador_admin_requiere_auth():
    assert TestClient(app).get("/api/admin/bugs/new-count").status_code == 401


def test_patch_admin_requiere_auth():
    r = TestClient(app).patch(
        "/api/admin/bugs/11111111-1111-1111-1111-111111111111", json={"status": "resolved"}
    )
    assert r.status_code == 401


def test_los_reportes_no_estan_detras_del_gate_de_plan():
    """Un usuario sin plan activo tiene que poder reportar justamente eso.

    Se verifica sobre el GRAFO DE DEPENDENCIAS real de la ruta, no por el status
    de un request anónimo: con un anónimo, get_current_user corta con 401 antes
    de que el paywall pudiera correr, así que un 401 NO prueba nada. Si alguien
    mueve estos routers al bloque `_paid` de main.py, este test falla.
    """
    def deps_de(path: str, metodo: str) -> set[str]:
        for r in app.routes:
            if getattr(r, "path", None) == path and metodo in getattr(r, "methods", set()):
                return {d.call.__name__ for d in r.dependant.dependencies}
        raise AssertionError(f"ruta no encontrada: {metodo} {path}")

    for path, metodo in (("/api/bugs", "POST"), ("/api/bugs/mine", "GET")):
        deps = deps_de(path, metodo)
        assert "require_access" not in deps, f"{metodo} {path} quedó detrás del gate de plan"
        assert "get_current_user" in deps, f"{metodo} {path} debe exigir sesión"


def test_las_rutas_admin_exigen_admin():
    """La bandeja y el PATCH no pueden quedar accesibles a un usuario común."""
    for r in app.routes:
        p = getattr(r, "path", "")
        if p.startswith("/api/admin/bugs"):
            deps = {d.call.__name__ for d in r.dependant.dependencies}
            assert "require_admin" in deps, f"{p} sin require_admin"


# ───────────────────────────────── validación de schemas ──

def test_titulo_muy_corto_rechazado():
    with pytest.raises(ValidationError):
        CreateBugReportRequest(title="ab", description=_OK["description"])


def test_descripcion_muy_corta_rechazada():
    with pytest.raises(ValidationError):
        CreateBugReportRequest(title=_OK["title"], description="corto")


def test_severidad_invalida_rechazada():
    with pytest.raises(ValidationError):
        CreateBugReportRequest(**_OK, severity="urgentisimo")


def test_estado_invalido_rechazado_en_patch():
    with pytest.raises(ValidationError):
        UpdateBugReportRequest(status="cerrado")


def test_titulo_de_solo_espacios_rechazado():
    """El strip corre ANTES de medir: '   ' no puede pasar como título válido."""
    with pytest.raises(ValidationError):
        CreateBugReportRequest(title="   ", description=_OK["description"])


def test_descripcion_de_solo_espacios_rechazada():
    with pytest.raises(ValidationError):
        CreateBugReportRequest(title=_OK["title"], description=" " * 20)


def test_los_campos_llegan_trimmeados():
    req = CreateBugReportRequest(
        title="  " + _OK["title"] + "  ", description="  " + _OK["description"] + " ",
        notes="  nota  ",
    )
    assert not req.title.startswith(" ") and not req.title.endswith(" ")
    assert not req.description.startswith(" ")
    assert req.notes == "nota"


def test_payload_valido_se_acepta():
    req = CreateBugReportRequest(**_OK, section="planos", severity="high")
    assert req.section == "planos" and req.severity == "high"
    assert req.context == {}   # default seguro


# ───────────────────────────────── contexto técnico (anti-abuso) ──

def test_contexto_recorta_valores_largos():
    out = _clean_context({"ua": "x" * 5000})
    assert len(out["ua"]) == 500


def test_contexto_acota_cantidad_de_claves():
    out = _clean_context({f"k{i}": "v" for i in range(100)})
    assert len(out) == 20


def test_contexto_descarta_nulos_y_castea():
    out = _clean_context({"a": None, "b": 123, "c": True})
    assert "a" not in out and out["b"] == "123" and out["c"] == "True"


def test_contexto_vacio_no_explota():
    assert _clean_context({}) == {}


# ───────────────────────────────── contrato de las vistas ──

def test_la_vista_del_usuario_no_expone_datos_internos():
    """El usuario NO debe ver admin_note, el contexto técnico ni de quién es."""
    from api.schemas.bug_report import BugReportOut
    campos = set(BugReportOut.model_fields)
    assert not campos & {"admin_note", "context", "user_id", "reporter_email"}


def test_la_vista_del_admin_si_expone_lo_necesario():
    from api.schemas.bug_report import BugReportAdminOut
    campos = set(BugReportAdminOut.model_fields)
    assert {"admin_note", "context", "reporter_email", "ticket", "status"} <= campos
