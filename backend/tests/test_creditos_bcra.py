"""
Tests del parser de la fuente oficial BCRA (créditos).

Lógica pura (sin red/DB/LLM): parseo de números AR, selección por moda
(anti-mezcla-de-tramos), match de destino y derivación de términos.
"""
from services.creditos_bcra import (
    _ar_num,
    _destino_match,
    _mode,
    derive_terms,
    parse_bcra,
)


def test_ar_num():
    assert _ar_num("6,17") == 6.17
    assert _ar_num("1.431.200,00") == 1431200.0
    assert _ar_num("75,00") == 75.0
    assert _ar_num("360") == 360.0
    assert _ar_num("") is None
    assert _ar_num("-") is None
    assert _ar_num(None) is None


def test_mode_prefers_frequent_then_higher():
    # 75 aparece 2 veces vs 90 una → 75 (la línea general domina por filas).
    assert _mode([75.0, 75.0, 90.0]) == 75.0
    # empate → el más generoso (no subreportar).
    assert _mode([75.0, 90.0]) == 90.0
    assert _mode([None, None]) is None


def test_destino_match():
    assert _destino_match("adquisicion de vivienda", "compra") is True
    assert _destino_match("construccion de vivienda", "construccion") is True
    # un crédito de compra NO debe matchear una fila de construcción pura.
    assert _destino_match("construccion", "compra") is False
    # compra_construccion matchea ambos.
    assert _destino_match("construccion", "compra_construccion") is True
    assert _destino_match("adquisicion", "compra_construccion") is True


def test_derive_terms_uses_mode_and_max_plazo():
    rows = [
        {"plazo_meses": 360, "ltv": 75.0, "ingreso_min": 500000.0, "antiguedad_m": 12.0,
         "edad_max": 85.0, "cuota_ingreso": 30.0, "tea": 6.17, "fecha": "2025-11-28"},
        {"plazo_meses": 180, "ltv": 75.0, "ingreso_min": 500000.0, "antiguedad_m": 12.0,
         "edad_max": 85.0, "cuota_ingreso": 30.0, "tea": 6.17, "fecha": "2025-11-20"},
        {"plazo_meses": 360, "ltv": 90.0, "ingreso_min": 700000.0, "antiguedad_m": 12.0,
         "edad_max": 85.0, "cuota_ingreso": 30.0, "tea": 12.69, "fecha": "2025-11-28"},
    ]
    t = derive_terms(rows)
    assert t["max_term_years"] == 30          # max(360)/12
    assert t["max_financing_percent"] == 75.0  # moda (2×75 vs 1×90), no el 90 del sub-tramo
    assert t["tea_min"] == 6.17 and t["tea_max"] == 12.69
    assert t["fecha"] == "2025-11-28"
    assert derive_terms([]) is None


def test_parse_bcra_minimal():
    hdr = ";".join(["col"] * 22)
    cols = [""] * 22
    cols[1] = "BANCO X"; cols[2] = "2026-01-01"; cols[4] = "UVA VIVIENDA"
    cols[7] = "360"; cols[12] = "80,00"; cols[16] = "7,76"; cols[17] = "Fija"
    rows = parse_bcra(hdr + "\n" + ";".join(cols))
    assert len(rows) == 1
    assert rows[0]["plazo_meses"] == 360.0
    assert rows[0]["ltv"] == 80.0
    assert rows[0]["tea"] == 7.76
    assert rows[0]["entidad"] == "BANCO X"
