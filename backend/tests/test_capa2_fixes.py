"""Regresión de los 2 bugs P1 de la Capa 2 (revisión docs/REVISION_CAPA2_2026-06-06.md).

Bug 1 (cálculo): `_spread` descartaba en silencio el costo de obra que caía fuera
del horizonte de períodos → subvaluaba egresos → inflaba margen/TIR. Ahora el
remanente se imputa (clamp) al período válido y se avisa en `notas`.

Bug 2 (prompt): contradicción prompt vs tool en Transferencia. Es texto del system
prompt (no testeable acá); se verifica por inspección/coherencia con la regla 5.
"""


def test_spread_conserva_total_cuando_excede_horizonte():
    from services.calculator_tools import _spread
    # 900 en 3 períodos desde el índice 2, pero solo hay 4 períodos (0..3):
    # el período 4 cae fuera → su parte (300) debe imputarse al último índice.
    arr = _spread(900.0, 2, 3, 4)
    assert round(sum(arr), 2) == 900.0, f"se perdió plata: {arr}"
    assert arr == [0.0, 0.0, 300.0, 600.0]


def test_spread_caso_normal_sin_overflow():
    from services.calculator_tools import _spread
    assert _spread(100.0, 0, 4, 4) == [25.0, 25.0, 25.0, 25.0]
    assert _spread(90.0, 1, 3, 10)[:5] == [0.0, 30.0, 30.0, 30.0, 0.0]


def test_spread_total_cero_o_dur_invalida():
    from services.calculator_tools import _spread
    assert _spread(0.0, 0, 3, 4) == [0.0, 0.0, 0.0, 0.0]
    assert _spread(100.0, 0, 0, 4) == [0.0, 0.0, 0.0, 0.0]


def test_flujo_fondos_no_pierde_obra_fuera_de_periodos():
    """Reproducción exacta del bug report: antes daba egresos=600/resultado=1400."""
    from services.calculator_tools import _tool_flujo_fondos_desarrollo as f
    r = f(periodos=3, costo_obra_total=900, obra_inicio=2, ingresos_total=2000)
    assert r["ok"] is True
    assert r["total_egresos"] == 900.0, "la obra fuera del horizonte se perdía"
    assert r["total_ingresos"] == 2000.0
    assert r["resultado_neto"] == 1100.0  # antes (con el bug): 1400.0
    assert r["notas"] and "horizonte" in r["notas"], "debe avisar que recortó"


def test_flujo_fondos_obra_dentro_de_periodos_sin_aviso():
    """Si la obra entra completa, no debe aparecer el aviso de recorte."""
    from services.calculator_tools import _tool_flujo_fondos_desarrollo as f
    r = f(periodos=6, costo_obra_total=600, obra_inicio=1, obra_duracion=3, ingresos_total=1000)
    assert r["ok"] is True
    assert r["total_egresos"] == 600.0
    assert not (r["notas"] and "horizonte" in r["notas"])


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests pasaron.")


if __name__ == "__main__":
    _run_all()
