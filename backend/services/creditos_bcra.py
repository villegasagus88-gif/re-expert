"""
Fuente oficial de datos de créditos: comparativa de hipotecarios del BCRA.

El BCRA publica un CSV oficial y estructurado con TODOS los préstamos
hipotecarios de bancos argentinos (una fila por producto/tramo):
  https://www.bcra.gob.ar/archivos/Pdfs/BCRAyVos/HIPOTECA.CSV

Es la fuente más confiable para refrescar el catálogo:
  - Oficial (la dicta el regulador), estructurada y por banco.
  - Trae plazo, financiación (relación monto/tasación), ingreso mínimo, edad,
    antigüedad, relación cuota/ingreso, TEA, CFT, destino de fondos y fecha.
  - No requiere scrapear páginas SPA ni IA: parseo determinístico, sin riesgo
    de que un modelo invente un número estructural.

Este módulo es PURO (csv/stdlib + httpx lazy): sin DB ni settings, así se puede
testear el parser de forma aislada. El que aplica los cambios a la DB vive en
`services/creditos_refresh.py`.
"""
from __future__ import annotations

import csv
import io
import logging
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

BCRA_CSV_URL = "https://www.bcra.gob.ar/archivos/Pdfs/BCRAyVos/HIPOTECA.CSV"
_FETCH_TIMEOUT = 25.0

# Índices de columna del CSV del BCRA (orden fijo del archivo oficial).
_C_ENTIDAD = 1
_C_FECHA = 2
_C_NOMBRE = 4
_C_DENOM = 5
_C_PLAZO_M = 7
_C_INGRESO = 8
_C_ANTIG_M = 9
_C_EDAD = 10
_C_CUOTA_ING = 11
_C_LTV = 12
_C_DESTINO = 13
_C_BENEF = 14
_C_TEA = 16
_C_TIPO = 17
_C_CFT = 18

# bank_name de nuestro catálogo (normalizado) → substring de la entidad BCRA.
BANK_ALIASES: dict[str, str] = {
    "banco nacion": "nacion",
    "banco ciudad": "ciudad",
    "bbva": "bbva",
    "santander": "santander",
    "icbc": "icbc",
    "banco de cordoba bancor": "cordoba",
    "bancor": "cordoba",
}


def _norm(s: Any) -> str:
    s = "" if s is None else str(s)
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return " ".join(s.replace("(", " ").replace(")", " ").split())


def _ar_num(s: Any) -> float | None:
    """Parsea número en formato AR (1.234.567,89 / 75,00 / 360) → float."""
    if s is None:
        return None
    t = str(s).strip()
    if not t or t in ("-", "N/A", "NA", "s/d", "S/D"):
        return None
    t = t.replace("%", "").replace("$", "").replace("UVA", "").strip()
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def parse_bcra(text: str) -> list[dict]:
    """CSV oficial → lista de filas normalizadas (solo lo que usamos)."""
    out: list[dict] = []
    reader = csv.reader(io.StringIO(text), delimiter=";")
    rows = list(reader)
    if not rows:
        return out
    for r in rows[1:]:
        if len(r) <= _C_TIPO:
            continue
        out.append({
            "entidad": r[_C_ENTIDAD].strip(),
            "entidad_norm": _norm(r[_C_ENTIDAD]),
            "fecha": r[_C_FECHA].strip(),
            "nombre": r[_C_NOMBRE].strip(),
            "denom_norm": _norm(r[_C_DENOM]),
            "destino_norm": _norm(r[_C_DESTINO]),
            "benef_norm": _norm(r[_C_BENEF]),
            "tipo": r[_C_TIPO].strip(),
            "plazo_meses": _ar_num(r[_C_PLAZO_M]),
            "ingreso_min": _ar_num(r[_C_INGRESO]),
            "antiguedad_m": _ar_num(r[_C_ANTIG_M]),
            "edad_max": _ar_num(r[_C_EDAD]),
            "cuota_ingreso": _ar_num(r[_C_CUOTA_ING]),
            "ltv": _ar_num(r[_C_LTV]),
            "tea": _ar_num(r[_C_TEA]),
            "cft": _ar_num(r[_C_CFT]),
        })
    return out


