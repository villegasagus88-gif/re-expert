---
title: "Apalancamiento — efecto leverage en real estate"
topic: "financiero"
subtopic: "apalancamiento"
jurisdiction: "Universal"
last_verified: "2026-05-10"
sources:
  - "Brealey, Myers, Allen — Corporate Finance"
  - "Damodaran — Investment Valuation"
keywords: [apalancamiento, leverage, deuda, equity, ROE, riesgo financiero, LTV, LTC, DSCR]
audience: ["developer", "inversor", "financiero"]
confidence: "alta"
---

# Apalancamiento

## TL;DR
- Apalancamiento = uso de deuda para amplificar el retorno del equity.
- **Si TIR del proyecto > costo de la deuda** → apalancar mejora la TIR del equity.
- **Si TIR < costo de deuda** → apalancar destruye valor más rápido (efecto inverso).
- Métricas clave: **LTV** (loan-to-value), **LTC** (loan-to-cost), **DSCR** (debt service coverage ratio).

---

## 1. Concepto básico

### 1.1 Idea
- Si un proyecto cuesta USD 10M y rinde 20%, todo financiado con equity:
  - TIR del equity = 20%.
- Si financio USD 5M con deuda al 10% y USD 5M con equity:
  - Resultado total: 20% sobre 10M = 2M.
  - Costo deuda: 10% sobre 5M = 0.5M.
  - Retorno equity: 1.5M sobre 5M = **30%**.
- El apalancamiento sube la TIR del equity de 20% a 30%.

### 1.2 Pero...
- Si el proyecto rinde 5% y la deuda cuesta 10%:
  - Resultado total: 5% sobre 10M = 0.5M.
  - Costo deuda: 10% sobre 5M = 0.5M.
  - Retorno equity: 0% sobre 5M = **0%**.
- Apalancar destruyó retorno.

### 1.3 Regla
$$ TIR_{\text{equity}} = TIR_{\text{proyecto}} + \frac{D}{E}(TIR_{\text{proyecto}} - K_d) $$

Donde D/E = ratio deuda/equity y K_d = costo de la deuda.

---

## 2. Métricas de apalancamiento

### 2.1 LTV (Loan-to-Value)
$$ LTV = \frac{\text{Deuda}}{\text{Valor del activo}} $$

- Conservador: 50-60%.
- Agresivo: 70-80%.
- Crítico: 80%+.

### 2.2 LTC (Loan-to-Cost)
$$ LTC = \frac{\text{Deuda}}{\text{Costo total del proyecto}} $$

- Más relevante para proyectos en construcción.
- Bancos suelen exigir LTC máximo 60-70%.

### 2.3 DSCR (Debt Service Coverage Ratio)
$$ DSCR = \frac{NOI}{\text{Servicio de deuda}} $$

- NOI = Ingreso operativo neto.
- DSCR > 1.25 → confortable.
- DSCR < 1 → no alcanza el flujo para servir la deuda.

### 2.4 Debt Yield
$$ DY = \frac{NOI}{\text{Deuda}} $$

- Rendimiento de la deuda independiente del valor.
- Bancos exigen 8-12% típicamente.

---

## 3. Riesgos del apalancamiento

### 3.1 Sensibilidad ampliada
- Pequeñas caídas en el valor del activo o el precio de venta golpean fuerte el equity.
- Ejemplo: con LTV 80%, una caída del 10% en el activo elimina el 50% del equity.

### 3.2 Riesgo de liquidez
- Servicio de deuda mensual (intereses + amortización) requiere caja.
- Si la preventa se demora o el alquiler cae → default.

### 3.3 Riesgo de refinanciación
- Si la deuda vence y no se puede renovar → problemas.
- Especialmente en contextos de tasas altas o crisis.

### 3.4 Riesgo cambiario
- Deuda en USD + ingresos en pesos = bomba.
- Caso típico AR.

---

## 4. Apalancamiento operativo vs financiero

### 4.1 Operativo
- Sensibilidad del resultado operativo a la variación de ingresos.
- Costos fijos altos → más apalancamiento operativo → más riesgo.

### 4.2 Financiero
- Uso de deuda.
- Costos financieros fijos (intereses).

### 4.3 Total
- Combinación de ambos.
- Real estate típicamente tiene apalancamiento operativo medio (algunos costos fijos: gerencia, impuestos, mantenimiento) y financiero variable según estructura.

---

## 5. Apalancamiento en distintos modelos

### 5.1 Desarrollo al costo
- Apalancamiento bajo o nulo.
- Riesgo distribuido entre fiduciantes-beneficiarios.

### 5.2 Desarrollo a precio cerrado
- Apalancamiento medio (40-60% LTC).
- Mezcla de equity + preventa + crédito.

### 5.3 Renta (residencial alquiler / oficinas)
- Apalancamiento alto sobre activos estabilizados (60-75% LTV).
- Justificado por flujo previsible.

### 5.4 Build to rent / build to suit
- Apalancamiento variable; en construcción más bajo, una vez estabilizado se puede subir refinanciando.

---

## 6. Ratios y covenants típicos

### 6.1 Bancos AR (cuando hay crédito constructor disponible)
- LTC máximo 60-70%.
- DSCR mínimo 1.20-1.30.
- Velocidad de venta mínima.
- Restricción a distribuir dividendos antes de cancelar deuda.

### 6.2 Mercado de capitales
- Covenants de mantener cierto patrimonio.
- Cross-default con otras deudas.
- Limitación de endeudamiento adicional.

---

## 7. Optimización del nivel de apalancamiento

### 7.1 Trade-off
- Más deuda → mayor TIR del equity esperada **pero** mayor riesgo (volatilidad y default).
- Más equity → menor TIR pero más resiliencia.

### 7.2 Heurística
- Buscar LTC tal que DSCR > 1.25 incluso en escenario pesimista.
- Mantener buffer de equity para llamadas de capital imprevistas.
- Evitar mismatch de moneda.

### 7.3 Apetito por riesgo
- Inversor agresivo: mayor apalancamiento.
- Inversor conservador / family office: equity más alto.

---

## 8. Errores comunes

- Apalancarse al máximo en proyectos con flujos volátiles.
- Asumir refinanciación automática.
- Ignorar covenants y tropezar con ellos.
- Apalancarse en USD con ingresos en pesos.
- Usar crédito constructor para gastos no previstos en el desembolso pactado.
- Ignorar el efecto de las garantías personales.

---

## 9. Reglas operativas para el chat

- **Estable y respondible:** concepto, fórmulas, ratios, cuándo amplifica vs destruye, riesgos asociados.
- **🟡 Semivolátil:** rangos típicos por modelo de negocio.
- **🔴 Volátil:** tasas y condiciones del mercado de crédito → consultar.
- **🔴 Caso particular:** estructuración óptima para un proyecto → financiero.

---

**Ver también:**
- `./tir-van.md`
- `./cashflow-real-estate.md`
- `./financiamiento.md`
- `./sensibilidad.md`
- `./metricas-developer.md`
