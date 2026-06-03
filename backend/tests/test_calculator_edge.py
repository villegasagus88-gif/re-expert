"""Edge cases de robustez de analizar_inversion (Capa 2).

La tool la invoca el LLM con inputs que pueden venir raros (strings, tasas
inválidas, flujos sin retorno, kwargs de más). Verifica que NUNCA lanza y que
degrada con gracia (ok=True con `notas`, o ok=False con `error`) — jamás una
excepción que rompa el stream del chat.

Complementa test_calculator_tools.py (del socio), que cubre los valores
conocidos de VAN/TIR/repago. Acá vamos por los bordes.
"""
from services.calculator_tools import _tool_analizar_inversion as calc


def test_acepta_flujos_como_strings():
    # El LLM a veces serializa los números como string; coércionamos.
    r = calc(flujos=["-1000", "600", "700"])
    assert r["ok"] is True
    assert r["total_invertido"] == 1000.0


def test_flujo_no_numerico_da_error_graceful():
    r = calc(flujos=[-1000, "abc", 700])
    assert r.get("ok") is False
    assert "error" in r


def test_tasa_como_string_valida():
    r = calc(flujos=[-1000, 600, 700], tasa_descuento_anual="12")
    assert r["ok"] is True
    assert r["van"] is not None


def test_tasa_invalida_se_ignora_con_nota():
    r = calc(flujos=[-1000, 600, 700], tasa_descuento_anual="doce")
    assert r["ok"] is True
    assert r["van"] is None
    assert r["notas"] and "tasa" in r["notas"].lower()


def test_todos_negativos_sin_tir_ni_repago():
    r = calc(flujos=[-1000, -200, -300])
    assert r["ok"] is True
    assert r["tir_anual_pct"] is None
    assert r["repago_simple_periodos"] is None
    # total_recuperado=0 sobre total_invertido=1500 → múltiplo 0.0 (no None).
    assert r["multiplo_capital"] == 0.0


def test_periodicidad_invalida_cae_a_anual_con_nota():
    r = calc(flujos=[-1000, 600, 700], periodicidad="quincenal")
    assert r["ok"] is True
    assert r["periodicidad"] == "anual"
    assert r["notas"] and "periodicidad" in r["notas"].lower()


def test_inversion_no_se_recupera_repago_none():
    r = calc(flujos=[-1000, 100, 100])
    assert r["ok"] is True
    assert r["repago_simple_periodos"] is None


def test_no_lanza_con_input_basura():
    # periodicidad None, etiquetas que no son lista, kwargs de más.
    r = calc(flujos=[-1000, 1200], periodicidad=None, etiquetas="no-es-lista", foo="bar")
    assert r["ok"] is True
    assert r["etiquetas"] is None


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests pasaron.")


if __name__ == "__main__":
    _run_all()
