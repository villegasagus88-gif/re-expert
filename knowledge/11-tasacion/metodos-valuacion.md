---
title: "Métodos de valuación inmobiliaria"
topic: "tasacion"
subtopic: "metodos"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "International Valuation Standards (IVS) — IVSC"
  - "Normas Argentinas de Valuación (NAV) — CPAU, TTU"
  - "Resolución CPAU 4/2015"
keywords: [metodo comparativo, metodo costo, metodo capitalizacion, valor mercado, valor reposicion, depreciacion, cap rate, valuacion, tasacion, ivs]
audience: ["tasador", "developer", "inversor", "chat"]
confidence: "alta"
---

# Métodos de valuación inmobiliaria

## TL;DR
- Tres métodos clásicos: **comparativo de mercado**, **costo de reposición**, **capitalización de renta**.
- Cada uno responde a una pregunta distinta: cuánto se paga por uno parecido / cuánto sale construirlo hoy / cuánto vale por lo que renta.
- En la práctica se aplica más de uno y se concilian resultados.
- Para suelo de desarrollo se usa además **método residual** (ver `./metodo-residual-suelo.md`).

## 1. Método comparativo de mercado (MAC)

### 1.1 Concepto
- Comparar el inmueble objeto con **transacciones recientes** de inmuebles similares en la misma zona.
- "Comparable book": tabla con operaciones cerradas + listados activos (con cuidado).

### 1.2 Cuándo aplicarlo
- Inmuebles con mercado activo y comparables disponibles.
- Departamentos en CABA: principal método.
- Lotes urbanos consolidados.
- Casas en barrios homogéneos.

### 1.3 Procedimiento
1. **Identificar comparables**: 3-6 operaciones de los últimos 6-12 meses, misma zona, similar tipología/superficie/antigüedad.
2. **Ajustes** por diferencias: ubicación, superficie, estado, amenities, orientación, planta.
3. **Promedio ponderado** + análisis de dispersión.
4. Valor por m² → multiplicar por m² del inmueble objeto.

### 1.4 Limitaciones
- Mercados ilíquidos sin comparables.
- Inmuebles únicos (premium, atípicos).
- Cierres reales son difíciles de conseguir (los listados no son cierres).

### 1.5 Fuentes
- Colegio de Escribanos (operaciones inscriptas, sin precio explícito pero con datos).
- Tasadores que comparten información sectorial.
- Portales para listados (precaución: son ofertas, no cierres).
- Bases internas de inmobiliarias.

## 2. Método del costo (de reposición)

### 2.1 Concepto
- Valor del inmueble = valor del terreno + costo de reposición de la construcción a nuevo − depreciación.
- Responde: ¿cuánto costaría hoy hacer uno igual?

### 2.2 Cuándo aplicarlo
- Inmuebles únicos sin comparables (industrias, hospitales, complejos especiales).
- Inmuebles nuevos.
- Para valuación contable / seguro.
- Como cross-check de otros métodos.

### 2.3 Procedimiento
1. Valuar el **terreno** por método comparativo.
2. Calcular **costo de reposición** de la construcción a nuevo:
   - Costo por m² actualizado (ICC INDEC, índices CAC).
   - Multiplicar por m² del edificio.
3. Aplicar **depreciación**:
   - Por edad.
   - Por estado de conservación.
   - Por obsolescencia funcional o económica.
4. Sumar: valor terreno + (costo reposición − depreciación) = valor del inmueble.

### 2.4 Depreciación — métodos
- **Lineal**: vida útil estándar (50-70 años residencial), edad / vida.
- **Ross**: ajusta por estado de conservación.
- **Heidecke**: combinación de edad y estado.
- **Ross-Heidecke** (más usado): tabla de doble entrada.

### 2.5 Limitaciones
- En mercado AR, el valor de mercado suele ser MAYOR al costo de reposición → reflejar valor del suelo.
- En crisis, puede invertirse (valor mercado < costo reposición).

## 3. Método de capitalización de renta (DCF / cap rate)

### 3.1 Concepto
- Valor del inmueble = renta neta anual / tasa de capitalización (cap rate).
- Responde: ¿cuánto vale como activo generador de flujo?

### 3.2 Cuándo aplicarlo
- Inmuebles de renta (oficinas, locales, depósitos, hoteles, multifamily).
- Cuando la renta es estable y predecible.
- Para análisis de inversión.

### 3.3 Procedimiento

**Capitalización directa**
```
Valor = Renta neta anual / Cap rate
```
Donde:
- Renta neta = ingreso bruto − vacancia − gastos operativos (no recuperables).
- Cap rate = tasa que el mercado paga por activos similares.

**Flujo descontado (DCF)**
```
Valor = Σ [Flujo año t / (1+r)^t] + Valor terminal / (1+r)^n
```
Más sofisticado, considera evolución temporal.

### 3.4 Cap rate — referencias
- Ver `../01-mercado-argentino/benchmarks.md`.
- Rangos típicos por segmento (orden de magnitud histórico).
- Cap rate ≠ TIR; cap rate es solo el primer año.

### 3.5 Limitaciones
- Sensibilidad alta al cap rate elegido.
- Renta debe ser de mercado, no nominal de contrato (a veces hay alquiler bajo o sobre mercado).
- Vacancia y gastos operativos a estimar con realismo.

## 4. Conciliación entre métodos

- Buen tasador aplica **al menos dos métodos** y los concilia.
- Si difieren mucho → revisar premisas.
- Ponderar según calidad del dato y propósito de la tasación.

| Propósito | Método principal |
|---|---|
| Compraventa residencial | Comparativo |
| Inversión de renta | Capitalización |
| Valuación contable / seguro | Costo |
| Desarrollo (suelo) | Residual (ver archivo dedicado) |
| Expropiación | Conciliación de los tres (TTN) |

## 5. Errores comunes

- Usar listados como si fueran cierres.
- Olvidar ajustar por inflación y tipo de cambio (especialmente cuando se mezclan datos USD/ARS).
- No depreciar por obsolescencia funcional (planta vieja, distribución mala).
- Aplicar cap rate de un segmento a otro.
- Tasar suelo solo por comparable, sin contrastar con residual.

## 6. Reglas operativas para el chat

- **Estable:** definición de cada método, cuándo aplicarlo, fórmulas básicas.
- **🔴 Volátil:** valor m² real, cap rate vigente — derivar a fuentes y tasador.
- **Sensible:** tasación formal solo profesional matriculado.
- Si la pregunta es "¿cuánto vale?", responder con metodología + pedir datos + derivar a tasador.

## Ver también
- `./metodo-residual-suelo.md`
- `./normas-profesionales.md`
- `../01-mercado-argentino/benchmarks.md`
- `../06-financiero/tir-van.md`
