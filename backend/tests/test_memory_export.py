"""Tests del export de memoria (Capa 1B) — foco en higiene de seguridad.

Cubre las dos mitigaciones agregadas en el sweep de seguridad de la Capa 1B:
  - CSV: neutralización de formula/DDE injection (OWASP). El export está pensado
    para compartirse ("llevar a una reunión"), así que el archivo lo abre un
    tercero en Excel/Sheets: un value que arranca con = + - @ podría ejecutar
    una fórmula en su máquina.
  - PDF: escape del mini-markup tipo XML de reportlab. Un value con '<' o '&'
    no debe romper el render (excepción → 500) ni inyectar formato.

render_memory_csv/pdf no tocan DB ni red. Corre con pytest o como script
(`python tests/test_memory_export.py`).
"""
from services.memory_export import (
    _csv_safe,
    render_memory_csv,
    render_memory_pdf,
)


def _items(value, key="dato", confidence="high", source="manual"):
    return [{"key": key, "value": value, "confidence": confidence, "source": source}]


def _csv_text(blob: bytes) -> str:
    return blob.decode("utf-8")  # viene como UTF-8 con BOM


# ── CSV: formula / DDE injection ──

def test_csv_neutraliza_formula_inicial():
    text = _csv_text(render_memory_csv("Proyecto", _items("=1+1")))
    assert "'=1+1" in text          # quedó forzado a texto literal
    assert ",=1+1" not in text      # nunca aparece como celda cruda ejecutable


def test_csv_cubre_todos_los_triggers():
    for trigger in ("=", "+", "-", "@", "\t", "\r"):
        assert _csv_safe(f"{trigger}evil") == f"'{trigger}evil"


def test_csv_valor_normal_queda_intacto():
    assert _csv_safe("USD 250000") == "USD 250000"
    assert _csv_safe("Palermo Soho") == "Palermo Soho"
    # El '-' solo dispara cuando está al INICIO (un negativo intermedio no).
    assert _csv_safe("saldo -500") == "saldo -500"


def test_csv_project_name_tambien_neutralizado():
    # El nombre del proyecto también es controlado por el usuario.
    assert "'=cmd|'/c calc'" in _csv_text(render_memory_csv("=cmd|'/c calc'", _items("ok")))


def test_csv_tiene_bom_y_estructura():
    blob = render_memory_csv("Proyecto X", _items("valor1"))
    assert blob.startswith(b"\xef\xbb\xbf")  # BOM UTF-8 para Excel
    text = _csv_text(blob)
    assert "Dato" in text and "Valor" in text and "valor1" in text


# ── PDF: markup injection / robustez ──

def test_pdf_no_rompe_con_markup_xml():
    # Sin escape, reportlab lanza al parsear <script> como tag desconocido.
    blob = render_memory_pdf(
        "Proyecto <X>", _items("<script>alert(1)</script>", key="riesgo<alto")
    )
    assert blob[:4] == b"%PDF"


def test_pdf_no_rompe_con_ampersand():
    # '&' suelto no es entidad válida en reportlab → rompería el build sin escape.
    blob = render_memory_pdf("A & B", _items("Tom & Jerry S.A. <2025>"))
    assert blob[:4] == b"%PDF"


def test_pdf_smoke_normal():
    blob = render_memory_pdf("Edificio Palermo", _items("Lote USD 250k"))
    assert blob[:4] == b"%PDF"
    assert len(blob) > 800  # un PDF con tabla pesa bastante más


def test_pdf_sin_items():
    assert render_memory_pdf("Vacío", [])[:4] == b"%PDF"


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
