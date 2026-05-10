---
title: "Cashflow del proyecto inmobiliario"
topic: "financiero"
subtopic: "cashflow-real-estate"
jurisdiction: "Argentina"
last_verified: "2026-05-10"
sources:
  - "Práctica de mercado real estate AR"
  - "Cámara Argentina de Desarrolladores Urbanos"
  - "Damodaran — Valuation"
keywords: [cashflow, flujo de caja, curva s, certificacion, preventa, escrituracion, FCF, capex, opex]
audience: ["developer", "analista financiero", "fideicomiso"]
confidence: "alta"
---

# Cashflow del proyecto inmobiliario

## TL;DR
- El cashflow proyectado es la columna vertebral del modelo financiero.
- Tres bloques: **egresos** (tierra + construcción + estructura + impuestos), **ingresos** (preventa + posventa + escrituración), **financiación** (anticipos, créditos, equity).
- En real estate AR se modela típicamente **mensualmente**, en **USD** o con **dual currency** (ARS para costos locales, USD para ingresos) y conversión por tipo de cambio.
- La **curva S** describe el avance acumulado de obra y suele ser la base para distribuir egresos de construcción.

---

## 1. Estructura del cashflow

### 1.1 Egresos (outflows)

| Categoría | Detalle | Timing típico |
|---|---|---|
| Tierra | Compra del terreno + escrituración + sellos | t=0 (lump sum) |
| Permisos y proyecto | Honorarios profesionales, derechos, factibilidades | t=0 a t=6 |
| Construcción | Certificaciones mensuales según curva S | a lo largo de la obra (18-36 meses) |
| Estructura | Equipo developer, oficina, comercialización, marketing | continuo, mensual |
| Impuestos | IVA cuando aplique, IIBB, sellos, ABL, tasas | continuo |
| Comercialización | Comisiones (3-6% sobre ventas) | al cierre de cada venta |
| Posventa | Reservas para garantía decenal y posventa | tras la entrega |

### 1.2 Ingresos (inflows)

| Categoría | Detalle | Timing |
|---|---|---|
| Preventa | Anticipo + cuotas durante obra | desde t=0 a entrega |
| Pozo / pre-finalización | Cuotas, ajustes según índice | durante obra |
| Boleto y posesión | Pago al alcanzar el % comprometido | en el hito |
| Escrituración | Saldo final | al FO + posesión |
| Alquileres post-finalización | Si retiene UFs en cartera | después de FO |

### 1.3 Financiación

| Concepto | Cuándo aplica |
|---|---|
| Equity inicial | Aporte del developer / inversores | t=0 |
| Aporte del fiduciante (al costo) | Llamadas de capital periódicas | durante obra |
| Crédito puente | Para cubrir gap entre venta y certificación | cuando aplica |
| Crédito construcción | Banco / mercado de capitales | durante obra |
| Salida (exit) | Recompra, distribución de excedente | al cierre |

---

## 2. Curva S de obra

### 2.1 Concepto
- Distribución del avance físico (y, por ende, de los egresos de construcción) a lo largo del cronograma.
- Forma típica: S — lenta al principio (movimiento de suelos, fundaciones), acelerada en medio (estructura, mampostería), lenta al final (terminaciones).

### 2.2 Aproximación
- 0-20% del tiempo → 5-10% del costo.
- 20-70% → 60-70% del costo.
- 70-100% → 25-30% del costo.

### 2.3 Uso
- Distribuir el costo total entre los meses del cronograma.
- Alimentar el cashflow.
- Comparar avance real vs proyectado.

---

## 3. Curva de ventas

### 3.1 Modelos típicos

**Modelo "lanzamiento fuerte"**
- Pico de ventas en los primeros 3-6 meses (preventa con descuento).
- Cola larga durante obra.
- Ventaja: entrada de fondos temprana.

**Modelo "escalonado"**
- Ventas graduales.
- Descuento decreciente conforme avanza la obra.
- Ventaja: precios crecientes capturan plusvalía.

**Modelo "stock"**
- Ventas concentradas al final de obra o al FO.
- Ventaja: precios máximos.
- Desventaja: financiamiento del developer durante toda la obra.

### 3.2 Variables
- % vendido al final de obra (objetivo: 60-80% para un proyecto sano).
- Velocidad de absorción (UFs/mes).
- Mix de tipologías y su atractivo relativo.

---

## 4. Tipo de cambio y dual currency

### 4.1 Problema
- Ingresos en USD (o ARS-USD), costos parcialmente en ARS.
- Brecha cambiaria (oficial vs MEP vs blue).

### 4.2 Aproximación
- Modelar costos en ARS y aplicar tipo de cambio para convertir.
- Modelar ingresos en USD.
- Sensibilizar el resultado al tipo de cambio.

### 4.3 Cobertura
- Comprar materiales críticos por adelantado (clavar precios).
- Indexar contratos al CAC o a USD.
- Cláusulas de redeterminación.

---

## 5. Métricas que salen del cashflow

### 5.1 Pico de necesidad de financiación
- Máximo del flujo acumulado negativo.
- Define el equity / crédito mínimo.

### 5.2 Punto de break-even
- Mes en que el flujo acumulado pasa a positivo.

### 5.3 Payback
- Plazo desde el inicio hasta recuperar el capital invertido.

### 5.4 TIR del proyecto y del equity
- Sobre el flujo total y sobre el flujo del equity (sin deuda).

> Ver `./tir-van.md`.

---

## 6. Buenas prácticas

### 6.1 Granularidad
- Mensual para los primeros 24 meses.
- Trimestral después (proyectos de 3+ años).

### 6.2 Conservadurismo
- Aplicar contingencias (5-10% sobre costo de obra, 10-15% sobre estructura).
- Modelar escenario base + pesimista + optimista.

### 6.3 Versionado
- Guardar versiones del modelo con fecha y supuestos.
- Comentar cada cambio.

### 6.4 Validación cruzada
- Cross-check con presupuesto técnico (ingeniero) y comercial (gerente de ventas).
- Verificar que los totales del modelo coincidan con boletos firmados y certificaciones aprobadas.

---

## 7. Errores comunes

- Subestimar gastos de estructura (oficina + sueldos + marketing).
- No incluir impuestos provinciales y municipales en su totalidad.
- Asumir velocidad de venta optimista.
- Olvidar el descuento de la cuota de preventa (ajustes vs incrementos).
- No modelar el efecto cambiario en moneda dura.
- No reservar fondo posventa.
- Confundir flujo de caja con resultado contable (devengado vs percibido).

---

## 8. Reglas operativas para el chat

- **Estable y respondible:** estructura del cashflow, curva S, modelos de venta, métricas derivadas, prácticas de modelado.
- **🟡 Semivolátil:** % típicos de comisión, contingencias.
- **🔴 Volátil:** tipo de cambio, índices CAC/IPC actuales, jornales.
- **🔴 Caso particular:** modelado de un proyecto concreto → analista + planilla detallada.

---

**Ver también:**
- `./tir-van.md`
- `./sensibilidad.md`
- `./financiamiento.md`
- `./metricas-developer.md`
- `../05-construccion/certificacion-obra.md`
