# 06 — Financiero

Análisis financiero de proyectos: indicadores, modelos, financiamiento, control.

## Archivos previstos
- `indicadores-evaluacion.md` — TIR, VAN, payback, punto de equilibrio
- `modelo-financiero-template.md` — estructura del modelo (xlsx + memo)
- `cashflow-proyecto.md` — armado del flujo, periodicidad, ajustes
- `tasa-descuento-ar.md` — cómo se determina k en AR (premio país, riesgo proyecto)
- `fuentes-financiamiento.md` — equity, deuda, pre-venta, fideicomiso al costo, hipoteca, mezzanine
- `apalancamiento.md` — efecto en TIR equity + riesgo
- `analisis-sensibilidad.md` — escenarios + Monte Carlo cuando aplique
- `costo-de-capital.md` — propio vs. tomado, ajustes por dolarización

## Reglas
- Todo flujo en USD billete.
- Sensibilidades obligatorias: precio −10%, costo +10%, plazo +6m.
- Cuando se cite tasa de un banco/fondo: nombre + fecha.

## 🔴 Datos volátiles vs 🟢 estables

Aplican las reglas de `_meta/politica-datos.md`.

**🔴 Volátil:**
- Tasas activas y pasivas bancarias.
- Costo del crédito hipotecario (UVA, fija, variable).
- Riesgo país.
- Premio por riesgo Argentina sobre la tasa libre de riesgo.
- TIR objetivo "del mercado" (depende del ciclo).

**🟡 Semivolátil:**
- Umbrales típicos de TIR USD para "ir/no-ir" en AR (refrescar anual).
- Mix típico de financiación de un proyecto.

**🟢 Estable — respuesta directa:**
- Fórmulas: TIR, VAN, Payback, Cap Rate, ROI.
- Cómo armar un flujo de caja proyectado (estructura, períodos, supuestos).
- Cómo se construye una tasa de descuento (CAPM, WACC adaptado a AR).
- Análisis de sensibilidad y stress.
- Fuentes de financiamiento y sus trade-offs (equity, deuda, pre-venta, fideicomiso al costo, hipoteca).
- Apalancamiento y su efecto en TIR equity.
- Estructura del modelo financiero estándar.

**Para datos del día → enviar a:** BCRA (tasas), bancos (UVA hipotecario), fondos comunes (TIR de FCI), CNV (fideicomisos financieros vivos).
