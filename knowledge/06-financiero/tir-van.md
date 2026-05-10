---
title: "TIR y VAN — métricas de evaluación financiera"
topic: "financiero"
subtopic: "tir-van"
jurisdiction: "Universal (aplicable AR)"
last_verified: "2026-05-10"
sources:
  - "Brealey, Myers, Allen — Principles of Corporate Finance"
  - "Damodaran — Investment Valuation"
  - "Práctica de mercado real estate AR"
keywords: [TIR, VAN, IRR, NPV, tasa descuento, payback, WACC, real estate, decision]
audience: ["developer", "inversor", "analista financiero"]
confidence: "alta"
---

# TIR y VAN

## TL;DR
- **VAN (Valor Actual Neto / NPV)**: suma de flujos descontados al momento cero. Decisión: aceptar si VAN > 0.
- **TIR (Tasa Interna de Retorno / IRR)**: tasa de descuento que hace VAN = 0. Decisión: aceptar si TIR > tasa de corte.
- En real estate AR: ambas se calculan **en USD** o en **moneda dura** para neutralizar inflación.
- Complementarias, no sustitutas: VAN mide riqueza absoluta; TIR mide rentabilidad relativa.

---

## 1. Valor Actual Neto (VAN)

### 1.1 Fórmula
$$ VAN = \sum_{t=0}^{n} \frac{F_t}{(1+r)^t} $$

Donde:
- F_t: flujo de caja del período t (negativo si egreso, positivo si ingreso).
- r: tasa de descuento (costo de oportunidad / WACC).
- n: cantidad de períodos.

### 1.2 Interpretación
- VAN > 0: el proyecto crea valor por encima del costo de oportunidad.
- VAN = 0: indiferente (rinde justo lo exigido).
- VAN < 0: destruye valor.

### 1.3 Sensibilidad
- Cambia con: tasa de descuento, plazo, magnitud y timing de flujos.
- En real estate: muy sensible al precio de venta y al timing de ingresos por preventa.

---

## 2. Tasa Interna de Retorno (TIR)

### 2.1 Concepto
- Tasa que iguala el VAN a cero.
- Representa el "rendimiento intrínseco" del proyecto.

### 2.2 Cálculo
- Iterativo (Excel: `=TIR()` o `=IRR()`).
- Requiere al menos un flujo negativo y uno positivo.

### 2.3 Decisión
- TIR > tasa de corte (hurdle rate) → aceptar.
- TIR < tasa de corte → rechazar.

### 2.4 Hurdle rate típico en RE AR
- 🔴 Volátil — depende del momento.
- En USD, a modo de referencia conceptual: rangos pre-2024 entre 12-18% para desarrollo medio; 20%+ para proyectos riesgosos o con apalancamiento alto. Verificar con mercado actual.

---

## 3. Limitaciones de la TIR

### 3.1 Múltiples TIRs
- Si los flujos cambian de signo varias veces, puede haber varias TIRs matemáticas.
- Solución: usar VAN o TIR Modificada.

### 3.2 Reinversión implícita
- TIR asume que los flujos intermedios se reinvierten a la propia TIR.
- Problemático cuando TIR es muy alta y no hay alternativas reales con esa rentabilidad.
- Solución: TIR Modificada (MIRR).

### 3.3 Escala
- TIR no captura el tamaño absoluto del proyecto.
- Un proyecto con TIR 30% sobre USD 100k puede valer menos que uno con TIR 18% sobre USD 5M.
- Por eso conviene mirar también VAN.

### 3.4 Comparación entre proyectos mutuamente excluyentes
- TIR puede dar el orden equivocado si los proyectos tienen escala o duración distinta.
- Reglas: usar VAN cuando hay conflicto.

---

## 4. TIR Modificada (MIRR)

### 4.1 Idea
- Asume que los flujos positivos se reinvierten a una tasa de reinversión realista (no a la TIR).
- Asume que los flujos negativos se financian a una tasa de financiamiento.

### 4.2 Fórmula
$$ MIRR = \left( \frac{FV(\text{positivos})}{|PV(\text{negativos})|} \right)^{1/n} - 1 $$

### 4.3 Cuándo conviene
- Proyectos con flujos cambiantes de signo.
- Cuando la TIR es muy distinta de la realidad de reinversión.

---

## 5. Tasa de descuento

### 5.1 Costo del capital propio (Ke)
- CAPM: $ K_e = R_f + \beta \cdot (R_m - R_f) + \text{riesgo país} $
- En AR: muy relevante el componente de riesgo país.

### 5.2 Costo de la deuda (Kd)
- Tasa efectiva post-impuesto.

### 5.3 WACC
- $ WACC = \frac{E}{V} K_e + \frac{D}{V} K_d (1-t) $
- Mezcla ponderada según estructura de capital.

### 5.4 Hurdle rate
- Tasa exigida por el inversor / accionista para autorizar un proyecto.
- Suele estar por encima del WACC para crear margen.

---

## 6. Aplicación al real estate

### 6.1 Estructura típica de flujos
- **Inicio**: compra de tierra (egreso grande).
- **Construcción**: egresos mensuales por certificación + impuestos + comercialización.
- **Pre-venta y venta**: ingresos progresivos.
- **Cierre**: gastos de escrituración + posventa.

### 6.2 Métricas habituales
- TIR del proyecto en USD.
- VAN del proyecto en USD a la tasa de corte del developer.
- Payback simple y descontado.
- Múltiplo de capital (Equity Multiple = total ingresos / total egresos del equity).
- Yield (margen) sobre ingresos totales.

### 6.3 Ajustes argentinos
- Descontar el efecto del tipo de cambio.
- Inflación local descontada con índice (CAC / IPC).
- Brechas cambiarias (oficial / MEP / blue) → asumir un tipo de cambio realista para la conversión.

---

## 7. Errores comunes

- Mezclar pesos nominales y dólares en un mismo cálculo.
- No incluir el costo de la tierra en t=0.
- No descontar la inflación cuando se trabaja en pesos.
- Tomar TIR aislada sin mirar plazo, escala y riesgo.
- Olvidar gastos comerciales y de estructura.
- Considerar todo el ingreso al cierre cuando hay preventa real con dinámica trimestral.

---

## 8. Reglas operativas para el chat

- **Estable y respondible:** definiciones, fórmulas, criterios de decisión, limitaciones, ajustes para AR.
- **🟡 Semivolátil:** rangos típicos de hurdle rate (referenciar fechas).
- **🔴 Caso particular:** evaluación de un proyecto específico → analista financiero + planilla con flujos detallados.

---

**Ver también:**
- `./cashflow-real-estate.md`
- `./sensibilidad.md`
- `./financiamiento.md`
- `./apalancamiento.md`
- `./metricas-developer.md`