def _is_uva(row: dict) -> bool:
    blob = f"{row['nombre']} {row['denom_norm']} {row['tipo']}".lower()
    return "uva" in blob


def _destino_match(destino_norm: str, credit_type: str) -> bool:
    d = destino_norm
    compra = any(k in d for k in ("adquisic", "compra", "vivienda"))
    constr = any(k in d for k in ("construc", "obra"))
    if credit_type in ("construccion",):
        return constr
    if credit_type in ("compra_construccion", "refaccion"):
        return compra or constr or any(k in d for k in ("refacc", "amplia", "termina"))
    # default: compra
    return compra or not constr  # si no dice nada, asumimos compra/adquisición


def match_rows(rows: list[dict], bank_name: str, credit_type: str) -> list[dict]:
    """Filas BCRA del banco indicado, en UVA, que matchean el destino."""
    alias = BANK_ALIASES.get(_norm(bank_name))
    if not alias:
        # fallback: primera palabra significativa del bank_name
        words = [w for w in _norm(bank_name).split() if w not in ("banco", "de", "la", "el")]
        alias = words[0] if words else ""
    if not alias:
        return []
    matched = [
        r for r in rows
        if alias in r["entidad_norm"] and _is_uva(r) and _destino_match(r["destino_norm"], credit_type)
    ]
    return matched


def _min(vals: list[float | None]) -> float | None:
    v = [x for x in vals if x is not None]
    return min(v) if v else None


def _max(vals: list[float | None]) -> float | None:
    v = [x for x in vals if x is not None]
    return max(v) if v else None


def _mode(vals: list[float | None]) -> float | None:
    """Valor más frecuente (el de la línea general, que domina por filas).

    Desempata por el más generoso (mayor) para no subreportar. Robusto frente a
    sub-tramos especiales (sector público, etc.) que distorsionan el max/min.
    """
    v = [x for x in vals if x is not None]
    if not v:
        return None
    counts: dict[float, int] = {}
    for x in v:
        counts[x] = counts.get(x, 0) + 1
    top = max(counts.values())
    return max(k for k, c in counts.items() if c == top)


def derive_terms(rows: list[dict]) -> dict | None:
    """Deriva los términos estructurales de la línea general a partir del BCRA.

    Devuelve None si no hay filas. Estrategia anti-mezcla-de-tramos:
      - plazo: max (es el "hasta X años" que ofrece el banco).
      - financiación/edad/ingreso/antigüedad/cuota: MODA (el valor más frecuente
        = la línea general; evita que un sub-tramo —sector público, 90% LTV—
        contamine el dato). La TEA va como rango (min=mejor tramo, max=peor)
        para usar de cota del rate, no para pisarlo.
    """
    if not rows:
        return None
    plazo_m = _max([r["plazo_meses"] for r in rows])
    return {
        "max_term_years": int(plazo_m // 12) if plazo_m else None,
        "max_financing_percent": _mode([r["ltv"] for r in rows]),
        "min_income_ars": _mode([r["ingreso_min"] for r in rows]),
        "min_employment_seniority_months": _mode([r["antiguedad_m"] for r in rows]),
        "max_age": _mode([r["edad_max"] for r in rows]),
        "relacion_cuota_ingreso_max": _mode([r["cuota_ingreso"] for r in rows]),
        "tea_min": _min([r["tea"] for r in rows]),
        "tea_max": _max([r["tea"] for r in rows]),
        "fecha": _max_fecha([r["fecha"] for r in rows]),
        "n_rows": len(rows),
    }


def _max_fecha(fechas: list[str]) -> str:
    valid = [f for f in fechas if f]
    return max(valid) if valid else ""


async def fetch_csv() -> str | None:
    """Baja el CSV oficial del BCRA. Devuelve el texto o None si falla."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(BCRA_CSV_URL)
            resp.raise_for_status()
            # El archivo del BCRA viene en latin-1.
            return resp.content.decode("latin-1", errors="replace")
    except Exception as e:  # noqa: BLE001
        logger.warning("No se pudo bajar el CSV del BCRA: %s", e)
        return None
