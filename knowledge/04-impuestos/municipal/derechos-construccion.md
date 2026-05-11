---
title: "Derechos de construcción, delineación y demolición"
topic: "impuestos"
subtopic: "derechos-construccion"
jurisdiction: "Municipal"
last_verified: "2026-05-11"
sources:
  - "Código Fiscal CABA — AGIP"
  - "Códigos Fiscales municipales PBA"
  - "Ordenanzas tarifarias anuales por jurisdicción"
keywords: [derechos construccion, delineacion, visado planos, permiso obra, derechos demolicion, cum, capa, dgroc]
audience: ["desarrollador", "arquitecto", "chat"]
confidence: "alta"
---

# Derechos de construcción, delineación y demolición

## TL;DR
- Al presentar planos y pedir permiso de obra, el municipio cobra **derechos** vinculados al hecho urbanístico/edilicio.
- Tipos: **delineación** (línea oficial, retiros, perfil), **construcción** (m² a construir), **demolición** (m² a demoler), **visado de planos** (revisión técnica), **conexiones**.
- Suelen liquidarse al **otorgar el permiso** (parte) y al **final de obra** (saldo o ajuste).
- En CABA dependen de la **Dirección General de Registro de Obras y Catastro (DGROC)**.
- 🔴 Importes y alícuotas cambian anualmente — verificar ordenanza tarifaria.

## 1. Tipos de derechos

### 1.1 Derecho de delineación
- Verifica retiros, FOT, FOS, alineación con línea oficial.
- Suele ser un porcentaje del valor del terreno o un fijo por m².

### 1.2 Derecho de construcción (el más relevante por magnitud)
- Sobre la **superficie computable a construir**.
- Tarifa por m² + multiplicador por categoría/destino (residencial, comercial, industrial).
- Premios y descuentos en algunos códigos (sustentabilidad, vivienda asequible).

### 1.3 Derecho de demolición
- Sobre m² a demoler.
- En CABA y municipios consolidados, requiere permiso aparte.

### 1.4 Visado de planos
- Revisión técnica por el área profesional del municipio (DGROC en CABA).
- Pago al ingreso del expediente.

### 1.5 Conexiones de servicios
- Agua, cloaca, gas, energía → cada operador (AySA, ABSA, Edenor, Edesur, Metrogas, Litoral Gas, etc.) cobra su derecho.

### 1.6 Tasa de cartelería de obra
- En CABA y muchos municipios PBA, la cartelería de obra paga derecho de publicidad propio.

### 1.7 Otros conceptos puntuales
- Ocupación de calzada / vereda durante obra (vallado, andamios, contenedores).
- Cortes de tránsito.
- Bombas, grúas (instalación temporal).

## 2. Quién paga

- **Comitente** de la obra (developer / propietario del terreno).
- Puede trasladarse al constructor si el contrato lo prevé (raro).

## 3. Momento de pago

| Concepto | Momento |
|---|---|
| Visado | Al ingreso del expediente |
| Derecho de construcción (anticipo) | Al otorgar el permiso de obra |
| Saldo final | Al final de obra / certificación |
| Demolición | Al permiso de demolición |
| Conexiones | Al solicitar el alta a cada empresa de servicios |

## 4. Bonificaciones, exenciones y premios

- Construcción sostenible (LEED / EDGE / IRAM) → algunos municipios bonifican.
- Vivienda asequible → tratamientos preferenciales.
- Conservación patrimonial (APH en CABA) → exenciones específicas.
- Premios por reciclaje de cascos antiguos → CABA tiene incentivos.

> Ver detalle en cada jurisdicción.

## 5. CABA — referencia operativa

### 5.1 Autoridad
- **DGROC** (Dirección General de Registro de Obras y Catastro).
- AGIP recauda.

### 5.2 Trámites principales
- **Aviso de obra** (obras menores).
- **Permiso de obra** (construcción nueva, ampliación, refacción mayor).
- **Permiso de demolición**.
- **Conforme a obra** (final de obra y registro real construido).

### 5.3 Plataforma
- Mayoría de trámites por TAD CABA / DGROC.
- Profesional matriculado (arquitecto / ingeniero) presenta y firma.

## 6. PBA — variaciones por municipio

- Cada municipio define sus derechos. Pilar, Tigre, Vicente López, San Isidro, La Plata tienen montos significativamente distintos.
- Algunos municipios cobran un **derecho de aprobación de planos** separado del derecho de construcción.
- Revisar ordenanza tarifaria del año.

## 7. Cómo computar en presupuesto del proyecto

- Línea de **derechos municipales** típica: 1-3% del costo de obra (en CABA puede ser mayor según superficie y destino).
- Sumarse a:
  - Honorarios profesionales (8-15%).
  - Aportes profesionales (CPAU, CPIC, CAPBA).
  - Sellos (provincial, cuando aplique).
  - Conexiones de servicios.

## 8. Errores comunes

- Subestimar el costo de derechos por no leer la ordenanza tarifaria del año.
- No prever el saldo final al "conforme a obra".
- Olvidar las conexiones de servicios.
- No incluir la cartelería en el presupuesto.

## 9. Reglas operativas para el chat

- **Estable:** qué derechos existen, quién los paga, cuándo se pagan, cómo se computan en el presupuesto.
- **🔴 Volátil — derivar:**
  - Monto en pesos por m² del año → ordenanza tarifaria del municipio.
  - En CABA: AGIP / DGROC.
- Si la pregunta es "¿cuánto pago de permiso?", responder con metodología + pedir m², destino, jurisdicción + derivar.

## Ver también
- `./abl-tsg.md`
- `./tasas-municipales.md`
- `./contribuciones-y-plusvalia.md`
- `../../02-normativa/codigo-edificacion-caba.md`
- `../../05-construccion/documentacion-obra.md`
