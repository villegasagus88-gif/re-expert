---
title: "Método residual para valuación de suelo de desarrollo"
topic: "tasacion"
subtopic: "metodo-residual"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "International Valuation Standards (IVS) — residual method"
  - "Normas Argentinas de Valuación (NAV)"
keywords: [metodo residual, valor suelo, valuacion suelo, desarrollo, developer, factibilidad, suelo creado, fot, valor terreno por proyecto]
audience: ["developer", "tasador", "inversor", "chat"]
confidence: "alta"
---

# Método residual — valor de suelo para desarrollo

## TL;DR
- **Valor del suelo = Ingreso bruto del proyecto − Todos los costos − Utilidad esperada del developer.**
- Es el método que un developer usa para definir **cuánto puede pagar** por un terreno y que el proyecto cierre.
- Es la inversa del análisis de factibilidad clásico.
- Sensibilísimo a: valor m² de venta, FOT/FOS, costos de construcción, plazos.
- 🔴 Inputs (valor m² venta, costo construcción) son **volátiles** — el método es **estable**.

## 1. Fórmula básica

```
Valor MAX del suelo = Ingreso bruto venta
                    − Costo construcción total (hard cost)
                    − Honorarios profesionales (8-15%)
                    − Indirectos + gerenciamiento (3-7%)
                    − Comercialización (3-5%)
                    − Impuestos (variable según estructura)
                    − Imprevistos (5-10%)
                    − Utilidad objetivo del developer (15-25%)
                    − Costo financiero (si se financia)
```

> El resultado es el máximo que un developer racional puede pagar por el suelo para que el proyecto le devuelva la utilidad objetivo.

## 2. Procedimiento paso a paso

### Paso 1 — Estudio urbanístico
- Verificar FOT, FOS, alturas, retiros.
- Calcular **m² construibles totales** = m² parcela × FOT.
- Aplicar índice de eficiencia → **m² vendibles** = m² construidos × 75-85%.

### Paso 2 — Mix de producto y pricing
- Definir mix de tipologías (1amb, 2amb, 3amb, etc.).
- Asignar valor m² por tipología (acorde a mercado de la zona).
- Calcular **ingreso bruto** = Σ (m² vendibles × precio m² por tipología).

### Paso 3 — Costos totales
- Hard cost (construcción): m² construidos × USD/m² (categoría + zona).
- Honorarios: 8-15% del hard cost.
- Indirectos: 3-7% sobre total.
- Comercialización: 3-5% sobre ingreso.
- Impuestos: depende de estructura (fideicomiso al costo vs SAS vs persona física).
- Imprevistos: 5-10%.

### Paso 4 — Utilidad esperada
- Definir target en función de:
  - Riesgo del proyecto.
  - Tiempo de inmovilización.
  - Costo de oportunidad.
- Típico AR: **15-25% sobre venta total**.

### Paso 5 — Aplicar fórmula
- Valor MAX suelo = Ingreso bruto − Costos − Utilidad.

### Paso 6 — Análisis de sensibilidad
- Variar:
  - Valor m² de venta (−10% / +10%).
  - Costo construcción (+10%).
  - Plazo (+6 meses).
  - Utilidad objetivo (−5%).
- Obtener **rango de valor del suelo** y no un único número.

## 3. Ejemplo numérico (ilustrativo, no operativo)

### 3.1 Datos
- Parcela: 500 m².
- FOT: 3.
- m² construibles: 1.500 m².
- Eficiencia 80% → 1.200 m² vendibles.
- Precio m² venta promedio: USD 3.000 (en pozo, USD MEP).
- Costo construcción: USD 1.200/m² × 1.500 m² = USD 1.800.000.

### 3.2 Cálculo

| Concepto | Valor (USD) |
|---|---|
| Ingreso bruto venta | 1.200 × 3.000 = 3.600.000 |
| Hard cost construcción | -1.800.000 |
| Honorarios (12%) | -216.000 |
| Indirectos (5%) | -180.000 |
| Comercialización (4%) | -144.000 |
| Impuestos (10%) | -360.000 |
| Imprevistos (7%) | -252.000 |
| Utilidad target (20%) | -720.000 |
| **Valor MAX del suelo** | **= -72.000** |

### 3.3 Lectura
- El proyecto **NO cierra** con estos números: ni siquiera puede pagarse el suelo.
- El developer debe:
  - Bajar el precio del suelo si negocia.
  - Subir el precio de venta (¿es posible en esa zona?).
  - Bajar costo de construcción (categoría menor).
  - Bajar utilidad target (¿asume más riesgo?).
  - Cambiar el producto (más m² vendibles).

> El método **expone con claridad la frontera de viabilidad**. Si no hay cómo pagar el suelo, no hay proyecto.

## 4. Variables sensibles

| Variable | Impacto típico |
|---|---|
| Precio m² venta | Altísimo (palanca dominante) |
| Costo construcción | Alto |
| FOT / m² vendibles | Alto (palanca urbanística) |
| Plazo de obra | Medio (inmoviliza capital) |
| Utilidad target | Medio-alto |
| Impuestos | Medio (cambia por estructura) |
| Honorarios | Bajo-medio |

## 5. Permuta y método residual

- Cuando se permuta suelo por UFs, el método residual ayuda a calcular **cuántas UFs equivalen** al valor del suelo.
- Tradeoff: el dueño del suelo recibe UFs (valor incierto, sin liquidez) en lugar de cash.
- Suele compensarse con un % adicional sobre el valor calculado por residual.
- Ver `../10-estrategia/permuta.md`.

## 6. Método residual vs método comparativo (suelo)

- **Comparativo de suelo**: precios de otros terrenos similares.
- **Residual**: derivado del proyecto factible.
- **Conciliación**:
  - Si comparativo > residual → suelo "caro" para desarrollo → buscar otros usos o esperar.
  - Si residual > comparativo → oportunidad (suelo "barato" si se cierra rápido).
- Buenos análisis usan **los dos**.

## 7. Errores comunes

- Usar valor m² venta optimista de la zona alta del rango.
- Subestimar costo de construcción (especialmente en USD cuando el ICC en ARS sube).
- No incluir impuestos según estructura fiscal.
- Olvidar imprevistos.
- Aplicar utilidad target baja para "que cierre" → falsa señal.
- No hacer sensibilidad → ver un único número.

## 8. Reglas operativas para el chat

- **Estable y muy respondible:** el método, las variables, la fórmula, la lógica de sensibilidad.
- **🔴 Volátil:** valor m² venta y costo construcción USD/m² → derivar al usuario para que aporte el dato actual.
- Si el usuario aporta los inputs, el chat puede correr el cálculo y dar rango + diagnóstico.
- Recordar: tasación formal de suelo para una transacción concreta → profesional matriculado.

## Ver también
- `./metodos-valuacion.md`
- `../00-fundamentos/analisis-factibilidad.md`
- `../06-financiero/tir-van.md`
- `../06-financiero/sensibilidad.md`
- `../10-estrategia/permuta.md`
