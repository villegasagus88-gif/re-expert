---
title: "Análisis de sensibilidad y escenarios"
topic: "financiero"
subtopic: "sensibilidad"
jurisdiction: "Universal"
last_verified: "2026-05-10"
sources:
  - "Damodaran — Investment Valuation"
  - "Buenas prácticas de modelado financiero"
keywords: [sensibilidad, escenarios, montecarlo, tornado, what-if, riesgo]
audience: ["analista financiero", "developer", "inversor"]
confidence: "alta"
---

# Sensibilidad y escenarios

## TL;DR
- Tres herramientas escalonadas:
  1. **Sensibilidad univariada** (one-way): cambiar una variable, ver impacto.
  2. **Análisis bivariado** (two-way): dos variables a la vez (ej. precio venta x costo de obra).
  3. **Escenarios** (base/pesimista/optimista): conjunto coherente de variables.
- En proyectos grandes: simulación **Monte Carlo** con distribuciones por variable.
- Output deseado: **gráfico de tornado** que ranking las variables por impacto.

---

## 1. Sensibilidad univariada

### 1.1 Procedimiento
1. Fijar el caso base con todos los supuestos.
2. Variar **una** variable ±x% (ej. ±10%, ±20%).
3. Recalcular VAN, TIR, payback.
4. Repetir para cada variable relevante.

### 1.2 Variables clave en RE AR
- Precio de venta por m².
- Costo de obra por m².
- Velocidad de venta (UFs/mes).
- Tipo de cambio.
- Tasa de descuento.
- Plazo de obra.
- Costo de la tierra.

### 1.3 Output
- Tabla de impactos.
- Gráfico **tornado**: barras horizontales, ordenadas por amplitud del rango VAN, con la variable más sensible arriba.

---

## 2. Análisis bivariado

### 2.1 Tabla de doble entrada
- Variable A en filas, Variable B en columnas.
- Cada celda muestra el VAN o TIR resultante.

### 2.2 Casos típicos
- Precio venta x costo obra.
- Tipo de cambio x velocidad de venta.
- Tasa de descuento x plazo de obra.

### 2.3 Visualización
- Mapa de calor (heatmap) que destaca zonas de "VAN > 0" vs "VAN < 0".

---

## 3. Análisis de escenarios

### 3.1 Definir escenarios coherentes

**Base**
- Supuestos centrales realistas.

**Pesimista**
- Variables empeoran de manera correlacionada:
  - Precio venta -10%.
  - Costo obra +15%.
  - Velocidad venta -30%.
  - Plazo obra +6 meses.

**Optimista**
- Variables mejoran:
  - Precio venta +10%.
  - Costo obra -5%.
  - Velocidad venta +20%.

### 3.2 Por qué importa
- Variables suelen estar correlacionadas (recesión → bajan precios + se demora venta + sube costo en USD).
- La sensibilidad univariada subestima el riesgo conjunto.

### 3.3 Probabilidades subjetivas
- Asignar probabilidades a cada escenario (ej. 60% base, 25% pesimista, 15% optimista).
- VAN esperado = Σ (probabilidad x VAN del escenario).

---

## 4. Simulación Monte Carlo

### 4.1 Procedimiento
1. Asignar a cada variable una **distribución de probabilidad**:
   - Normal: media + desvío.
   - Triangular: mínimo, modal, máximo.
   - Uniforme: rango.
   - Histórica.
2. Definir **correlaciones** entre variables.
3. Simular N veces (típicamente 5.000-10.000).
4. Obtener distribución de VAN / TIR resultante.

### 4.2 Outputs
- Histograma de VAN.
- Probabilidad de VAN > 0.
- VAN al 5%, 50%, 95% (percentiles).
- Sensitivity rank (ej. spider chart).

### 4.3 Cuándo conviene
- Proyectos grandes (USD 10M+).
- Múltiples variables interactuando.
- Decisiones de Go / No-Go ante un consorcio de inversores.

### 4.4 Cuándo no
- Proyecto chico, pocas variables clave → sensibilidad simple es suficiente.

---

## 5. Análisis de break-even

### 5.1 Variables críticas
- ¿Hasta qué precio puedo bajar sin romper VAN > 0?
- ¿Cuánto puede subir el costo antes de destruir el proyecto?
- ¿Cuál es la velocidad mínima de venta tolerable?

### 5.2 Procedimiento
- Resolver inverso: fijar VAN = 0 y despejar la variable.

### 5.3 Uso
- Negociación con constructor (qué tope de costo aceptar).
- Negociación con tierra (qué precio máximo pagar).
- Discusión con ventas (precio mínimo).

---

## 6. Stress testing

### 6.1 Concepto
- Llevar variables a extremos plausibles (no necesariamente probabilísticos).
- Ver si el proyecto sobrevive financieramente.

### 6.2 Stress típicos en AR
- Devaluación 50% sin trasladar precios.
- Pause de ventas 6 meses.
- Aumento de costo de obra 30% sin redeterminación.
- Default de un comprador grande.

### 6.3 Resultado
- Identificar puntos de fractura: ¿se necesitan llamadas de capital?, ¿se vende stock?, ¿se reestructura deuda?

---

## 7. Errores comunes

- Sensibilizar variables irrelevantes (ej. pequeñas tasas) y no las críticas.
- Asumir variables independientes cuando están correlacionadas.
- No definir escenarios coherentes ("pesimista" con buenas ventas y mal costo).
- Reportar solo el caso base sin franja de incertidumbre.
- Confundir sensibilidad con riesgo (es solo una dimensión).
- No actualizar el análisis cuando cambian los supuestos.

---

## 8. Reglas operativas para el chat

- **Estable y respondible:** metodología, tipos de análisis, variables críticas, casos típicos en AR.
- **🟡 Semivolátil:** rangos de stress razonables (referenciar fecha).
- **🔴 Caso particular:** análisis de un proyecto concreto → analista + planilla.

---

**Ver también:**
- `./tir-van.md`
- `./cashflow-real-estate.md`
- `./apalancamiento.md`
- `../08-macro-argentina/escenarios.md` (TBD)
