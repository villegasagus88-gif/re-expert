"""
Tests de Almacenamiento (/api/storage/*).

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_storage.py --import-mode=importlib -q

Cuatro capas:
  - HTTP: auth obligatoria en todos los endpoints.
  - Gate: la sección va detrás del plan pago (decisión de producto).
  - Query: el listado NUNCA baja el BYTEA de los planos.
  - Unit: sanitización del rename, parseo del id compuesto y el header de descarga.
"""
import pytest
from api.routes.storage import (
    _COLS_LISTADO,
    _content_disposition,
    _parse_id,
)
from api.schemas.storage import RenameRequest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app
from pydantic import ValidationError

_UUID = "11111111-1111-1111-1111-111111111111"
_FID = f"planos:{_UUID}"


# ───────────────────────────────── HTTP: auth ──

@pytest.mark.parametrize("metodo,path,kw", [
    ("get", "/api/storage/files", {}),
    ("get", "/api/storage/summary", {}),
    ("patch", f"/api/storage/files/{_FID}", {"json": {"name": "x.pdf"}}),
    ("delete", f"/api/storage/files/{_FID}", {}),
    ("get", f"/api/storage/files/{_FID}/download", {}),
])
def test_todo_exige_sesion(metodo, path, kw):
    r = getattr(TestClient(app), metodo)(path, **kw)
    assert r.status_code == 401, f"{metodo.upper()} {path} devolvió {r.status_code}"


# ───────────────────────────────── gate de plan ──

def _deps(path: str, metodo: str) -> set[str]:
    for r in app.routes:
        if getattr(r, "path", None) == path and metodo in getattr(r, "methods", set()):
            return {d.call.__name__ for d in r.dependant.dependencies}
    raise AssertionError(f"ruta no encontrada: {metodo} {path}")


@pytest.mark.parametrize("path,metodo", [
    ("/api/storage/files", "GET"),
    ("/api/storage/summary", "GET"),
    ("/api/storage/files/{file_id}", "PATCH"),
    ("/api/storage/files/{file_id}", "DELETE"),
    ("/api/storage/files/{file_id}/download", "GET"),
])
def test_almacenamiento_esta_detras_del_gate_de_plan(path, metodo):
    """Decisión de producto: sin plan activo no se accede al almacenamiento.

    Se mira el GRAFO DE DEPENDENCIAS real, no el status de un request anónimo
    (un anónimo corta en 401 por get_current_user antes de llegar al paywall,
    así que un 401 no probaría nada).
    """
    d = _deps(path, metodo)
    assert "require_access" in d, f"{metodo} {path} quedó fuera del gate de plan"
    assert "get_current_user" in d, f"{metodo} {path} debe exigir sesión"


# ───────────────────────────────── el listado no baja los bytes ──

def test_el_listado_nunca_selecciona_el_bytea():
    """`file_data` es el PDF entero: si entra al listado, un usuario con 40
    planos se baja cientos de MB a memoria en cada apertura del panel."""
    nombres = {getattr(c, "key", None) or getattr(c, "name", None) for c in _COLS_LISTADO}
    assert "file_data" not in nombres, "file_data se coló en el listado"


def test_el_listado_compila_sin_file_data_en_el_sql():
    """Prueba de verdad: compilar el SELECT y revisar que el SQL no lo pide."""
    from models.plan_analysis import PlanFile, PlanProject
    from sqlalchemy import select

    sql = str(
        select(*_COLS_LISTADO)
        .join(PlanProject, PlanProject.id == PlanFile.project_id)
        .compile(compile_kwargs={"literal_binds": True})
    )
    assert "file_data" not in sql, f"el SQL del listado incluye file_data:\n{sql}"


# ───────────────────────────────── id compuesto ──

def test_parse_id_valido():
    fuente, ref = _parse_id(_FID)
    assert fuente == "planos"
    assert str(ref) == _UUID


@pytest.mark.parametrize("malo", [
    "", ":", "planos:", "planos:no-es-uuid", _UUID,          # sin fuente
    "otro:" + _UUID,                                          # fuente desconocida
    "../../etc/passwd", "planos:" + _UUID + "/../otro",
])
def test_parse_id_rechaza_basura(malo):
    with pytest.raises(HTTPException) as e:
        _parse_id(malo)
    assert e.value.status_code == 404


# ───────────────────────────────── rename: sanitización ──

@pytest.mark.parametrize("entrada,esperado", [
    ("  planta baja.pdf  ", "planta baja.pdf"),
    ('pla"nta.pdf', "planta.pdf"),
    ("carpeta/otro.pdf", "carpetaotro.pdf"),
    ("a\\b.pdf", "ab.pdf"),
    # los ':' también se van: Windows los rechaza en nombres de archivo
    ("corte\r\nX-Inyectado: 1", "corteX-Inyectado 1"),
    ("plano\t\tA.pdf", "planoA.pdf"),
])
def test_rename_limpia_lo_peligroso(entrada, esperado):
    assert RenameRequest(name=entrada).name == esperado


@pytest.mark.parametrize("malo", ["", "   ", '"""', "\r\n", "///", "\t"])
def test_rename_rechaza_nombres_que_quedan_vacios(malo):
    """Un nombre que después de limpiar queda vacío no puede guardarse:
    la limpieza corre ANTES de validar la longitud."""
    with pytest.raises(ValidationError):
        RenameRequest(name=malo)


def test_rename_respeta_el_maximo_de_la_columna():
    RenameRequest(name="a" * 255)                     # el límite justo entra
    with pytest.raises(ValidationError):
        RenameRequest(name="a" * 256)                 # la columna es String(255)


# ───────────────────────────────── Content-Disposition ──

def test_descarga_fuerza_attachment():
    assert _content_disposition("plano.pdf").startswith("attachment;")


def test_descarga_no_rompe_el_header_con_comillas_ni_saltos():
    """El nombre lo elige el usuario: no puede cerrar el header ni inyectar uno."""
    h = _content_disposition('ma"lo\r\nX-Inyectado: 1.pdf')
    assert "\r" not in h and "\n" not in h
    assert h.count('"') == 2, f"comillas desbalanceadas en el header: {h}"


def test_descarga_conserva_el_nombre_real_en_utf8():
    """Los acentos se pierden en el fallback ASCII pero viajan en filename*."""
    h = _content_disposition("plantá baja ñandú.pdf")
    assert "filename*=UTF-8''" in h
    assert "%C3%A1" in h            # 'á' percent-encoded
    assert "á" not in h.split("filename*=")[0]   # el fallback quedó ASCII


def test_descarga_con_nombre_impresentable_no_queda_vacio():
    h = _content_disposition("....")
    assert 'filename="' in h and 'filename=""' not in h
