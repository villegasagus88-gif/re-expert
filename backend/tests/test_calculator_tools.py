"""Tests de las calculadoras financieras (Capa 2).

Valores conocidos verificados a mano para VAN, TIR, repago y edge cases.
Pure Python: corre con pytest o como script (`python tests/test_calculator_tools.py`).
"""
from services.calculator_tools import (
    _irr_bisect,
    _npv,
    _payback,
    _tool_analizar_inversion,
    run_calculator_tool,
)


def test_van_valor_conocido():
    # VAN de [-1000,300,400,500,600] @10% = 388.77 (calculado a mano).
    van = _npv(0.10, [-1000, 300, 400, 500, 600])
    assert abs(van - 388.77) < 0.1


def test_tir_valor_conocido():
    # TIR de [-100,60,60]: raíz de -100 + 60/(1+r) + 60/(1+r)^2 = 0 → ~13.07%.
    tir = _irr_bisect([-100, 60, 60])
    assert tir is not None
    assert abs(tir - 0.1307) < 0.001


def test_van_cero_en_la_tir():
    # Por definición, el VAN descontado a la TIR debe ser ~0.
    flujos = [-1000, 300, 400, 500, 600]
    tir = _irr_bisect(flujos)
    assert tir is not None
    assert abs(_npv(tir, flujos)) < 1e-4


def test_repago_simple_exacto():
    # [-1000,500,500,500]: acumulado llega a 0 exactamente en t=2.
    assert _payback([-1000, 500, 500, 500]) == 2.0


def test_repago_con_interpolacion():
    # [-1000,400,400,400]: a t=2 acumulado=-200, en t=3 entra 400 → 2 + 200/400 = 2.5
    assert _payback([-1000, 400, 400, 400]) == 2.5


def test_flujo_sin_tir():
    # Todos positivos → no hay TIR convencional.
    assert _irr_bisect([100, 200, 300]) is None


def test_tool_resultado_completo():
    r = _tool_analizar_inversion(
        flujos=[-1000000, 300000, 400000, 500000, 600000],
        tasa_descuento_anual=12,
        periodicidad="anual",
    )
    assert r["ok"] is True
    assert r["van"] is not None
    assert r["tir_anual_pct"] is not None
    assert r["repago_simple_periodos"] is not None
    assert r["total_invertido"] == 1000000.0
    assert r["total_recuperado"] == 1800000.0
    assert r["ganancia_neta"] == 800000.0
    assert r["multiplo_capital"] == 1.8


def test_tool_sin_tasa_da_tir_y_repago():
    r = _tool_analizar_inversion(flujos=[-1000, 600, 600])
    assert r["ok"] is True
    assert r["van"] is None  # sin tasa, no hay VAN
    assert r["tir_anual_pct"] is not None
    assert r["repago_simple_periodos"] is not None


def test_periodicidad_mensual_anualiza():
    # 2% por mes ≈ 26.8% anual. Flujo donde la TIR por período ~2%.
    r = _tool_analizar_inversion(
        flujos=[-10000, 5150, 5150], tasa_descuento_anual=None, periodicidad="mensual"
    )
    assert r["ok"] is True
    assert r["periodicidad"] == "mensual"
    # tir anual debe ser bastante mayor que la tir por período (anualización).
    assert r["tir_anual_pct"] > r["tir_periodo_pct"]


def test_tool_flujos_invalidos():
    r = _tool_analizar_inversion(flujos=[-1000])
    assert r.get("ok") is False
    assert "error" in r


def test_dispatcher_desconocido():
    import asyncio

    out = asyncio.run(run_calculator_tool("no_existe", {}))
    assert "error" in out


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
