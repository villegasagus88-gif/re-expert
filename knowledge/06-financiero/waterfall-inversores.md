---
title: "Waterfall de distribución a inversores (GP/LP, pref, catch-up, carried)"
topic: "financiero"
subtopic: "waterfall"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [waterfall, gp, lp, sponsor, inversor, preferred return, pref, catch up, carried interest, promote, hurdle rate, distribucion]
audience: ["developer", "inversor", "chat"]
confidence: "alta"
---

# Waterfall de distribución a inversores

## TL;DR
- **Waterfall** = estructura de cómo se reparten los flujos del proyecto entre **GP** (sponsor / developer) y **LP** (inversores).
- Componentes típicos: **return of capital → preferred return → catch-up → carried interest (promote)**.
- Bien diseñado, alinea incentivos: el GP gana proporcionalmente más solo si supera un hurdle (TIR mínima al LP).

## 1. Actores

### 1.1 GP — General Partner / Sponsor / Developer
- Lidera el proyecto.
- Aporta know-how + estructura + parte del equity (típico 5-20%).
- Recibe management fees + promote.

### 1.2 LP — Limited Partners / Inversores
- Aportan la mayoría del equity (80-95%).
- Responsabilidad limitada a su aporte.
- Reciben distribuciones según waterfall.

### 1.3 Vehículos AR
- Fideicomiso al costo (común en pozo).
- Fideicomiso financiero.
- SA / SAS para proyectos cerrados.
- FCI cerrado inmobiliario (ver `./fci-inmobiliarios.md`).

## 2. Componentes del waterfall

### 2.1 Tier 1 — Return of Capital (RoC)
- 100% de las distribuciones van a los LPs hasta que recuperen su capital aportado.
- A veces incluye GP también pro-rata.

### 2.2 Tier 2 — Preferred Return (pref)
- LPs reciben hasta una **tasa mínima** (hurdle) antes de que el GP cobre promote.
- Rangos AR típicos: **8-12% USD anual** (real estate).
- Puede ser acumulativo / compuesto.

### 2.3 Tier 3 — Catch-up
- Después del pref, el GP "alcanza" su porcentaje.
- Estructuras típicas: 50/50 o 100% al GP hasta que llegue a la proporción objetivo.

### 2.4 Tier 4 — Carried Interest / Promote
- Una vez cubiertos los anteriores, el exceso se reparte en proporción promote.
- Rangos típicos: **80% LP / 20% GP** o **70/30**.
- Estructuras escalonadas: más promote al GP a partir de hurdles más altos (waterfall escalonado).

## 3. Ejemplo numérico (simplificado USD)

### 3.1 Capital
- LP aporta 9 MUSD (90%).
- GP aporta 1 MUSD (10%).
- Total equity: 10 MUSD.

### 3.2 Resultado del proyecto
- Distribuciones totales al cabo de 3 años: 17 MUSD.

### 3.3 Waterfall
- Tier 1 RoC: 10 MUSD devueltos pro-rata (LP 9, GP 1).
- Quedan: 7 MUSD para distribuir.

### 3.4 Pref 10% anual al LP
- LP había aportado 9 MUSD → pref acumulado ~ 9 × 0.10 × 3 = 2.7 MUSD.
- Tier 2: 2.7 MUSD al LP.
- Quedan: 4.3 MUSD.

### 3.5 Catch-up + carried 80/20
- Tier 3 catch-up al GP hasta lograr proporción 80/20 sobre las ganancias.
- Tier 4 reparto 80/20.

### 3.6 Resultado final orientativo
- LP: ~13.4 MUSD (9 + 2.7 + 80% × 2.2 con catch-up + reparto) → TIR ~14%.
- GP: ~3.6 MUSD (1 + catch-up + promote) → TIR muy superior si superó el hurdle.

> Cifras orientativas; el cálculo exacto depende de la fórmula precisa de catch-up.

## 4. Tipos de waterfall

### 4.1 Europeo (whole-of-fund)
- Se calcula sobre el total del fondo / proyecto.
- LP recupera **todo** su capital + pref antes de que GP cobre promote.
- Más conservador (favorece LP).

### 4.2 Americano (deal-by-deal)
- Se calcula por proyecto individual.
- GP puede cobrar promote por un proyecto bueno aunque otros pierdan.
- Más agresivo (favorece GP).
- Suele tener **clawback** (devolución si el final del fondo no cumple pref).

### 4.3 Escalonado (tiered)
- Múltiples hurdles con promote creciente.
  - Hasta TIR 10% → 80/20.
  - 10-15% → 70/30.
  - >15% → 60/40 o 50/50.
- Incentivo fuerte al GP para superar hurdles altos.

## 5. Management fees (GP)

### 5.1 Tipos
- **Asset management fee**: 1-2% anual sobre AUM (capital comprometido).
- **Acquisition fee**: 0.5-1.5% sobre adquisición.
- **Construction management fee**: 2-4% sobre hard cost.
- **Disposition fee**: 0.5-1% sobre venta.

### 5.2 Tensión
- Fees altos → GP gana aunque proyecto sea mediocre.
- LPs sofisticados: prefieren menos fees + más promote (alineación).

## 6. Cláusulas críticas para LP

### 6.1 Clawback
- Si al final del fondo el LP no recibió su pref, el GP devuelve promote ya cobrado.

### 6.2 Hurdle real (no nominal)
- En contexto AR con inflación, definir pref en **USD** o en moneda dura.

### 6.3 Vetos / mayorías especiales
- Para decisiones materiales (cambio de alcance, venta anticipada, refinanciación).

### 6.4 Reporting
- Estados mensuales / trimestrales.
- Auditor independiente.

### 6.5 Salida
- Plazo del fondo.
- Mecanismo de venta forzosa al final.

## 7. Práctica AR

### 7.1 Fideicomiso al costo (pozo)
- Inversores aportan en cuotas.
- "Devolución" en m².
- No siempre tiene waterfall formal pero sí estructura de gain sharing.

### 7.2 Vehículos sofisticados
- Fideicomiso financiero (CNV).
- SA con accionistas Clase A (GP) y B (LP).
- FCI cerrados (CNV) — ver `./fci-inmobiliarios.md`.

### 7.3 Renta (BTR)
- Distribuciones periódicas + venta final.
- Waterfall puede ser distinto para renta vs venta de activos.

## 8. Errores comunes

- Diseñar waterfall sin sensibilizar escenarios (puede dar 0 al GP en escenarios medios).
- Definir pref en pesos sin proteger inflación.
- No prever clawback en deal-by-deal.
- Comprometer demasiados fees al GP → LP pierde apetito.
- No documentar formalmente (acuerdo de palabra).

## 9. Reglas operativas para el chat

- **Estable:** estructura de waterfall, conceptos, alineación de incentivos.
- **🔴 Volátil:** % específicos por proyecto, mercado de capitales AR.
- **Sensible:** todo waterfall lo modela un asesor financiero + abogado. Chat NO diseña waterfall vinculante.
- Si el usuario pregunta "¿cuánto cobra el GP?", responder: depende de pref + promote + fees; pedir parámetros para modelar.

## Ver también
- `./estructura-capital.md`
- `./tir-van.md`
- `./fci-inmobiliarios.md`
- `../10-figuras-juridicas/fideicomiso.md`
- `../15-teoria-developer/`
