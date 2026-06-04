"""Tests de las calculadoras financieras (Capa 2).

Valores conocidos verificados a mano para VAN, TIR, repago y edge cases.
Pure Python: corre con pytest o como script (`python tests/test_calculator_tools.py`).
"""
from services.calculator_tools import (
    _irr_bisect,
    _npv,
    _payback,
    _tool_analizar_inversion,
    _tool_calcular_impuesto_transferencia,
    _tool_calcular_iva,
    _tool_calcular_sellos,
    _tool_factibilidad_rapida,
    _tool_tasacion_comparables,
    _tool_valor_residual_terreno,
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


def test_factibilidad_m2_directo():
    # 1000 m² vendibles × 2500 − obra(1000×1000) − terreno(500000) = 2.5M − 1M − 0.5M = 1.0M
    r = _tool_factibilidad_rapida(
        precio_venta_m2=2500,
        costo_construccion_m2=1000,
        m2_vendibles=1000,
        costo_terreno=500000,
    )
    assert r["ok"] is True
    assert r["ingresos_por_venta"] == 2500000.0
    assert r["costo_obra"] == 1000000.0
    assert r["costo_terreno"] == 500000.0
    assert r["margen"] == 1000000.0
    assert r["margen_sobre_ventas_pct"] == 40.0  # 1M / 2.5M


def test_factibilidad_desde_terreno_fot():
    # terreno 500 × fot 2 = 1000 construibles; vendibles = 1000 × 0.85 = 850
    r = _tool_factibilidad_rapida(
        precio_venta_m2=3000,
        costo_construccion_m2=1200,
        superficie_terreno_m2=500,
        fot=2,
    )
    assert r["ok"] is True
    assert r["m2_construibles"] == 1000.0
    assert r["m2_vendibles"] == 850.0
    assert r["supuestos"]["factor_vendible"] == 0.85


def test_factibilidad_con_comisiones_y_gastos():
    r = _tool_factibilidad_rapida(
        precio_venta_m2=2000,
        costo_construccion_m2=900,
        m2_vendibles=1000,
        costo_terreno=300000,
        comisiones_pct=4,
        gastos_generales_pct=10,
    )
    # ingresos 2M; obra 900k; gg 90k; comis 80k; terreno 300k → costo 1.37M → margen 630k
    assert r["comisiones"] == 80000.0
    assert r["gastos_generales"] == 90000.0
    assert r["costo_total"] == 1370000.0
    assert r["margen"] == 630000.0


def test_factibilidad_faltan_datos():
    r = _tool_factibilidad_rapida(precio_venta_m2=2000, costo_construccion_m2=900)
    assert r.get("ok") is False  # sin m2 ni terreno+fot


def test_factibilidad_break_even():
    # m2_vend=1000, obra 1000@1000=1M, terreno 500k, sin comis/imp/gastos.
    # break-even precio = (terreno+obra)/m2_vend = 1.5M/1000 = 1500.
    r = _tool_factibilidad_rapida(
        precio_venta_m2=2500, costo_construccion_m2=1000, m2_vendibles=1000, costo_terreno=500000
    )
    assert r["precio_equilibrio_m2"] == 1500.0
    assert r["veredicto"] == "verde"  # margen 40% sobre ventas


def test_factibilidad_break_even_con_comision():
    # con comisión 4%, break-even = (terreno+obra)/(m2*(1-0.04)) = 1.5M/960 = 1562.5
    r = _tool_factibilidad_rapida(
        precio_venta_m2=2500, costo_construccion_m2=1000, m2_vendibles=1000,
        costo_terreno=500000, comisiones_pct=4,
    )
    assert r["precio_equilibrio_m2"] == 1562.5


def test_factibilidad_sensibilidad():
    r = _tool_factibilidad_rapida(
        precio_venta_m2=3000, costo_construccion_m2=1200,
        superficie_terreno_m2=500, fot=2, costo_terreno=400000,
    )
    # 3 escenarios de eficiencia y 3 de precio.
    assert len(r["sensibilidad_eficiencia"]) == 3
    assert len(r["sensibilidad_precio"]) == 3
    # eficiencia 0.90 debe dar más m² vendibles y más margen que 0.80.
    e80 = r["sensibilidad_eficiencia"][0]
    e90 = r["sensibilidad_eficiencia"][2]
    assert e90["m2_vendibles"] > e80["m2_vendibles"]
    assert e90["margen"] > e80["margen"]


def test_factibilidad_gastos_base_ventas():
    # gastos 12% sobre VENTAS (no sobre obra) deben ser mayores aquí.
    r_obra = _tool_factibilidad_rapida(
        precio_venta_m2=2000, costo_construccion_m2=900, m2_vendibles=1000,
        costo_terreno=300000, gastos_generales_pct=12, gastos_base="obra",
    )
    r_ventas = _tool_factibilidad_rapida(
        precio_venta_m2=2000, costo_construccion_m2=900, m2_vendibles=1000,
        costo_terreno=300000, gastos_generales_pct=12, gastos_base="ventas",
    )
    # ventas: 12% de 2.0M = 240k; obra: 12% de 900k = 108k.
    assert r_ventas["gastos_generales"] == 240000.0
    assert r_obra["gastos_generales"] == 108000.0
    assert r_ventas["margen"] < r_obra["margen"]


def test_iva_extraer():
    # 12100 bruto con 21% → neto 10000, iva 2100.
    r = _tool_calcular_iva(monto=12100, alicuota_pct=21, modo="extraer")
    assert r["ok"] is True
    assert r["neto"] == 10000.0
    assert r["iva"] == 2100.0


def test_iva_agregar():
    r = _tool_calcular_iva(monto=10000, alicuota_pct=21, modo="agregar")
    assert r["bruto"] == 12100.0
    assert r["iva"] == 2100.0


def test_sellos_base_valuacion_y_reparto():
    # precio 100000, valuación 120000 → base 120000; alícuota 3.6 → 4320; ambos → 2160 c/u.
    r = _tool_calcular_sellos(monto=100000, valuacion_fiscal=120000, alicuota_pct=3.6)
    assert r["base_imponible"] == 120000.0
    assert r["impuesto_total"] == 4320.0
    assert r["paga_comprador"] == 2160.0
    assert r["paga_vendedor"] == 2160.0


def test_sellos_exencion_vivienda_unica():
    r = _tool_calcular_sellos(
        monto=80000, alicuota_pct=3.6, vivienda_unica=True, tope_exencion=100000
    )
    assert r["exento"] is True
    assert r["impuesto_total"] == 0.0


def test_tasacion_comparables_mediana_y_valor():
    # comparables USD/m²: 2000, 2200, 2400 → mediana 2200; m2 100 → 220000.
    r = _tool_tasacion_comparables(comparables=[2000, 2200, 2400], m2_objetivo=100)
    assert r["ok"] is True
    assert r["usd_m2_mediana"] == 2200.0
    assert r["usd_m2_referencia"] == 2200.0  # sin descuento ni ajuste
    assert r["valor_estimado"] == 220000.0


def test_tasacion_comparables_descuento_publicacion():
    # mediana 2000 con -10% → ref 1800; m2 50 → 90000.
    r = _tool_tasacion_comparables(
        comparables=[1900, 2000, 2100], m2_objetivo=50, descuento_publicacion_pct=10
    )
    assert r["usd_m2_referencia"] == 1800.0
    assert r["valor_estimado"] == 90000.0


def test_tasacion_comparables_objetos_y_confianza():
    # objetos {precio_total, m2}; muy dispersos → confianza baja.
    r = _tool_tasacion_comparables(
        comparables=[{"precio_total": 100000, "m2": 50}, {"precio_total": 600000, "m2": 100}]
    )
    assert r["ok"] is True
    assert r["confianza"] == "baja"  # n<3 y/o dispersión alta


def test_valor_residual_terreno():
    # m2_vend=1000, precio 2500 → ingresos 2.5M; obra 1000@1000=1M; util 20% de ventas=500k.
    # residual = 2.5M - 1M - 0 - 0 - 500k = 1.0M; incidencia/m2_vend = 1000.
    r = _tool_valor_residual_terreno(
        precio_venta_m2=2500, costo_construccion_m2=1000, m2_vendibles=1000,
        utilidad_objetivo_pct=20,
    )
    assert r["valor_residual_terreno"] == 1000000.0
    assert r["incidencia_m2_vendible"] == 1000.0


def test_valor_residual_negativo():
    # precio bajo + util alta → residual negativo.
    r = _tool_valor_residual_terreno(
        precio_venta_m2=1000, costo_construccion_m2=1200, m2_vendibles=1000,
        utilidad_objetivo_pct=20,
    )
    assert r["valor_residual_terreno"] < 0
    assert "NEGATIVO" in (r["notas"] or "")


def test_sellos_tramos_aplica_tramo_bajo():
    # base 219.000.000 ≤ 226.100.000 → 2.7%.
    tramos = [{"hasta": 226100000, "alicuota_pct": 2.7}, {"hasta": None, "alicuota_pct": 3.5}]
    r = _tool_calcular_sellos(monto=219000000, tramos=tramos)
    assert r["alicuota_pct"] == 2.7
    assert r["impuesto_total"] == _tool_calcular_sellos(monto=219000000, alicuota_pct=2.7)["impuesto_total"]


def test_sellos_tramos_aplica_tramo_alto():
    # base 300.000.000 > 226.100.000 → 3.5% (tramo superior, hasta=null).
    tramos = [{"hasta": 226100000, "alicuota_pct": 2.7}, {"hasta": None, "alicuota_pct": 3.5}]
    r = _tool_calcular_sellos(monto=300000000, tramos=tramos)
    assert r["alicuota_pct"] == 3.5


def test_transferencia_pre2018_sin_impuesto():
    # ITI derogado (Ley 27.743): adquirido antes de 2018 → $0 nacional.
    r = _tool_calcular_impuesto_transferencia(precio_venta=200000, adquirido_post_2018=False)
    assert r["impuesto"] == 0.0
    assert "Sin impuesto nacional" in r["aplica"]


def test_transferencia_ganancias_post2018():
    r = _tool_calcular_impuesto_transferencia(
        precio_venta=200000, costo_adquisicion=150000, adquirido_post_2018=True
    )
    assert "Ganancias cedular" in r["aplica"]
    assert r["impuesto"] == 7500.0  # 15% de (200000-150000)


def test_transferencia_indeterminado_da_ambos():
    r = _tool_calcular_impuesto_transferencia(precio_venta=200000, costo_adquisicion=150000)
    assert r["impuesto"] is None
    assert r["escenario_pre_2018"]["impuesto"] == 0.0
    assert r["escenario_post_2018"]["impuesto"] == 7500.0


def test_dispatcher_calc_impositiva():
    import asyncio

    out = asyncio.run(run_calculator_tool("calcular_iva", {"monto": 1210, "alicuota_pct": 21}))
    assert out["ok"] is True


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
