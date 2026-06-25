"""
Tests del motor financiero determinístico del Opportunity Scanner.
Puro (sin DB ni red): valida pro-forma, score, escenarios y robustez.
"""
from services.opportunity_scanner import (
    _irr_monthly,
    _normalize_probs,
    compute_deterministic,
)

BASE = {
    "titulo": "Lote test", "tipo_inmueble": "terreno", "objetivo": "desarrollar", "moneda": "USD",
    "m2_vendibles": 1000, "precio_pedido": 600000, "costo_obra_m2": 1200, "precio_venta_m2": 2400,
    "comision_pct": 4, "preventa_pct": 20, "plazo_obra_meses": 14, "plazo_venta_meses": 10,
}


def test_proforma_math():
    fin = compute_deterministic(BASE)["finanzas"]
    assert fin["venta_total"] == 2400000.0
    assert fin["inversion_total"] == 1980000.0
    assert fin["margen_neto_pct"] == 13.5
    assert fin["incidencia_tierra_pct"] == 25.0
    assert fin["break_even_venta_m2"] == 2076.0


def test_score_in_range_and_recommendation():
    a = compute_deterministic(BASE)
    assert 0 <= a["score"] <= 100
    assert a["recomendacion_label"] in ("recomendada", "precaucion", "rechazada")
    assert a["recomendacion"]["veredicto"]


def test_scenarios_sum_100():
    a = compute_deterministic(BASE)
    assert len(a["escenarios"]) == 3
    assert round(sum(e["probabilidad"] for e in a["escenarios"])) == 100


def test_empty_inputs_do_not_crash():
    a = compute_deterministic({"moneda": "USD"})
    assert 0 <= a["score"] <= 100
    assert a["parcial"] is True
    assert len(a["checklist_faltantes"]) > 0  # debe avisar variables faltantes


def test_negative_margin_flags_risk():
    bad = {**BASE, "precio_venta_m2": 1500}  # vende por debajo del break-even
    a = compute_deterministic(bad)
    assert a["finanzas"]["margen_neto_pct"] < 10
    assert any(r["severidad"] == "alta" for r in a["riesgos"])


def test_normalize_probs():
    assert round(sum(_normalize_probs(50, 30, 20))) == 100
    assert round(sum(_normalize_probs(0, 0, 0))) == 100  # default si vienen en 0


def test_irr_sign_change_required():
    assert _irr_monthly([100, 200, 300]) is None       # sin cambio de signo
    assert _irr_monthly([-1000, 600, 600]) is not None  # inversión + retornos
