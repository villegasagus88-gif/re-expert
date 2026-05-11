---
title: "Índices de costo de la construcción (ICC, CAC, IPC, UVA, USD)"
topic: "costos-presupuesto"
subtopic: "indices"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "INDEC — ICC"
  - "Cámara Argentina de la Construcción (CAC)"
  - "BCRA — UVA, USD"
keywords: [icc, indec, cac, indice costo construccion, uva, ipc, inflacion, fx, dolar, redeterminacion, ajuste]
audience: ["developer", "constructor", "PM", "chat"]
confidence: "alta"
---

# Índices de costo

## TL;DR
- **ICC INDEC** y **CAC** son los dos índices de referencia para costo de construcción en AR.
- En obras > 6 meses, los contratos suelen incluir **cláusula de redeterminación** indexada (CAC, ICC, UVA o canasta).
- Para developers que venden en USD: monitorear **costo en USD** (ICC en pesos / FX) → señal de competitividad.

## 1. ICC — Índice del Costo de la Construcción (INDEC)

### 1.1 Qué mide
- Variación mensual del costo de construcción de un edificio modelo (vivienda multifamiliar 6 plantas en CABA).
- Tres capítulos: **Materiales, Mano de obra, Gastos generales**.

### 1.2 Publicación
- Mensual por INDEC.
- Apertura: ICC general + cada capítulo.

### 1.3 Uso
- Indexar contratos.
- Comparar evolución del costo en pesos vs inflación general (IPC).
- Análisis sectorial.

## 2. CAC — Cámara Argentina de la Construcción

### 2.1 Qué publica
- Índices propios de costo (similar al ICC pero con metodología CAC).
- Estudios de costos por rubro.
- Tabla de jornales y aportes.

### 2.2 Uso
- Referencia para contratos privados.
- Más cercano al "costo real" del sector según la cámara.

## 3. IPC — Índice de Precios al Consumidor

### 3.1 Qué mide
- Inflación general (canasta de consumo).
- No es índice de construcción, pero es referencia macro.

### 3.2 Relación con costo de obra
- IPC ≠ ICC: pueden diverger.
- En AR los precios de materiales (sobre todo importados) suelen subir más que IPC.
- Mano de obra (paritarias) sigue IPC con retraso.

## 4. UVA — Unidad de Valor Adquisitivo

### 4.1 Qué es
- Unidad indexada al IPC, creada por BCRA.
- Valor: cotización diaria.
- Permite contratos en "moneda constante".

### 4.2 Uso en construcción
- Créditos hipotecarios UVA (Banco Hipotecario, BNA).
- Algunos contratos de obra y compraventa.

### 4.3 Riesgos
- Si salario no sigue inflación → estrés de cuotas (caso 2018-2024).
- Salida UVA: refinanciaciones, fideicomisos colchón.

## 5. USD — dólar estadounidense

### 5.1 Tipos de USD relevantes
- **USD oficial / mayorista** (BCRA, MULC).
- **USD MEP / bolsa** (CCL Cable, MEP).
- **USD blue** (informal).
- **USD tarjeta / turista** (mayorista + percepciones).

### 5.2 En real estate AR
- Precios de venta de inmuebles: USD (en MEP o blue según mercado).
- Costos en pesos pero materiales importados ligados a USD oficial.
- Brecha cambiaria impacta márgenes.

### 5.3 Costo en USD del m²
- Indicador de competitividad sectorial.
- Calculado: costo ARS / FX MEP.
- Rango histórico orientativo AMBA: 600-1.200 USD/m² para hard cost residencial estándar.
- 🔴 Sumamente volátil, dependiente de FX.

## 6. Redeterminación de precios

### 6.1 Concepto
- Mecanismo contractual para actualizar el precio de la obra ante cambios significativos de costos.

### 6.2 Obra pública (Decreto 691/16 + Ley 13.064)
- Fórmula polinómica de redeterminación.
- Componentes ponderados (materiales, MO, equipos).
- Umbral típico: variación > 5% activa redeterminación.

### 6.3 Obra privada
- Cláusulas libres entre partes.
- Indexación por CAC, ICC, UVA, USD, o fórmula mixta.
- Período típico: trimestral o cada certificación.

### 6.4 Riesgo distribuido
- Sin redeterminación: constructor asume todo el riesgo.
- Con redeterminación: developer asume riesgo de costo.
- En AR alta inflación → casi siempre se redetermina.

## 7. Análisis de sensibilidad

### 7.1 Variables clave
- Inflación (IPC, ICC).
- FX (USD MEP).
- Tasa de interés (UVA, BADLAR).
- Brecha cambiaria.

### 7.2 Escenarios
- Optimista / base / pesimista.
- Stress test del proyecto.

### 7.3 Cobertura
- Acopio de materiales clave en pesos.
- Pre-venta en USD (cierra ingresos).
- Contratos en UVA o USD para insumos.

## 8. Tabla orientativa de pesos en CAC/ICC

| Capítulo | % aprox |
|---|---|
| Materiales | 40-50% |
| Mano de obra | 35-45% |
| Gastos generales | 8-15% |

> 🔴 Pondaraciones cambian con revisión de canasta.

## 9. Errores comunes

- Modelar el proyecto solo en pesos sin sensibilidad.
- Asumir que ICC y IPC son iguales (no lo son).
- No prever redeterminación en contratos largos.
- Confundir USD oficial con MEP en factibilidades.
- Olvidar que paritarias mueven costo MO.

## 10. Reglas operativas para el chat

- **Estable:** qué mide cada índice, mecánica de redeterminación.
- **🔴 Volátil:** valores específicos de ICC, CAC, IPC, UVA, USD → INDEC, CAC, BCRA, dólarhoy.
- **Sensible:** todo modelo definitivo lo arma profesional (PM financiero, contador, controller).
- Si el usuario pide "valor actual ICC", redirigir a INDEC.

## Ver también
- `./estructura-costos.md`
- `./control-presupuestario.md`
- `../00-macro-ar/inflacion-fx-tasas.md`
- `../06-financiero/hipoteca-uva.md`
