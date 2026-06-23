"""
Tests de la lógica de detección del monitor de créditos (Fase 2).

Cubre las funciones puras (sin red ni DB ni LLM): stripping de HTML, criterio
de "cambió" con tolerancias, y el diff contra el crédito guardado.

Nota: la suite se corre por archivo (ver CLAUDE.md). No requiere ANTHROPIC_API_KEY
(get_client es lazy y no se invoca acá).
"""
from services.creditos_monitor import _diff, _numeric_changed, _strip_html


class _StubCredit:
    """Stub mínimo con los atributos que mira _diff."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_numeric_changed_rate_tolerance():
    # Igual o dentro de tolerancia → no cambia.
    assert _numeric_changed(4.5, 4.5, "interest_rate_tna") is False
    # Cambio real de tasa → sí.
    assert _numeric_changed(4.5, 5.0, "interest_rate_tna") is True
    # El modelo no encontró el dato → no proponemos.
    assert _numeric_changed(4.5, None, "interest_rate_tna") is False
    # Dato nuevo donde no había → sí.
    assert _numeric_changed(None, 5.0, "interest_rate_tna") is True


def test_numeric_changed_income_relative_noise():
    # 2% de diferencia en el ingreso mínimo = ruido → no propone.
    assert _numeric_changed(1_000_000, 1_020_000, "min_income_ars") is False
    # 20% → cambio real.
    assert _numeric_changed(1_000_000, 1_200_000, "min_income_ars") is True


def test_numeric_changed_term_exact():
    assert _numeric_changed(30, 30, "max_term_years") is False
    assert _numeric_changed(30, 20, "max_term_years") is True


def test_strip_html_removes_scripts_keeps_text():
    html = (
        "<html><head><style>.x{color:red}</style>"
        "<script>var a=1;</script></head>"
        "<body><h1>Credito UVA</h1><p>TNA 4,5&nbsp;% &amp; plazo 30</p></body></html>"
    )
    out = _strip_html(html)
    assert "var a" not in out and "color:red" not in out
    assert "<" not in out  # sin tags
    assert "TNA 4,5" in out and "plazo 30" in out
    assert "&" in out  # &amp; decodificado


def test_diff_detects_rate_change_only():
    c = _StubCredit(
        interest_rate_tna=4.5, max_term_years=30, max_financing_percent=75,
        min_income_ars=1_000_000, status="active",
    )
    ext = {
        "interest_rate_tna": 5.0,        # cambia
        "max_term_years": 30,            # igual
        "max_financing_percent": 75,     # igual
        "min_income_ars": 1_020_000,     # ruido
        "status": "active",
    }
    changes = _diff(c, ext)
    assert len(changes) == 1
    assert changes[0]["field"] == "interest_rate_tna"
    assert changes[0]["new"] == 5.0
    assert changes[0]["change_type"] == "field_update"


def test_diff_detects_discontinued():
    c = _StubCredit(
        interest_rate_tna=4.5, max_term_years=30, max_financing_percent=75,
        min_income_ars=1_000_000, status="active",
    )
    ext = {"status": "discontinued", "interest_rate_tna": None}
    changes = _diff(c, ext)
    fields = {ch["field"] for ch in changes}
    assert "status" in fields
    status_change = next(ch for ch in changes if ch["field"] == "status")
    assert status_change["change_type"] == "discontinued"
