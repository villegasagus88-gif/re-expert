"""Tests de los entregables de análisis financiero (PDF/Excel).

Los helpers puros (_fmt, _slug, _norm_secciones, schema) corren siempre.
El render real necesita reportlab/openpyxl: si no están instalados (entorno
local sin deps), esos tests se saltean. Corre con pytest o como script.
"""
import asyncio

from services.financial_artifact import (
    DOCUMENT_TOOL_SCHEMA,
    _fmt,
    _norm_secciones,
    _slug,
    generar_documento,
)

_SECCIONES = [
    {"titulo": "Resultados", "tipo": "kv", "filas": [["TIR anual", "24,89%"], ["VAN", 323936], ["Repago", "2,6 años"]]},
    {"titulo": "Flujo", "tipo": "tabla", "headers": ["Período", "Neto"], "filas": [[0, -300000], [1, 50000]]},
]


def _deps_ok() -> bool:
    try:
        import openpyxl  # noqa: F401
        import reportlab  # noqa: F401
        return True
    except Exception:
        return False


def test_fmt_numeros_ar():
    assert _fmt(323936) == "323.936"
    assert _fmt(24.89) == "24,89"
    assert _fmt(1234567.5) == "1.234.567,50"
    assert _fmt("USD 100") == "USD 100"
    assert _fmt(True) == "Sí"


def test_slug():
    assert _slug("Factibilidad — Edificio Soler 4500!") == "factibilidad-edificio-soler-4500"
    assert _slug("") == "analisis"
    assert _slug(None) == "analisis"


def test_norm_secciones_filtra_basura():
    s = _norm_secciones([{"titulo": "X", "tipo": "raro", "filas": [[1, 2]]}, "no-dict", {"filas": "no-lista"}])
    assert len(s) == 2
    assert s[0]["tipo"] == "kv"  # 'raro' → kv
    assert s[1]["filas"] == []   # "no-lista" → []


def test_schema_bien_formado():
    assert DOCUMENT_TOOL_SCHEMA["name"] == "generar_documento_analisis"
    props = DOCUMENT_TOOL_SCHEMA["input_schema"]["properties"]
    assert props["formato"]["enum"] == ["pdf", "excel", "ambos"]
    assert "secciones" in DOCUMENT_TOOL_SCHEMA["input_schema"]["required"]


def test_generar_documento_requiere_datos():
    out = asyncio.run(generar_documento(titulo="", secciones=[]))
    assert out.get("ok") is False
    assert "error" in out


def test_render_pdf_magic_bytes():
    if not _deps_ok():
        print("  skip render_pdf (sin reportlab/openpyxl)")
        return
    from services.financial_artifact import render_analisis_pdf

    blob = render_analisis_pdf("Test", _SECCIONES, resumen="Cierra verde.", proyecto="Demo")
    assert blob[:4] == b"%PDF"
    assert len(blob) > 800


def test_render_xlsx_magic_bytes():
    if not _deps_ok():
        print("  skip render_xlsx (sin reportlab/openpyxl)")
        return
    from services.financial_artifact import render_analisis_xlsx

    blob = render_analisis_xlsx("Test", _SECCIONES, resumen="Cierra verde.", proyecto="Demo")
    # xlsx es un zip → empieza con 'PK'.
    assert blob[:2] == b"PK"
    assert len(blob) > 1000


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests pasaron.")


if __name__ == "__main__":
    _run_all()
