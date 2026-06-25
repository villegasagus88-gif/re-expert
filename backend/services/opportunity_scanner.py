"""
Opportunity Scanner — orquestador de análisis de oportunidades inmobiliarias.

Módulo NUEVO e independiente. No toca la Capa 2 de Agustín; sólo importa
get_client() de anthropic_service para la capa LLM. La mitad financiera es
código puro y determinístico (testeable sin DB ni red); la mitad LLM agrega
lectura de mercado, ajuste de probabilidades y extracción desde URL/texto, y
siempre degrada con elegancia (parcial=True) si Anthropic no está disponible.

Moneda de trabajo: USD (benchmark de TIR objetivo configurable).
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Supuestos por defecto (visibles en el informe) ──
DEFAULTS = {
    "comision_pct": 4.0,            # comisión inmobiliaria s/ operación
    "impuestos_compra_pct": 4.0,    # sellos + escritura s/ precio de compra
    "honorarios_pct": 4.0,          # honorarios profesionales s/ costo de obra
    "contingencia_pct": 7.0,        # contingencia de obra
    "descuento_cierre_pct": 8.0,    # gap entre precio publicado y precio de cierre
    "costo_financiero_pct": 0.0,    # s/ inversión (si hay financiación)
    "preventa_pct": 0.0,            # % de ventas durante la obra
    "plazo_obra_meses": 12,
    "plazo_venta_meses": 12,
    "margen_objetivo_pct": 18.0,    # umbral de margen neto para "recomendable"
    "benchmark_tir_pct": 15.0,      # TIR anual objetivo en USD
}

# Probabilidades determinísticas por defecto (las puede ajustar el LLM; suman 100)
PROB_DEFAULT = {"base": 55.0, "optimista": 15.0, "pesimista": 30.0}


# ─────────────────────────── helpers numéricos ───────────────────────────

def _f(x: Any, default: float | None = None) -> float | None:
    """Coerción segura a float (None / '' / no-numérico → default)."""
    if x is None or x == "":
        return default
    try:
        v = float(x)
        if v != v or v in (float("inf"), float("-inf")):  # NaN / inf
            return default
        return v
    except (TypeError, ValueError):
        return default


def _r2(x: float | None) -> float | None:
    if x is None:
        return None
    try:
        return round(float(x), 2)
    except (TypeError, ValueError):
        return None


def _npv(rate: float, flows: list[float]) -> float:
    return sum(cf / ((1.0 + rate) ** i) for i, cf in enumerate(flows))


def _irr_monthly(flows: list[float]) -> float | None:
    """TIR mensual por bisección. None si no hay cambio de signo."""
    if not flows or all(f >= 0 for f in flows) or all(f <= 0 for f in flows):
        return None
    lo, hi = -0.9999, 10.0
    f_lo, f_hi = _npv(lo, flows), _npv(hi, flows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = _npv(mid, flows)
        if abs(f_mid) < 1e-6:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def _pct(part: float | None, whole: float | None) -> float | None:
    if part is None or whole in (None, 0):
        return None
    return part / whole * 100.0


def _get(inputs: dict, key: str, default: float | None = None) -> float | None:
    v = _f(inputs.get(key), None)
    if v is None:
        d = DEFAULTS.get(key, default)
        return _f(d, default)
    return v


# ─────────────────────────── motor financiero ───────────────────────────

def _cashflow_irr(
    upfront: float, obra: float, financiero: float, venta_total: float,
    comision_venta: float, preventa_pct: float, mo_obra: int, mo_venta: int,
) -> tuple[float | None, float | None]:
    """Arma un flujo mensual aproximado y devuelve (tir_anual_pct, necesidad_max_caja)."""
    mo_obra = max(1, int(mo_obra or 1))
    mo_venta = max(1, int(mo_venta or 1))
    T = mo_obra + mo_venta
    flows = [0.0] * (T + 1)
    flows[0] -= upfront
    for m in range(1, mo_obra + 1):
        flows[m] -= obra / mo_obra
    for m in range(1, T + 1):
        flows[m] -= financiero / T
    neto_venta = max(0.0, venta_total - comision_venta)
    preventa_amt = neto_venta * max(0.0, min(100.0, preventa_pct)) / 100.0
    resto = neto_venta - preventa_amt
    for m in range(1, mo_obra + 1):
        flows[m] += preventa_amt / mo_obra
    for m in range(mo_obra + 1, T + 1):
        flows[m] += resto / mo_venta
    # necesidad máxima de caja = peor punto del acumulado
    acc, peor = 0.0, 0.0
    for f in flows:
        acc += f
        peor = min(peor, acc)
    irr_m = _irr_monthly(flows)
    tir_anual = ((1.0 + irr_m) ** 12 - 1.0) * 100.0 if irr_m is not None else None
    return _r2(tir_anual), _r2(-peor)


def _compute_finance(inputs: dict) -> dict:
    """Pro-forma de desarrollo (USD). Todos los supuestos quedan explícitos."""
    m2_vend = _f(inputs.get("m2_vendibles"), 0.0) or 0.0
    precio_pedido = _f(inputs.get("precio_pedido"), 0.0) or 0.0
    costo_obra_m2 = _f(inputs.get("costo_obra_m2"), 0.0) or 0.0
    precio_venta_m2 = _f(inputs.get("precio_venta_m2"), 0.0) or 0.0

    comision_pct = _get(inputs, "comision_pct")
    imp_compra_pct = _get(inputs, "impuestos_compra_pct")
    honor_pct = _get(inputs, "honorarios_pct")
    conting_pct = _get(inputs, "contingencia_pct")
    fin_pct = _get(inputs, "costo_financiero_pct")
    preventa_pct = _get(inputs, "preventa_pct") or 0.0
    mo_obra = int(_get(inputs, "plazo_obra_meses") or 12)
    mo_venta = int(_get(inputs, "plazo_venta_meses") or 12)

    costo_tierra = precio_pedido
    costo_obra_total = costo_obra_m2 * m2_vend
    honorarios = costo_obra_total * honor_pct / 100.0
    contingencia = costo_obra_total * conting_pct / 100.0
    imp_compra = costo_tierra * imp_compra_pct / 100.0
    comision_compra = costo_tierra * comision_pct / 100.0
    venta_total = precio_venta_m2 * m2_vend
    comision_venta = venta_total * comision_pct / 100.0
    base_invertible = costo_tierra + costo_obra_total + honorarios + contingencia + imp_compra + comision_compra
    costo_financiero = base_invertible * fin_pct / 100.0
    inversion_total = base_invertible + costo_financiero
    egresos_totales = inversion_total + comision_venta

    utilidad_bruta = venta_total - (costo_tierra + costo_obra_total)
    utilidad_neta = venta_total - egresos_totales
    margen_bruto = _pct(utilidad_bruta, venta_total)
    margen_neto = _pct(utilidad_neta, venta_total)
    roi = _pct(utilidad_neta, inversion_total)
    incidencia_tierra_m2 = (costo_tierra / m2_vend) if m2_vend else None
    incidencia_tierra_pct = _pct(costo_tierra, venta_total)
    break_even_m2 = (egresos_totales / m2_vend) if m2_vend else None

    tir, caja_max = _cashflow_irr(
        upfront=costo_tierra + imp_compra + comision_compra,
        obra=costo_obra_total + honorarios + contingencia,
        financiero=costo_financiero,
        venta_total=venta_total, comision_venta=comision_venta,
        preventa_pct=preventa_pct, mo_obra=mo_obra, mo_venta=mo_venta,
    )

    return {
        "moneda": inputs.get("moneda", "USD"),
        "inversion_total": _r2(inversion_total),
        "costo_tierra": _r2(costo_tierra),
        "costo_obra_total": _r2(costo_obra_total),
        "honorarios": _r2(honorarios),
        "contingencia": _r2(contingencia),
        "impuestos_compra": _r2(imp_compra),
        "comision_compra": _r2(comision_compra),
        "comision_venta": _r2(comision_venta),
        "costo_financiero": _r2(costo_financiero),
        "venta_total": _r2(venta_total),
        "utilidad_bruta": _r2(utilidad_bruta),
        "utilidad_neta": _r2(utilidad_neta),
        "margen_bruto_pct": _r2(margen_bruto),
        "margen_neto_pct": _r2(margen_neto),
        "roi_pct": _r2(roi),
        "tir_anual_pct": tir,
        "incidencia_tierra_m2": _r2(incidencia_tierra_m2),
        "incidencia_tierra_pct": _r2(incidencia_tierra_pct),
        "break_even_venta_m2": _r2(break_even_m2),
        "necesidad_maxima_caja": caja_max,
        "plazo_total_meses": int(mo_obra + mo_venta),
    }


def _scenario(inputs: dict, dv_precio: float, dv_costo: float, nombre: str, prob: float) -> dict:
    s_in = dict(inputs)
    pv = _f(inputs.get("precio_venta_m2"), 0.0) or 0.0
    co = _f(inputs.get("costo_obra_m2"), 0.0) or 0.0
    s_in["precio_venta_m2"] = pv * (1 + dv_precio / 100.0)
    s_in["costo_obra_m2"] = co * (1 + dv_costo / 100.0)
    fin = _compute_finance(s_in)
    return {
        "nombre": nombre,
        "probabilidad": prob,
        "precio_venta_m2": _r2(s_in["precio_venta_m2"]),
        "costo_obra_m2": _r2(s_in["costo_obra_m2"]),
        "margen_neto_pct": fin["margen_neto_pct"],
        "roi_pct": fin["roi_pct"],
        "tir_pct": fin["tir_anual_pct"],
        "comentario": "",
    }


def _build_scenarios(inputs: dict) -> list[dict]:
    return [
        _scenario(inputs, 0.0, 0.0, "base", PROB_DEFAULT["base"]),
        _scenario(inputs, 8.0, -5.0, "optimista", PROB_DEFAULT["optimista"]),
        _scenario(inputs, -10.0, 12.0, "pesimista", PROB_DEFAULT["pesimista"]),
    ]


def _sensitivity(inputs: dict) -> list[dict]:
    out = []
    for variable, key in (("costo_obra", "costo_obra_m2"), ("precio_venta", "precio_venta_m2")):
        base = _f(inputs.get(key), 0.0) or 0.0
        puntos = []
        for dv in (-10.0, 0.0, 10.0, 20.0):
            s_in = dict(inputs)
            s_in[key] = base * (1 + dv / 100.0)
            fin = _compute_finance(s_in)
            mn = fin["margen_neto_pct"]
            decision = (
                "Descartar" if (mn is None or mn < 8) else
                "Riesgoso" if mn < 14 else
                "Negociar / avanzar" if mn < 20 else "Avanzar"
            )
            puntos.append({
                "variacion_pct": dv, "margen_neto_pct": mn,
                "roi_pct": fin["roi_pct"], "decision": decision,
            })
        out.append({"variable": variable, "puntos": puntos})
    return out


def _score(fin: dict, inputs: dict) -> int:
    """Score financiero 0-100 (las dimensiones de mercado/zonificación las suma la
    capa LLM/datos en fases siguientes; acá es financiero-céntrico y trazable)."""
    def clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    mn = fin.get("margen_neto_pct")
    roi = fin.get("roi_pct")
    tir = fin.get("tir_anual_pct")
    bench = DEFAULTS["benchmark_tir_pct"]
    pv = _f(inputs.get("precio_venta_m2"), 0.0) or 0.0
    be = fin.get("break_even_venta_m2")
    inc = fin.get("incidencia_tierra_pct")
    preventa = _f(inputs.get("preventa_pct"), 0.0) or 0.0

    s_margen = clamp((mn or -10) / 20.0)                                  # 20% neto = full
    s_tir = clamp((tir or 0) / (bench * 1.8)) if tir is not None else 0.4 # ~27% = full
    s_roi = clamp((roi or 0) / 40.0)
    s_be = clamp((pv - be) / pv) if (be and pv) else 0.4                 # headroom sobre break-even
    s_inc = clamp(1.0 - ((inc or 35) - 15) / 30.0)                       # incidencia <=15% ideal
    s_prev = clamp(preventa / 40.0)                                       # 40% preventa = full

    score = (
        s_margen * 28 + s_tir * 22 + s_be * 16 + s_roi * 12 + s_inc * 12 + s_prev * 10
    )
    return int(round(max(0.0, min(100.0, score))))


def _veredicto(score: int) -> tuple[str, str]:
    if score < 40:
        return "descartar", "rechazada"
    if score < 60:
        return "esperar", "precaucion"
    if score < 75:
        return "negociar", "precaucion"
    if score < 90:
        return "due_diligence", "recomendada"
    return "avanzar", "recomendada"


def _precio_max_compra(inputs: dict) -> float | None:
    """Precio de tierra al que el margen neto alcanza el objetivo (despeje simple)."""
    target = DEFAULTS["margen_objetivo_pct"]
    base = _f(inputs.get("precio_pedido"), 0.0) or 0.0
    if base <= 0:
        return None
    # búsqueda: bajamos el precio hasta alcanzar el margen objetivo
    for frac in [1.0 - i * 0.01 for i in range(0, 41)]:  # hasta -40%
        s_in = dict(inputs)
        s_in["precio_pedido"] = base * frac
        mn = _compute_finance(s_in)["margen_neto_pct"]
        if mn is not None and mn >= target:
            return _r2(base * frac)
    return None


def _recommendation(score: int, fin: dict, inputs: dict) -> dict:
    veredicto, _ = _veredicto(score)
    mn = fin.get("margen_neto_pct")
    be = fin.get("break_even_venta_m2")
    pv = _f(inputs.get("precio_venta_m2"), 0.0) or 0.0
    target = DEFAULTS["margen_objetivo_pct"]
    pmax = _precio_max_compra(inputs)

    riesgo = "Velocidad de venta y costo de obra son los que más comprimen el margen."
    if mn is not None and mn < target:
        cond = f"Bajar el precio de entrada (a ~{pmax} si aplica) o vender por encima de {be}/m²."
    else:
        cond = "Mantener el costo de obra dentro de lo previsto y asegurar la preventa mínima."
    rango_venta = f"{be}/m² (break-even) — {_r2(pv * 1.1)}/m² (objetivo)" if be else None

    resumen = (
        f"Score {score}/100. Margen neto estimado {mn}% "
        f"({'por debajo' if (mn or 0) < target else 'en línea con'} el objetivo de {target}%). "
    )
    pasos = [
        "Validar precio real de cierre (no el publicado) y comparables de la zona.",
        "Confirmar costo de obra con presupuesto firme y contingencia.",
        "Chequear normativa urbana / factor de ocupación antes de avanzar.",
    ]
    return {
        "veredicto": veredicto,
        "score": score,
        "resumen": resumen,
        "precio_max_compra": pmax,
        "rango_venta_viable": rango_venta,
        "condicion_minima": cond,
        "riesgo_principal": riesgo,
        "proximos_pasos": pasos,
    }


# Variables críticas que, si faltan, distorsionan el análisis (checklist profesional)
_CRITICAS = [
    ("m2_vendibles", "No cargaste los m² vendibles."),
    ("precio_pedido", "No cargaste el precio pedido."),
    ("costo_obra_m2", "No cargaste el costo de obra por m²."),
    ("precio_venta_m2", "No cargaste el precio de venta esperado por m²."),
    ("comision_pct", "No cargaste la comisión inmobiliaria (se usó el supuesto)."),
    ("impuestos_compra_pct", "No cargaste impuestos de compra (sellos/escritura)."),
    ("costo_financiero_pct", "No contemplaste costo financiero."),
    ("plazo_obra_meses", "No cargaste el plazo de obra."),
    ("plazo_venta_meses", "No cargaste el plazo de venta."),
    ("preventa_pct", "No cargaste el % de preventa esperado."),
    ("contingencia_pct", "No cargaste contingencia de obra (se usó el supuesto)."),
]


def _risks_and_checklist(inputs: dict, fin: dict) -> tuple[list[dict], list[str]]:
    riesgos: list[dict] = []
    mn = fin.get("margen_neto_pct")
    be = fin.get("break_even_venta_m2")
    pv = _f(inputs.get("precio_venta_m2"), 0.0) or 0.0
    inc = fin.get("incidencia_tierra_pct")

    if mn is not None and mn < 10:
        riesgos.append({"tipo": "financiero", "severidad": "alta",
                        "descripcion": f"Margen neto comprimido ({mn}%).",
                        "mitigacion": "Negociar precio de entrada o revisar el producto."})
    if be and pv and pv < be:
        riesgos.append({"tipo": "financiero", "severidad": "alta",
                        "descripcion": f"El precio de venta ({pv}/m²) está por debajo del break-even ({be}/m²).",
                        "mitigacion": "No avanzar a este precio de venta."})
    if inc is not None and inc > 35:
        riesgos.append({"tipo": "financiero", "severidad": "media",
                        "descripcion": f"Incidencia de tierra alta ({inc}% del valor de venta).",
                        "mitigacion": "Revisar el precio de la tierra o densificar el proyecto."})
    if (_f(inputs.get("preventa_pct"), 0.0) or 0.0) <= 0:
        riesgos.append({"tipo": "mercado", "severidad": "media",
                        "descripcion": "Sin preventa: toda la venta depende del mercado post-obra.",
                        "mitigacion": "Asegurar una preventa mínima antes de iniciar."})

    faltantes = [msg for key, msg in _CRITICAS if _f(inputs.get(key), None) is None]
    for msg in faltantes[:6]:
        riesgos.append({"tipo": "dato_faltante", "severidad": "baja",
                        "descripcion": msg, "mitigacion": "Cargá el dato para afinar el análisis."})
    return riesgos, faltantes


def _base_supuestos(inputs: dict) -> list[str]:
    out = []
    for key, label in (
        ("comision_pct", "Comisión inmobiliaria"),
        ("impuestos_compra_pct", "Impuestos de compra (sellos/escritura)"),
        ("honorarios_pct", "Honorarios profesionales (s/ obra)"),
        ("contingencia_pct", "Contingencia de obra"),
        ("descuento_cierre_pct", "Descuento precio publicado vs cierre"),
        ("benchmark_tir_pct", "TIR objetivo (USD)"),
        ("margen_objetivo_pct", "Margen neto objetivo"),
    ):
        if _f(inputs.get(key), None) is None:
            out.append(f"Supuesto utilizado: {label} {DEFAULTS[key]}%.")
    return out


def compute_deterministic(inputs: dict) -> dict:
    """Análisis 100% determinístico (sin LLM). Testeable y siempre disponible."""
    fin = _compute_finance(inputs)
    score = _score(fin, inputs)
    _, recomendacion = _veredicto(score)
    escenarios = _build_scenarios(inputs)
    sensibilidad = _sensitivity(inputs)
    riesgos, faltantes = _risks_and_checklist(inputs, fin)
    rec = _recommendation(score, fin, inputs)
    return {
        "score": score,
        "recomendacion": rec,
        "recomendacion_label": recomendacion,
        "finanzas": fin,
        "escenarios": escenarios,
        "sensibilidad": sensibilidad,
        "riesgos": riesgos,
        "checklist_faltantes": faltantes,
        "lectura_mercado": None,
        "supuestos": _base_supuestos(inputs),
        "fuentes": [{"nombre": "Datos cargados por el usuario", "estado": "dato_usuario", "confianza": 1.0}],
        "parcial": True,  # parcial hasta que corra (o no) la capa LLM
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ─────────────────────────── capa LLM (mercado) ───────────────────────────

_MARKET_TOOL = {
    "name": "reportar_lectura_mercado",
    "description": "Devuelve la lectura de mercado, ajuste de probabilidades de escenarios, "
                   "riesgos cualitativos y fuentes para una oportunidad inmobiliaria.",
    "input_schema": {
        "type": "object",
        "properties": {
            "lectura_mercado": {"type": "string", "description": "2-4 frases accionables sobre zona, demanda y precios. Sin frases genéricas."},
            "prob_base": {"type": "number"},
            "prob_optimista": {"type": "number"},
            "prob_pesimista": {"type": "number"},
            "riesgos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tipo": {"type": "string", "enum": ["mercado", "legal", "financiero", "tecnico", "regulatorio"]},
                        "severidad": {"type": "string", "enum": ["alta", "media", "baja"]},
                        "descripcion": {"type": "string"},
                        "mitigacion": {"type": "string"},
                    },
                    "required": ["tipo", "severidad", "descripcion"],
                },
            },
            "supuestos": {"type": "array", "items": {"type": "string"}},
            "fuentes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nombre": {"type": "string"},
                        "estado": {"type": "string", "enum": ["conectada", "no_conectada", "estimacion"]},
                        "confianza": {"type": "number"},
                    },
                    "required": ["nombre", "estado"],
                },
            },
        },
        "required": ["lectura_mercado", "prob_base", "prob_optimista", "prob_pesimista"],
    },
}

_MARKET_SYSTEM = (
    "Sos un analista senior de real estate argentino. Te paso los datos de una oportunidad y "
    "los NÚMEROS financieros ya calculados (determinísticos). Tu trabajo: dar una lectura de "
    "mercado accionable, ajustar las probabilidades de los 3 escenarios (base/optimista/pesimista, "
    "DEBEN sumar 100) y listar riesgos cualitativos. Reglas estrictas: NO contradigas ni recalcules "
    "los números financieros que te doy. NO inventes fuentes ni datos de mercado: si no tenés un dato "
    "real verificable, marcá la fuente como 'estimacion' o 'no_conectada' y sé explícito en los supuestos. "
    "Evitá frases genéricas tipo 'la zona tiene potencial'. Sé concreto y profesional. Llamá a la tool."
)


def _opp_context(inputs: dict, fin: dict) -> str:
    return (
        f"Oportunidad: {inputs.get('titulo', 'sin título')} | tipo: {inputs.get('tipo_inmueble')} | "
        f"objetivo: {inputs.get('objetivo')} | zona: {inputs.get('zona')} | ciudad: {inputs.get('ciudad')} | "
        f"moneda: {inputs.get('moneda', 'USD')}\n"
        f"Inputs: m2_vendibles={inputs.get('m2_vendibles')}, precio_pedido={inputs.get('precio_pedido')}, "
        f"costo_obra_m2={inputs.get('costo_obra_m2')}, precio_venta_m2={inputs.get('precio_venta_m2')}\n"
        f"Números calculados (NO los cambies): margen_neto={fin.get('margen_neto_pct')}%, "
        f"ROI={fin.get('roi_pct')}%, TIR={fin.get('tir_anual_pct')}%, "
        f"break_even_venta_m2={fin.get('break_even_venta_m2')}, "
        f"incidencia_tierra={fin.get('incidencia_tierra_pct')}%, "
        f"inversion_total={fin.get('inversion_total')}, venta_total={fin.get('venta_total')}"
    )


def _normalize_probs(b: float, o: float, p: float) -> tuple[float, float, float]:
    vals = [max(0.0, _f(x, 0.0) or 0.0) for x in (b, o, p)]
    total = sum(vals)
    if total <= 0:
        return PROB_DEFAULT["base"], PROB_DEFAULT["optimista"], PROB_DEFAULT["pesimista"]
    return tuple(round(v / total * 100.0, 1) for v in vals)  # type: ignore[return-value]


async def _market_read(inputs: dict, fin: dict) -> dict | None:
    """Llama a Claude (tool-forced) para la lectura de mercado. None si falla."""
    try:
        from services.anthropic_service import get_client
        client = get_client()
        resp = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1200,
            system=_MARKET_SYSTEM,
            tools=[_MARKET_TOOL],
            tool_choice={"type": "tool", "name": "reportar_lectura_mercado"},
            messages=[{"role": "user", "content": _opp_context(inputs, fin)}],
        )
    except Exception as e:  # noqa: BLE001 — la IA no debe tumbar el análisis
        logger.warning("Opportunity: lectura de mercado LLM falló — %s", e)
        return None
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)
    return None


async def analyze_opportunity(inputs: dict, use_llm: bool = True) -> dict:
    """Análisis completo: determinístico + (opcional) capa LLM de mercado.

    Siempre devuelve un informe válido. Si la capa LLM falla o se desactiva,
    el informe queda con parcial=True y la mitad financiera intacta.
    """
    analysis = compute_deterministic(inputs)
    if not use_llm:
        return analysis

    market = await _market_read(inputs, analysis["finanzas"])
    if not market:
        return analysis  # parcial=True ya seteado

    # Ajustar probabilidades de escenarios con la lectura del LLM
    b, o, p = _normalize_probs(
        market.get("prob_base"), market.get("prob_optimista"), market.get("prob_pesimista")
    )
    prob_map = {"base": b, "optimista": o, "pesimista": p}
    for esc in analysis["escenarios"]:
        esc["probabilidad"] = prob_map.get(esc["nombre"], esc["probabilidad"])

    analysis["lectura_mercado"] = market.get("lectura_mercado")
    if isinstance(market.get("riesgos"), list):
        analysis["riesgos"] = list(market["riesgos"]) + analysis["riesgos"]
    if isinstance(market.get("supuestos"), list):
        analysis["supuestos"] = analysis["supuestos"] + market["supuestos"]
    if isinstance(market.get("fuentes"), list):
        analysis["fuentes"] = analysis["fuentes"] + market["fuentes"]
    analysis["parcial"] = False
    analysis["generated_at"] = datetime.now(UTC).isoformat()
    return analysis


# ─────────────────────────── extracción desde URL/texto ───────────────────────────

_EXTRACT_TOOL = {
    "name": "extraer_datos_oportunidad",
    "description": "Extrae datos estructurados de una oportunidad inmobiliaria desde el texto de una publicación.",
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "zona": {"type": "string"},
            "ciudad": {"type": "string"},
            "tipo_inmueble": {"type": "string", "enum": ["terreno", "departamento", "ph", "casa", "local", "oficina", "galpon", "edificio", "pozo", "otro"]},
            "superficie_terreno_m2": {"type": "number"},
            "m2_vendibles": {"type": "number"},
            "precio_pedido": {"type": "number"},
            "precio_venta_m2": {"type": "number"},
            "moneda": {"type": "string", "enum": ["USD", "ARS"]},
        },
    },
}

_EXTRACT_SYSTEM = (
    "Extraés datos de una publicación inmobiliaria argentina. Devolvés SOLO lo que el texto indica "
    "explícitamente, llamando a la tool. Si un dato no está, omitilo (no inventes). Precios como "
    "números (sin símbolos), superficies en m². Detectá la moneda (USD o ARS)."
)


async def _fetch_url(url: str) -> str | None:
    try:
        import re

        import httpx
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RE-Expert-Scanner/1.0)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text.strip()[:12000]
    except Exception as e:  # noqa: BLE001
        logger.warning("Opportunity: no se pudo bajar %s — %s", url, e)
        return None


async def extract_inputs(texto: str | None, url: str | None) -> dict:
    """Extrae inputs estructurados desde una URL o texto libre (capa LLM)."""
    content = (texto or "").strip()
    nota = ""
    if url:
        fetched = await _fetch_url(url)
        if fetched:
            content = f"{content}\n\n{fetched}".strip()
        else:
            nota = "No se pudo acceder a la URL; usá el texto pegado si lo hay."
    if not content:
        return {"inputs": {}, "fuentes": [], "nota": "Pegá una URL accesible o el texto de la publicación.", "parcial": True}

    try:
        from services.anthropic_service import get_client
        client = get_client()
        resp = await client.messages.create(
            model=settings.ANTHROPIC_MODEL_FAST,
            max_tokens=600,
            system=_EXTRACT_SYSTEM,
            tools=[_EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extraer_datos_oportunidad"},
            messages=[{"role": "user", "content": content[:12000]}],
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Opportunity: extracción LLM falló — %s", e)
        return {"inputs": {}, "fuentes": [], "nota": "No se pudo procesar con IA ahora. Cargá los datos a mano.", "parcial": True}

    data: dict = {}
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use":
            data = dict(block.input)
            break
    fuentes = []
    if url:
        fuentes.append({"nombre": "Publicación", "url": url, "estado": "conectada",
                        "confianza": 0.6, "fecha_consulta": datetime.now(UTC).date().isoformat()})
    return {"inputs": data, "fuentes": fuentes, "nota": nota, "parcial": False}
