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


def _median(xs: list[float]) -> float | None:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


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
    gastos_base: str = "obra",
    impuestos_pct: float | None = None,
    **_ignore: Any,
) -> dict:
    """
    Factibilidad rápida de un terreno/proyecto:
      ingresos = m² vendibles × precio_venta_m2
      costos   = terreno + obra + gastos generales + comisiones + impuestos
      margen   = ingresos − costos

    Incluye precio de equilibrio (break-even), veredicto y análisis de
    sensibilidad por eficiencia vendible y por precio.
    `gastos_base`: 'obra' (% sobre el costo de obra, default) o 'ventas'
    (% sobre los ingresos) — convención distinta, cambia el resultado.
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
    g_base = (gastos_base or "obra").strip().lower()
    if g_base not in ("obra", "ventas"):
        g_base = "obra"
    if not gastos_generales_pct:
        notas.append("Gastos generales (soft costs) en 0% — agregá gastos_generales_pct si aplica.")
    else:
        notas.append(f"Gastos generales = {g_pct}% sobre {'los ingresos' if g_base == 'ventas' else 'el costo de obra'}.")
    if not comisiones_pct:
        notas.append("Comisiones en 0% — agregá comisiones_pct (ej 4) si vendés vía inmobiliaria.")

    # Helper de margen reutilizable para los escenarios de sensibilidad.
    def _calc(m2_vend: float, precio: float) -> dict:
        ing = m2_vend * precio
        gg = (ing if g_base == "ventas" else costo_obra) * g_pct / 100.0
        com = ing * c_pct / 100.0
        imp = ing * i_pct / 100.0
        inv = costo_terreno + costo_obra + gg
        ct = inv + com + imp
        m = ing - ct
        return {
            "ingresos": ing, "gastos_generales": gg, "comisiones": com,
            "impuestos": imp, "inversion": inv, "costo_total": ct, "margen": m,
            "margen_sobre_ventas_pct": (m / ing * 100) if ing else None,
        }

    base = _calc(m2_vendibles, precio_venta_m2)

    # Precio de venta de equilibrio (margen = 0), por m² vendible.
    var_pct = c_pct + i_pct + (g_pct if g_base == "ventas" else 0.0)
    fixed_cost = costo_terreno + costo_obra + (0.0 if g_base == "ventas" else costo_obra * g_pct / 100.0)
    denom = m2_vendibles * (1 - var_pct / 100.0)
    precio_equilibrio = fixed_cost / denom if denom > 0 else None

    # Veredicto por margen sobre ventas.
    msv = base["margen_sobre_ventas_pct"]
    if msv is None:
        veredicto = None
    elif msv >= 25:
        veredicto = "verde"
    elif msv >= 15:
        veredicto = "amarillo"
    else:
        veredicto = "rojo"

    # Sensibilidad por eficiencia vendible (sobre m² construibles).
    sens_efic = []
    for frac in (0.80, 0.85, 0.90):
        mv = m2_construibles * frac
        s = _calc(mv, precio_venta_m2)
        sens_efic.append({
            "factor_vendible": frac,
            "m2_vendibles": _r2(mv),
            "margen": _r2(s["margen"]),
            "margen_sobre_ventas_pct": _r2(s["margen_sobre_ventas_pct"]),
        })

    # Sensibilidad por precio de venta (−10% / base / +10%).
    sens_precio = []
    for factor in (0.90, 1.00, 1.10):
        p = precio_venta_m2 * factor
        s = _calc(m2_vendibles, p)
        sens_precio.append({
            "precio_venta_m2": _r2(p),
            "margen": _r2(s["margen"]),
            "margen_sobre_ventas_pct": _r2(s["margen_sobre_ventas_pct"]),
        })

    return {
        "ok": True,
        "veredicto": veredicto,
        "m2_construibles": _r2(m2_construibles),
        "m2_vendibles": _r2(m2_vendibles),
        "ingresos_por_venta": _r2(base["ingresos"]),
        "costo_terreno": _r2(costo_terreno),
        "costo_obra": _r2(costo_obra),
        "gastos_generales": _r2(base["gastos_generales"]),
        "comisiones": _r2(base["comisiones"]),
        "impuestos": _r2(base["impuestos"]),
        "inversion_total": _r2(base["inversion"]),
        "costo_total": _r2(base["costo_total"]),
        "margen": _r2(base["margen"]),
        "margen_sobre_ventas_pct": _r2(msv),
        "markup_sobre_costo_pct": _r2(base["margen"] / base["costo_total"] * 100) if base["costo_total"] else None,
        "roi_sobre_inversion_pct": _r2(base["margen"] / base["inversion"] * 100) if base["inversion"] else None,
        "precio_equilibrio_m2": _r2(precio_equilibrio) if precio_equilibrio is not None else None,
        "sensibilidad_eficiencia": sens_efic,
        "sensibilidad_precio": sens_precio,
        "supuestos": {
            "factor_vendible": fv,
            "comisiones_pct": c_pct,
            "gastos_generales_pct": g_pct,
            "gastos_base": g_base,
            "impuestos_pct": i_pct,
        },
        "notas": " ".join(notas) if notas else None,
        "source": "calc",
    }


# ════════════════════════════════════════════════════════════════════
# Tools de tasación / valuación
# ════════════════════════════════════════════════════════════════════
def _tool_tasacion_comparables(
    comparables: list | None = None,
    m2_objetivo: float | None = None,
    descuento_publicacion_pct: float | None = None,
    ajuste_pct: float | None = None,
    **_ignore: Any,
) -> dict:
    """
    Valuación por comparables de mercado. `comparables` es una lista de
    USD/m² (números) o de objetos {precio_total, m2}. Devuelve estadística
    robusta (mediana), un valor de referencia ajustado (publicación→cierre y
    ajuste por diferencias) y un nivel de confianza según la dispersión.
    """
    if not isinstance(comparables, list) or len(comparables) < 1:
        return {"error": "Pasá al menos un comparable (USD/m² o {precio_total, m2}).", "ok": False}

    vals: list[float] = []
    for c in comparables:
        try:
            if isinstance(c, (int, float)):
                vals.append(float(c))
            elif isinstance(c, dict):
                p = c.get("precio_total", c.get("precio"))
                m = c.get("m2", c.get("superficie"))
                if p and m:
                    vals.append(float(p) / float(m))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
    vals = [v for v in vals if v > 0]
    if not vals:
        return {"error": "No pude interpretar los comparables.", "ok": False}

    n = len(vals)
    prom = sum(vals) / n
    med = _median(vals)
    mn, mx = min(vals), max(vals)
    std = (sum((v - prom) ** 2 for v in vals) / n) ** 0.5
    disp = (std / prom * 100) if prom else 0.0

    notas: list[str] = []
    desc = float(descuento_publicacion_pct) if descuento_publicacion_pct else 0.0
    aj = float(ajuste_pct) if ajuste_pct else 0.0
    if not descuento_publicacion_pct:
        notas.append(
            "Sin descuento publicación→cierre: estos valores son de PUBLICACIÓN; "
            "el cierre real suele ser 5–15% menor. Pasá descuento_publicacion_pct."
        )
    factor = (1 - desc / 100.0) * (1 + aj / 100.0)
    ref = med * factor

    if n < 3:
        conf = "baja"
        notas.append("Pocos comparables (<3): confianza baja, conseguí más.")
    elif disp > 25:
        conf = "baja"
        notas.append("Comparables muy dispersos (>25%): revisá que sean misma zona/tipología/estado.")
    elif disp > 12:
        conf = "media"
    else:
        conf = "alta"

    out = {
        "ok": True,
        "n": n,
        "usd_m2_min": _r2(mn),
        "usd_m2_max": _r2(mx),
        "usd_m2_promedio": _r2(prom),
        "usd_m2_mediana": _r2(med),
        "usd_m2_referencia": _r2(ref),
        "dispersion_pct": _r2(disp),
        "confianza": conf,
    }
    if m2_objetivo:
        m2o = float(m2_objetivo)
        out["m2_objetivo"] = m2o
        out["valor_estimado"] = _r2(ref * m2o)
        out["rango_estimado"] = [_r2(mn * factor * m2o), _r2(mx * factor * m2o)]
    out["supuestos"] = {"descuento_publicacion_pct": desc, "ajuste_pct": aj}
    out["notas"] = " ".join(notas) if notas else None
    out["source"] = "calc"
    return out


def _tool_valor_residual_terreno(
    precio_venta_m2: float | None = None,
    costo_construccion_m2: float | None = None,
    m2_vendibles: float | None = None,
    superficie_terreno_m2: float | None = None,
    fot: float | None = None,
    factor_vendible: float | None = None,
    gastos_generales_pct: float | None = None,
    gastos_base: str = "obra",
    comisiones_pct: float | None = None,
    utilidad_objetivo_pct: float | None = None,
    **_ignore: Any,
) -> dict:
    """
    Valor residual del terreno: cuánto se puede pagar como MÁXIMO por el suelo
    para lograr una utilidad objetivo, dado el producto terminado.
      residual = ingresos − obra − gastos − comisiones − utilidad_objetivo
    """
    try:
        precio_venta_m2 = float(precio_venta_m2)
        costo_construccion_m2 = float(costo_construccion_m2)
    except (TypeError, ValueError):
        return {"error": "precio_venta_m2 y costo_construccion_m2 son obligatorios y numéricos.", "ok": False}

    notas: list[str] = []
    fv = float(factor_vendible) if factor_vendible else _FACTOR_VENDIBLE_DEFAULT
    if m2_vendibles:
        m2_vend = float(m2_vendibles)
        m2_constr = m2_vend / fv if factor_vendible else m2_vend
    elif superficie_terreno_m2 and fot:
        m2_constr = float(superficie_terreno_m2) * float(fot)
        m2_vend = m2_constr * fv
        notas.append(f"m² vendibles estimados como construibles × {fv}.")
    else:
        return {"error": "Dame m2_vendibles o superficie_terreno_m2 + fot.", "ok": False}

    g_pct = float(gastos_generales_pct) if gastos_generales_pct else 0.0
    c_pct = float(comisiones_pct) if comisiones_pct else 0.0
    u_pct = float(utilidad_objetivo_pct) if utilidad_objetivo_pct else 0.0
    g_base = (gastos_base or "obra").strip().lower()
    if g_base not in ("obra", "ventas"):
        g_base = "obra"
    if not utilidad_objetivo_pct:
        notas.append(
            "utilidad_objetivo_pct en 0%: esto es el máximo a pagar SIN ganancia "
            "(break-even del terreno). Pasá tu utilidad objetivo (ej 20)."
        )

    ingresos = m2_vend * precio_venta_m2
    costo_obra = m2_constr * costo_construccion_m2
    gastos = (ingresos if g_base == "ventas" else costo_obra) * g_pct / 100.0
    comisiones = ingresos * c_pct / 100.0
    utilidad = ingresos * u_pct / 100.0
    residual = ingresos - costo_obra - gastos - comisiones - utilidad

    if residual < 0:
        notas.append(
            "Valor residual NEGATIVO: ni con el terreno gratis se logra esa "
            "utilidad a ese precio/costo. Revisá precio de venta o costo de obra."
        )

    return {
        "ok": True,
        "valor_residual_terreno": _r2(residual),
        "incidencia_m2_vendible": _r2(residual / m2_vend) if m2_vend else None,
        "incidencia_m2_terreno": _r2(residual / float(superficie_terreno_m2)) if superficie_terreno_m2 else None,
        "m2_vendibles": _r2(m2_vend),
        "m2_construibles": _r2(m2_constr),
        "ingresos_por_venta": _r2(ingresos),
        "costo_obra": _r2(costo_obra),
        "gastos_generales": _r2(gastos),
        "comisiones": _r2(comisiones),
        "utilidad_objetivo": _r2(utilidad),
        "supuestos": {
            "factor_vendible": fv,
            "gastos_generales_pct": g_pct,
            "gastos_base": g_base,
            "comisiones_pct": c_pct,
            "utilidad_objetivo_pct": u_pct,
        },
        "notas": " ".join(notas) if notas else None,
        "source": "calc",
    }


# ════════════════════════════════════════════════════════════════════
# Tools impositivas (AR) — paramétricas: la alícuota entra por parámetro
# (con default referencial) para que no quede vieja. La tool encierra la
# LÓGICA correcta; el valor de la tasa lo confirma el modelo/usuario.
# ════════════════════════════════════════════════════════════════════
_IVA_GENERAL = 21.0
_SELLOS_REFERENCIAL = 3.6   # CABA/PBA total aprox; varía por jurisdicción
# ITI derogado por Ley 27.743 (8/7/2024). Solo queda la cedular para post-2018.
_GANANCIAS_INMUEBLE_PCT = 15.0  # cedular sobre la ganancia (adquiridos desde 2018)


def _tool_calcular_iva(
    monto: float | None = None,
    alicuota_pct: float | None = None,
    modo: str = "extraer",
    **_ignore: Any,
) -> dict:
    """
    IVA neto/bruto.
      modo='extraer' → `monto` es BRUTO (con IVA); calcula neto e IVA contenido.
      modo='agregar' → `monto` es NETO (sin IVA); le suma el IVA.
    """
    try:
        monto = float(monto)
    except (TypeError, ValueError):
        return {"error": "monto debe ser un número.", "ok": False}
    alic = float(alicuota_pct) if alicuota_pct else _IVA_GENERAL
    modo = (modo or "extraer").strip().lower()
    notas = []
    if not alicuota_pct:
        notas.append(f"Usé IVA {alic}% (general). Para obra puede aplicar 10,5%; pasá alicuota_pct.")
    if modo == "agregar":
        neto = monto
        iva = monto * alic / 100.0
        bruto = neto + iva
    else:
        bruto = monto
        neto = monto / (1 + alic / 100.0)
        iva = bruto - neto
    return {
        "ok": True,
        "modo": modo,
        "alicuota_pct": alic,
        "neto": _r2(neto),
        "iva": _r2(iva),
        "bruto": _r2(bruto),
        "notas": " ".join(notas) if notas else None,
        "source": "calc",
    }


def _tool_calcular_sellos(
    monto: float | None = None,
    valuacion_fiscal: float | None = None,
    alicuota_pct: float | None = None,
    tramos: list | None = None,
    jurisdiccion: str | None = None,
    reparto: str = "ambos",
    vivienda_unica: bool = False,
    tope_exencion: float | None = None,
    **_ignore: Any,
) -> dict:
    """
    Impuesto de Sellos sobre una compraventa.
      base = max(monto de la operación, valuación fiscal)
      impuesto = base × alícuota; se reparte según `reparto`.

    `tramos` permite alícuotas escalonadas (muchas jurisdicciones cambian la
    tasa según el monto): lista de {"hasta": X, "alicuota_pct": Y}. Se aplica
    la del primer tramo cuyo `hasta` ≥ base; usá hasta=null para el tramo
    superior. La base y los topes deben estar en la MISMA moneda.
    """
    try:
        monto = float(monto)
    except (TypeError, ValueError):
        return {"error": "monto (valor de la operación) es obligatorio y numérico.", "ok": False}

    notas = []
    base = monto
    if valuacion_fiscal is not None:
        base = max(monto, float(valuacion_fiscal))
        if base != monto:
            notas.append("Base = valuación fiscal (mayor que el precio declarado).")

    # Alícuota: por tramos (escalonada) > plana > referencial.
    if tramos and isinstance(tramos, list):
        def _tope(t):
            h = t.get("hasta")
            return float("inf") if h in (None, "") else float(h)
        ordenados = sorted(tramos, key=_tope)
        elegido = next((t for t in ordenados if base <= _tope(t)), ordenados[-1])
        alic = float(elegido.get("alicuota_pct"))
        _h = elegido.get("hasta")
        notas.append(
            f"Tramo aplicado: {alic}% (base {_r2(base)} {'≤ ' + str(_h) if _h not in (None, '') else 'en el tramo superior'})."
        )
    elif alicuota_pct:
        alic = float(alicuota_pct)
    else:
        alic = _SELLOS_REFERENCIAL
        notas.append(
            f"Alícuota {alic}% es REFERENCIAL (CABA/PBA aprox). Sellos varía por "
            "jurisdicción y suele tener tramos por monto — verificá la vigente y pasá "
            "alicuota_pct o tramos."
        )

    exento = False
    if vivienda_unica and tope_exencion is not None and base <= float(tope_exencion):
        exento = True
        notas.append("Exento por vivienda única dentro del tope (verificá condiciones locales).")

    impuesto = 0.0 if exento else base * alic / 100.0

    reparto = (reparto or "ambos").strip().lower()
    if reparto == "comprador":
        comprador, vendedor = impuesto, 0.0
    elif reparto == "vendedor":
        comprador, vendedor = 0.0, impuesto
    else:
        comprador = vendedor = impuesto / 2.0
        reparto = "ambos"

    return {
        "ok": True,
        "jurisdiccion": jurisdiccion,
        "base_imponible": _r2(base),
        "alicuota_pct": alic,
        "exento": exento,
        "impuesto_total": _r2(impuesto),
        "paga_comprador": _r2(comprador),
        "paga_vendedor": _r2(vendedor),
        "reparto": reparto,
        "notas": " ".join(notas) if notas else None,
        "source": "calc",
    }


def _tool_calcular_impuesto_transferencia(
    precio_venta: float | None = None,
    costo_adquisicion: float | None = None,
    adquirido_post_2018: bool | None = None,
    alicuota_ganancias_pct: float | None = None,
    **_ignore: Any,
) -> dict:
    """
    Impuesto NACIONAL que paga el VENDEDOR (persona física no habitualista) al
    transferir un inmueble:
      - Adquirido ANTES de 2018 → $0. El ITI fue DEROGADO (Ley 27.743, vigente
        desde 8/7/2024) y la cedular no aplica a adquisiciones pre-2018.
      - Adquirido DESDE 2018    → Ganancias cedular (15% sobre la ganancia real).
    Si no se sabe la fecha, devuelve ambos escenarios. NO incluye sellos
    provinciales, escribanía ni comisión.
    """
    try:
        precio_venta = float(precio_venta)
    except (TypeError, ValueError):
        return {"error": "precio_venta es obligatorio y numérico.", "ok": False}

    gan_pct = float(alicuota_ganancias_pct) if alicuota_ganancias_pct else _GANANCIAS_INMUEBLE_PCT
    notas = [
        "El ITI fue derogado (Ley 27.743, desde 8/7/2024): ya no se paga.",
        "Aplica a personas físicas no habitualistas. Verificá vigencia y exenciones.",
        "Es impuesto NACIONAL; aparte van sellos provinciales, escribanía y comisión.",
    ]

    costo = float(costo_adquisicion) if costo_adquisicion is not None else None
    ganancia = max(0.0, precio_venta - costo) if costo is not None else None
    cedular = ganancia * gan_pct / 100.0 if ganancia is not None else None
    if costo is None:
        notas.append(
            "Para la cedular necesito costo_adquisicion (actualizable) para la ganancia real."
        )

    if adquirido_post_2018 is True:
        aplica = "Ganancias cedular (adquirido desde 2018)"
        impuesto = cedular
    elif adquirido_post_2018 is False:
        aplica = "Sin impuesto nacional (adquirido antes de 2018: ITI derogado y la cedular no aplica)"
        impuesto = 0.0
    else:
        aplica = "indeterminado (falta fecha de adquisición)"
        impuesto = None
        notas.append(
            "Decime si lo adquiriste antes o desde 2018: antes → $0 nacional; "
            "desde 2018 → cedular 15% sobre la ganancia."
        )

    return {
        "ok": True,
        "aplica": aplica,
        "impuesto": _r2(impuesto) if impuesto is not None else None,
        "escenario_pre_2018": {
            "impuesto": 0.0,
            "motivo": "ITI derogado y cedular no aplica a adquisiciones pre-2018.",
        },
        "escenario_post_2018": {
            "alicuota_pct": gan_pct,
            "ganancia": _r2(ganancia) if ganancia is not None else None,
            "impuesto": _r2(cedular) if cedular is not None else None,
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
            "(margen sobre ventas, markup sobre costo, ROI). Además devuelve el "
            "PRECIO DE EQUILIBRIO (break-even) por m², un VEREDICTO (verde/amarillo/"
            "rojo) y SENSIBILIDAD por eficiencia vendible (80/85/90%) y por precio "
            "(±10%). Usala cuando el usuario evalúe si un terreno 'cierra'. Podés "
            "pasar m2_vendibles directo, o superficie_terreno_m2 + fot para estimar. "
            "Presentá la sensibilidad y el break-even, no solo el caso base."
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
                "gastos_generales_pct": {"type": "number", "description": "Gastos generales/soft costs en % (ej 12). La base la define gastos_base."},
                "gastos_base": {"type": "string", "enum": ["obra", "ventas"], "default": "obra", "description": "Base de los gastos generales: 'obra' (% sobre costo de obra) o 'ventas' (% sobre ingresos). Cambia el resultado; confirmá con el usuario si no está claro."},
                "impuestos_pct": {"type": "number", "description": "Impuestos en % sobre ingresos (ej 3)."},
            },
            "required": ["precio_venta_m2", "costo_construccion_m2"],
        },
    },
    {
        "name": "tasacion_comparables",
        "description": (
            "Valúa un inmueble por comparables de mercado. Primero conseguí los "
            "comparables con search_web (Zonaprop/Reporte Inmobiliario/Properati del "
            "barrio y tipología, últimos 30–60 días) y pasalos acá. Devuelve mediana "
            "y rango de USD/m², un valor de referencia ajustado (publicación→cierre y "
            "ajuste por diferencias), nivel de confianza por dispersión, y el valor "
            "estimado total si das m2_objetivo. Presentá SIEMPRE un rango con fuentes "
            "y fecha, no un número puntual."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "comparables": {
                    "type": "array",
                    "description": "Lista de USD/m² (números) o de {precio_total, m2}.",
                    "items": {"type": ["number", "object"]},
                },
                "m2_objetivo": {"type": "number", "description": "m² del inmueble a valuar (para el valor total)."},
                "descuento_publicacion_pct": {"type": "number", "description": "Ajuste publicación→cierre en % a descontar (ej 8 = -8%)."},
                "ajuste_pct": {"type": "number", "description": "Ajuste por diferencias del inmueble vs comparables (+ mejor, - peor)."},
            },
            "required": ["comparables"],
        },
    },
    {
        "name": "valor_residual_terreno",
        "description": (
            "Cuánto se puede pagar como MÁXIMO por un terreno para lograr una "
            "utilidad objetivo, dado el producto terminado (residual = ingresos − "
            "obra − gastos − comisiones − utilidad objetivo). Devuelve el valor "
            "residual del terreno y la incidencia por m² vendible y por m² de "
            "terreno. La tool clave para decidir la compra de suelo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "precio_venta_m2": {"type": "number", "description": "USD/m² vendible del producto terminado."},
                "costo_construccion_m2": {"type": "number", "description": "USD/m² construible (costo de obra)."},
                "m2_vendibles": {"type": "number", "description": "m² vendibles (o usá superficie_terreno_m2 + fot)."},
                "superficie_terreno_m2": {"type": "number", "description": "Superficie del terreno."},
                "fot": {"type": "number", "description": "FOT (m² construibles = terreno × FOT)."},
                "factor_vendible": {"type": "number", "description": "Eficiencia vendible/construible (default 0.85)."},
                "gastos_generales_pct": {"type": "number", "description": "Gastos generales en % (base según gastos_base)."},
                "gastos_base": {"type": "string", "enum": ["obra", "ventas"], "default": "obra"},
                "comisiones_pct": {"type": "number", "description": "Comisión de venta en % sobre ingresos."},
                "utilidad_objetivo_pct": {"type": "number", "description": "Utilidad objetivo en % sobre ventas (ej 20)."},
            },
            "required": ["precio_venta_m2", "costo_construccion_m2"],
        },
    },
    {
        "name": "calcular_iva",
        "description": (
            "Convierte entre neto y bruto de IVA. modo='extraer': el monto es BRUTO "
            "(con IVA) y devuelve el neto + IVA contenido. modo='agregar': el monto "
            "es NETO y le suma el IVA. alícuota default 21% (general); en obra puede "
            "aplicar 10,5%."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "monto": {"type": "number", "description": "Importe a procesar."},
                "alicuota_pct": {"type": "number", "description": "IVA en % (default 21)."},
                "modo": {"type": "string", "enum": ["extraer", "agregar"], "default": "extraer"},
            },
            "required": ["monto"],
        },
    },
    {
        "name": "calcular_sellos",
        "description": (
            "Impuesto de Sellos de una compraventa: base = máx(precio, valuación "
            "fiscal) × alícuota, repartido entre comprador y vendedor. OJO: la "
            "alícuota varía por jurisdicción; pasá alicuota_pct con la vigente de la "
            "provincia/CABA. Soporta exención por vivienda única con tope."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "monto": {"type": "number", "description": "Valor de la operación."},
                "valuacion_fiscal": {"type": "number", "description": "Valuación fiscal (la base es el mayor entre esta y el precio)."},
                "alicuota_pct": {"type": "number", "description": "Alícuota plana de Sellos en % (ej CABA ~3.6 total). Usá tramos si la tasa cambia por monto."},
                "tramos": {
                    "type": "array",
                    "description": "Alícuotas escalonadas por monto: [{\"hasta\": 226100000, \"alicuota_pct\": 2.7}, {\"hasta\": null, \"alicuota_pct\": 3.5}]. La base y los topes deben estar en la misma moneda (convertí USD→ARS si hace falta).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "hasta": {"type": ["number", "null"], "description": "Tope superior del tramo (null = sin tope)."},
                            "alicuota_pct": {"type": "number"},
                        },
                    },
                },
                "jurisdiccion": {"type": "string", "description": "Provincia/CABA, para el detalle."},
                "reparto": {"type": "string", "enum": ["ambos", "comprador", "vendedor"], "default": "ambos"},
                "vivienda_unica": {"type": "boolean", "description": "Si es vivienda única (puede haber exención)."},
                "tope_exencion": {"type": "number", "description": "Tope de valor para la exención de vivienda única."},
            },
            "required": ["monto"],
        },
    },
    {
        "name": "calcular_impuesto_transferencia",
        "description": (
            "Impuesto NACIONAL del VENDEDOR persona física al transferir un inmueble. "
            "El ITI fue DEROGADO (Ley 27.743, desde 8/7/2024). Hoy: si lo adquirió "
            "ANTES de 2018 → $0 nacional (ni ITI ni cedular); si lo adquirió DESDE "
            "2018 → Ganancias cedular 15% sobre la ganancia. No incluye sellos, "
            "escribanía ni comisión. Si no se sabe la fecha, devuelve ambos escenarios."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "precio_venta": {"type": "number", "description": "Precio de venta del inmueble."},
                "costo_adquisicion": {"type": "number", "description": "Costo de compra (para la ganancia, si aplica cedular)."},
                "adquirido_post_2018": {"type": "boolean", "description": "true si se adquirió desde 2018 (cedular), false si antes (sin impuesto nacional)."},
                "alicuota_ganancias_pct": {"type": "number", "description": "Alícuota Ganancias cedular en % (default 15)."},
            },
            "required": ["precio_venta"],
        },
    },
]


# ════════════════════════════════════════════════════════════════════
# Dispatcher
# ════════════════════════════════════════════════════════════════════
CALCULATOR_TOOL_IMPLS = {
    "analizar_inversion": _tool_analizar_inversion,
    "factibilidad_rapida": _tool_factibilidad_rapida,
    "tasacion_comparables": _tool_tasacion_comparables,
    "valor_residual_terreno": _tool_valor_residual_terreno,
    "calcular_iva": _tool_calcular_iva,
    "calcular_sellos": _tool_calcular_sellos,
    "calcular_impuesto_transferencia": _tool_calcular_impuesto_transferencia,
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
