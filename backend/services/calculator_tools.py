"""
Calculator tools (Capa 2) — matemática financiera exacta para el chat.

El modelo, en vez de "estimar" una TIR/VAN a mano (y equivocarse), llama
`analizar_inversion` con el flujo de fondos y recibe los números calculados
con precisión en Python puro (sin dependencias externas).

Convenciones:
  - `flujos[0]` es t0 (la inversión inicial, normalmente negativa).
  - `tasa_descuento_anual` viene en PORCENTAJE (12 = 12%). Es opcional:
    sin ella igual se calculan TIR y repago simple.
  - `periodicidad` define cuántos períodos hay por año, para anualizar la TIR.

Cada tool devuelve un dict serializable. Si algo no se puede calcular,
devuelve el resultado parcial + un campo `notas` con la advertencia, nunca
una excepción que rompa el chat.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_PERIODOS_POR_ANIO = {"anual": 1, "mensual": 12, "trimestral": 4}


# ════════════════════════════════════════════════════════════════════
# Matemática (Python puro)
# ════════════════════════════════════════════════════════════════════
def _npv(rate_period: float, flujos: list[float]) -> float:
    """Valor actual neto a una tasa POR PERÍODO. flujos[t] se descuenta t veces."""
    total = 0.0
    for t, cf in enumerate(flujos):
        total += cf / ((1.0 + rate_period) ** t)
    return total


def _irr_bisect(flujos: list[float]) -> float | None:
    """
    TIR POR PERÍODO por bisección sobre VAN=0 en el bracket (-0.9999, 10).

    Devuelve None si no hay cambio de signo en los flujos (no existe TIR real
    convencional) o si la búsqueda no converge.
    """
    # Necesita al menos un negativo y un positivo.
    if not any(f > 0 for f in flujos) or not any(f < 0 for f in flujos):
        return None

    lo, hi = -0.9999, 10.0
    f_lo = _npv(lo, flujos)
    f_hi = _npv(hi, flujos)
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    # Sin cambio de signo en el bracket → no podemos bisectar de forma confiable.
    if (f_lo > 0) == (f_hi > 0):
        return None

    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = _npv(mid, flujos)
        if abs(f_mid) < 1e-9 or (hi - lo) < 1e-12:
            return mid
        if (f_mid > 0) == (f_lo > 0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return (lo + hi) / 2.0


def _payback(flujos: list[float]) -> float | None:
    """
    Período de repago: primer t (con interpolación lineal) donde el acumulado
    pasa de negativo a ≥ 0. Devuelve None si nunca se recupera la inversión.
    """
    acum = 0.0
    prev = 0.0
    for t, cf in enumerate(flujos):
        prev = acum
        acum += cf
        if acum >= 0 and t > 0:
            # Interpolación dentro del período t: cuánto faltaba al inicio.
            falta = -prev
            if cf > 0:
                return round((t - 1) + falta / cf, 4)
            return float(t)
    return None


def _r2(x: float | None, nd: int = 2) -> float | None:
    if x is None:
        return None
    return round(x, nd)


# ════════════════════════════════════════════════════════════════════
# Tool: analizar_inversion
# ════════════════════════════════════════════════════════════════════
def _tool_analizar_inversion(
    flujos: list[Any] | None = None,
    tasa_descuento_anual: float | None = None,
    periodicidad: str = "anual",
    etiquetas: list[str] | None = None,
    **_ignore: Any,
) -> dict:
    notas: list[str] = []

    # Validación / coerción de flujos.
    if not isinstance(flujos, list) or len(flujos) < 2:
        return {
            "error": "Pasá al menos 2 flujos (flujos[0] = inversión inicial, "
            "normalmente negativa).",
            "ok": False,
        }
    try:
        cfs = [float(x) for x in flujos]
    except (TypeError, ValueError):
        return {"error": "Todos los flujos deben ser números.", "ok": False}

    periodicidad = (periodicidad or "anual").strip().lower()
    ppa = _PERIODOS_POR_ANIO.get(periodicidad)
    if ppa is None:
        notas.append(f"periodicidad '{periodicidad}' no reconocida; uso 'anual'.")
        periodicidad, ppa = "anual", 1

    # Tasa de descuento (en %) → por período.
    tasa_periodo = None
    if tasa_descuento_anual is not None:
        try:
            tasa_anual = float(tasa_descuento_anual) / 100.0
            tasa_periodo = (1.0 + tasa_anual) ** (1.0 / ppa) - 1.0
        except (TypeError, ValueError):
            notas.append("tasa_descuento_anual inválida; se ignora.")
            tasa_descuento_anual = None

    # VAN (solo si hay tasa).
    van = _npv(tasa_periodo, cfs) if tasa_periodo is not None else None

    # TIR.
    tir_periodo = _irr_bisect(cfs)
    if tir_periodo is None:
        notas.append(
            "No existe una TIR convencional para este flujo (no hay cambio de "
            "signo, o tiene múltiples raíces)."
        )
        tir_anual = None
    else:
        tir_anual = (1.0 + tir_periodo) ** ppa - 1.0

    # Repago simple.
    repago_simple = _payback(cfs)
    if repago_simple is None:
        notas.append("La inversión no se recupera con los flujos dados (repago simple).")

    # Repago descontado (solo si hay tasa).
    repago_desc = None
    if tasa_periodo is not None:
        descontados = [cf / ((1.0 + tasa_periodo) ** t) for t, cf in enumerate(cfs)]
        repago_desc = _payback(descontados)
        if repago_desc is None:
            notas.append(
                "La inversión no se recupera en valor presente (repago descontado)."
            )

    total_invertido = -sum(f for f in cfs if f < 0)
    total_recuperado = sum(f for f in cfs if f > 0)
    ganancia_neta = sum(cfs)
    multiplo = (
        round(total_recuperado / total_invertido, 3) if total_invertido > 0 else None
    )

    return {
        "ok": True,
        "van": _r2(van),
        "tir_anual_pct": _r2(tir_anual * 100, 2) if tir_anual is not None else None,
        "tir_periodo_pct": _r2(tir_periodo * 100, 4) if tir_periodo is not None else None,
        "repago_simple_periodos": repago_simple,
        "repago_descontado_periodos": repago_desc,
        "total_invertido": _r2(total_invertido),
        "total_recuperado": _r2(total_recuperado),
        "ganancia_neta": _r2(ganancia_neta),
        "multiplo_capital": multiplo,
        "periodicidad": periodicidad,
        "periodos": len(cfs) - 1,
        "tasa_descuento_anual_pct": tasa_descuento_anual,
        "etiquetas": etiquetas if isinstance(etiquetas, list) else None,
        "notas": " ".join(notas) if notas else None,
        "source": "calc",
    }


# ════════════════════════════════════════════════════════════════════
# Tool: factibilidad_rapida
# ════════════════════════════════════════════════════════════════════
_FACTOR_VENDIBLE_DEFAULT = 0.85  # eficiencia vendible/construible típica


def _tool_factibilidad_rapida(
    precio_venta_m2: float | None = None,
    costo_construccion_m2: float | None = None,
    m2_vendibles: float | None = None,
    superficie_terreno_m2: float | None = None,
    fot: float | None = None,
    factor_vendible: float | None = None,
    costo_terreno: float | None = None,
    incidencia_terreno_m2: float | None = None,
    comisiones_pct: float | None = None,
    gastos_generales_pct: float | None = None,
    impuestos_pct: float | None = None,
    **_ignore: Any,
) -> dict:
    """
    Factibilidad rápida de un terreno/proyecto:
      ingresos = m² vendibles × precio_venta_m2
      costos   = terreno + obra + gastos generales + comisiones + impuestos
      margen   = ingresos − costos
    """
    notas: list[str] = []

    def _num(x):
        return None if x is None else float(x)

    try:
        precio_venta_m2 = _num(precio_venta_m2)
        costo_construccion_m2 = _num(costo_construccion_m2)
    except (TypeError, ValueError):
        return {"error": "precio_venta_m2 y costo_construccion_m2 deben ser números.", "ok": False}

    if not precio_venta_m2 or not costo_construccion_m2:
        return {
            "error": "Necesito al menos precio_venta_m2 y costo_construccion_m2.",
            "ok": False,
        }

    fv = float(factor_vendible) if factor_vendible else _FACTOR_VENDIBLE_DEFAULT

    # ── Determinar m² construibles y vendibles ──
    m2_construibles = None
    if m2_vendibles:
        m2_vendibles = float(m2_vendibles)
        m2_construibles = m2_vendibles / fv if factor_vendible else m2_vendibles
        if not factor_vendible:
            notas.append("Asumí m² construibles = m² vendibles (no se dio factor_vendible).")
    elif superficie_terreno_m2 and fot:
        m2_construibles = float(superficie_terreno_m2) * float(fot)
        m2_vendibles = m2_construibles * fv
        notas.append(f"m² vendibles estimados como construibles × {fv} (factor_vendible).")
    else:
        return {
            "error": "Dame m2_vendibles, o bien superficie_terreno_m2 + fot para estimarlos.",
            "ok": False,
        }

    # ── Ingresos ──
    ingresos = m2_vendibles * precio_venta_m2

    # ── Costos ──
    costo_obra = m2_construibles * costo_construccion_m2

    if costo_terreno is not None:
        costo_terreno = float(costo_terreno)
    elif incidencia_terreno_m2 is not None:
        costo_terreno = float(incidencia_terreno_m2) * m2_vendibles
        notas.append("Costo de terreno estimado por incidencia × m² vendibles.")
    else:
        costo_terreno = 0.0
        notas.append("No se incluyó costo de terreno (no se dio costo_terreno ni incidencia).")

    g_pct = float(gastos_generales_pct) if gastos_generales_pct else 0.0
    c_pct = float(comisiones_pct) if comisiones_pct else 0.0
    i_pct = float(impuestos_pct) if impuestos_pct else 0.0
    if not gastos_generales_pct:
        notas.append("Gastos generales (soft costs) en 0% — agregá gastos_generales_pct si aplica.")
    if not comisiones_pct:
        notas.append("Comisiones en 0% — agregá comisiones_pct (ej 4) si vendés vía inmobiliaria.")

    gastos_generales = costo_obra * g_pct / 100.0
    comisiones = ingresos * c_pct / 100.0
    impuestos = ingresos * i_pct / 100.0

    inversion_dura = costo_terreno + costo_obra + gastos_generales
    costo_total = inversion_dura + comisiones + impuestos
    margen = ingresos - costo_total

    return {
        "ok": True,
        "m2_construibles": _r2(m2_construibles),
        "m2_vendibles": _r2(m2_vendibles),
        "ingresos_por_venta": _r2(ingresos),
        "costo_terreno": _r2(costo_terreno),
        "costo_obra": _r2(costo_obra),
        "gastos_generales": _r2(gastos_generales),
        "comisiones": _r2(comisiones),
        "impuestos": _r2(impuestos),
        "inversion_total": _r2(inversion_dura),
        "costo_total": _r2(costo_total),
        "margen": _r2(margen),
        "margen_sobre_ventas_pct": _r2(margen / ingresos * 100) if ingresos else None,
        "markup_sobre_costo_pct": _r2(margen / costo_total * 100) if costo_total else None,
        "roi_sobre_inversion_pct": _r2(margen / inversion_dura * 100) if inversion_dura else None,
        "supuestos": {
            "factor_vendible": fv,
            "comisiones_pct": c_pct,
            "gastos_generales_pct": g_pct,
            "impuestos_pct": i_pct,
        },
        "notas": " ".join(notas) if notas else None,
        "source": "calc",
    }


# ════════════════════════════════════════════════════════════════════
# Schemas (formato Anthropic tool_use)
# ════════════════════════════════════════════════════════════════════
CALCULATOR_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "analizar_inversion",
        "description": (
            "Calcula con PRECISIÓN las métricas financieras de un flujo de fondos: "
            "VAN (valor actual neto), TIR (tasa interna de retorno) y período de "
            "repago, más múltiplo sobre capital y ganancia neta. Usala SIEMPRE que "
            "se discuta la rentabilidad de un proyecto/inversión inmobiliaria o el "
            "usuario dé un flujo de caja. Nunca estimes estos números a mano. "
            "Convención: flujos[0] es t0 (la inversión inicial, normalmente negativa); "
            "los siguientes son los ingresos/egresos de cada período."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "flujos": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "description": "Flujos en orden. flujos[0] = inversión inicial "
                    "(negativa). Ej: [-1000000, 300000, 400000, 500000].",
                },
                "tasa_descuento_anual": {
                    "type": "number",
                    "description": "Tasa de descuento anual en PORCENTAJE (ej: 12 = 12%). "
                    "Opcional: necesaria para VAN y repago descontado. Sin ella igual "
                    "se calculan TIR y repago simple.",
                },
                "periodicidad": {
                    "type": "string",
                    "enum": ["anual", "mensual", "trimestral"],
                    "default": "anual",
                    "description": "Cada cuánto ocurre cada flujo. Define la "
                    "anualización de la TIR.",
                },
                "etiquetas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Opcional: nombre de cada período (ej: ['Terreno', "
                    "'Año 1', 'Año 2']) para el desglose.",
                },
            },
            "required": ["flujos"],
        },
    },
    {
        "name": "factibilidad_rapida",
        "description": (
            "Factibilidad rápida de un terreno o proyecto inmobiliario: calcula "
            "ingresos por venta (m² vendibles × precio), costos (terreno + obra + "
            "gastos generales + comisiones + impuestos), margen y rentabilidad "
            "(margen sobre ventas, markup sobre costo, ROI sobre inversión). Usala "
            "cuando el usuario evalúe si un terreno/negocio 'cierra'. Podés pasar "
            "m2_vendibles directo, o superficie_terreno_m2 + fot para estimarlos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "precio_venta_m2": {"type": "number", "description": "USD por m² vendible."},
                "costo_construccion_m2": {"type": "number", "description": "USD por m² construible (costo de obra)."},
                "m2_vendibles": {"type": "number", "description": "m² vendibles. Si se da, se usa directo."},
                "superficie_terreno_m2": {"type": "number", "description": "Superficie del terreno (alternativa para estimar m²)."},
                "fot": {"type": "number", "description": "Factor de Ocupación Total (edificabilidad). m² construibles = terreno × FOT."},
                "factor_vendible": {"type": "number", "description": "Eficiencia vendible/construible (ej 0.85). Default 0.85 al estimar."},
                "costo_terreno": {"type": "number", "description": "Costo total del terreno en USD."},
                "incidencia_terreno_m2": {"type": "number", "description": "USD de terreno por m² vendible (alternativa a costo_terreno)."},
                "comisiones_pct": {"type": "number", "description": "Comisión de venta en % sobre ingresos (ej 4)."},
                "gastos_generales_pct": {"type": "number", "description": "Gastos generales/soft costs en % sobre el costo de obra (ej 12)."},
                "impuestos_pct": {"type": "number", "description": "Impuestos en % sobre ingresos (ej 3)."},
            },
            "required": ["precio_venta_m2", "costo_construccion_m2"],
        },
    },
]


# ════════════════════════════════════════════════════════════════════
# Dispatcher
# ════════════════════════════════════════════════════════════════════
CALCULATOR_TOOL_IMPLS = {
    "analizar_inversion": _tool_analizar_inversion,
    "factibilidad_rapida": _tool_factibilidad_rapida,
}


async def run_calculator_tool(name: str, inputs: dict[str, Any]) -> dict:
    """Despacha una tool de cálculo. Son puras (no necesitan db/red)."""
    impl = CALCULATOR_TOOL_IMPLS.get(name)
    if impl is None:
        return {"error": f"Calculadora desconocida: {name}"}
    try:
        return impl(**(inputs or {}))
    except Exception as e:  # noqa: BLE001
        logger.exception("Calculator tool %s falló", name)
        return {"error": f"Calculadora {name} falló: {e}", "ok": False}
