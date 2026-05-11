---
title: "Estructura de capital del proyecto (equity, deuda, mezzanine)"
topic: "financiero"
subtopic: "estructura-capital"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [estructura capital, equity, deuda senior, mezzanine, preferred equity, ltv, ltc, dscr, debt service, preventa, capital stack]
audience: ["developer", "inversor", "chat"]
confidence: "alta"
---

# Estructura de capital

## TL;DR
- **Capital stack** = composición de las fuentes que financian el proyecto: equity (riesgo, residual) + deuda (preferente, fija) + híbridos (mezzanine, preferred equity).
- En AR la **deuda bancaria a construcción es limitada** → mayoría se hace con equity + pre-venta en pozo.
- Métricas clave: **LTV** (loan-to-value), **LTC** (loan-to-cost), **DSCR** (debt service coverage ratio).

## 1. Capa por capa (stack)

### 1.1 Senior Debt (deuda senior)
- Hipoteca / crédito bancario.
- Garantía real (terreno + obra).
- Costo más bajo.
- LTV típico: 50-70%.
- Primera en cobrar en caso de problema.

### 1.2 Mezzanine
- Deuda subordinada al senior.
- Mayor costo (typicalmente senior + 3-7%).
- A veces convertible en equity.
- LTC adicional: hasta 75-85% combinado con senior.

### 1.3 Preferred Equity
- Híbrido entre deuda y equity.
- Distribución preferente (no garantizada).
- Sin garantía real (más caro que mezzanine).

### 1.4 Equity (common)
- Capital residual.
- Última en cobrar.
- Captura todo el upside.
- Aportado por GP + LP.

## 2. Métricas clave

### 2.1 LTV — Loan to Value
- LTV = Deuda / Valor del activo terminado.
- Rangos AR: 40-60% (más conservador que mercados desarrollados).

### 2.2 LTC — Loan to Cost
- LTC = Deuda / Costo total del proyecto.
- Rangos AR: 50-70%.

### 2.3 DSCR — Debt Service Coverage Ratio
- DSCR = NOI / Servicio de deuda (capital + intereses).
- Requerido por bancos: > 1.20-1.40 según producto.
- En BTR / renta: clave para mantener el crédito.

### 2.4 Debt Yield
- Debt Yield = NOI / Deuda.
- Métrica conservadora (no depende del cap rate de salida).
- Bancos sofisticados: > 8-10%.

## 3. Fuentes de capital en AR

### 3.1 Equity propio
- Capital del developer + socios fundadores.
- Skin in the game obligatorio.

### 3.2 Inversores privados (LPs)
- High-net-worth, family offices, ex-clientes.
- Típicamente 60-90% del equity.

### 3.3 Pre-venta en pozo
- Función principal: financiar la obra.
- Compradores pagan en cuotas durante construcción.
- 30-50% del total del proyecto en proyectos exitosos.

### 3.4 Crédito bancario
- Banco Hipotecario (UVA), BNA, Galicia, Santander, Macro.
- A construcción: oferta limitada en AR.
- A comprador final: créditos hipotecarios UVA (ver `./hipoteca-uva.md`).

### 3.5 ON / Obligaciones negociables
- Para grandes developers (IRSA, Consultatio, TGLT).
- Régimen CNV.

### 3.6 FCI cerrados inmobiliarios
- Vehículo CNV regulado.
- Ver `./fci-inmobiliarios.md`.

### 3.7 Fideicomiso al costo
- Mecanismo de pooling para pozo.
- Inversores aportan en cuotas → recibe m² al final.

### 3.8 Crowdfunding inmobiliario
- Plataformas (Crowdium, Sumar, etc.).
- Tickets bajos (USD 1.000+).
- Regulación CNV en evolución.

## 4. Ejemplo de capital stack (edificio AR USD 10M)

| Capa | % | Monto USD | Costo / TIR |
|---|---|---|---|
| Senior debt (banco) | 40% | 4M | 8-12% USD efectivo |
| Pre-venta pozo | 35% | 3.5M | costo: descuento ~25% del valor terminado |
| Equity LP | 20% | 2M | pref 10% + promote |
| Equity GP (sponsor) | 5% | 0.5M | promote |
| **Total** | **100%** | **10M** | |

> 🔴 Mix orientativo; en AR la deuda a construcción a veces es 0 y se compensa con más pre-venta + equity.

## 5. Trade-offs

### 5.1 Más deuda
- ✅ Mayor TIR equity (apalancamiento).
- ❌ Mayor riesgo en escenarios negativos.
- ❌ Restricciones (covenants).

### 5.2 Más pre-venta
- ✅ Financiación barata.
- ❌ Bloquea precio (no se beneficia de upside del mercado).
- ❌ Riesgo de retrocesión si compradores no cumplen.

### 5.3 Más equity
- ✅ Menor riesgo.
- ❌ Menor TIR del developer.

## 6. Apalancamiento óptimo

### 6.1 Concepto
- Más deuda multiplica retornos al equity, pero también las pérdidas.
- "Sweet spot": LTC que maximice TIR esperada ajustada por riesgo.

### 6.2 Stress test
- Probar el capital stack con: caída precio venta -20%, sobrecosto +15%, atraso +6m.
- Si rompe el covenant del banco o el pref del LP → demasiada deuda.

### 6.3 En AR
- Conservador por inflación + FX + falta de crédito.
- LTC 50-65% es común.

## 7. Refinanciación

### 7.1 Construction → permanent loan
- Al terminar la obra y estabilizar renta (BTR), se refinancia el crédito a construcción por hipoteca de largo plazo.
- En AR: poco desarrollado, pero hay líneas BNA / Banco Hipotecario.

### 7.2 Cash-out refinance
- En BTR: refinanciar con mayor LTV → liberar equity → invertir en nuevo proyecto.

## 8. Garantías

### 8.1 Hipoteca
- Sobre el inmueble.
- Inscripta en RPI.

### 8.2 Fianza personal del sponsor
- Bancos suelen pedirla en AR.
- Subjective recourse.

### 8.3 Cesión de derechos
- Boletos pre-venta cedidos al banco como garantía.
- Cash sweep.

### 8.4 Construction completion guarantee
- Garantía de terminación de la obra.

## 9. Errores comunes

- Sobreapalancar en mercado volátil.
- No prever fluctuaciones FX en deuda en USD.
- Comprometer pre-venta antes de tener financiamiento de obra cerrado.
- Olvidar covenants (DSCR, LTV) → cross-default.
- No tener back-up de capital (gap funding).

## 10. Reglas operativas para el chat

- **Estable:** conceptos, capas, métricas, trade-offs.
- **🔴 Volátil:** tasas vigentes, % de financiamiento disponible → bancos / CNV / asesor financiero.
- **Sensible:** todo capital stack lo arma asesor financiero + abogado. Chat NO arma estructura vinculante.
- Si el usuario pregunta "¿cuánto banco puedo conseguir?", redirigir a banco específico + estado del proyecto.

## Ver también
- `./waterfall-inversores.md`
- `./apalancamiento.md`
- `./hipoteca-uva.md`
- `./fci-inmobiliarios.md`
- `./financiamiento.md`
