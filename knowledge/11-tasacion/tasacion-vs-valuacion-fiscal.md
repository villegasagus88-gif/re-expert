---
title: "Tasación de mercado vs. valuación fiscal"
topic: "tasacion"
subtopic: "fiscal-vs-mercado"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Códigos Fiscales nacional / provincial / CABA"
  - "AGIP, ARBA, AFIP — bases de valuaciones"
keywords: [valuacion fiscal, valor mercado, vir, vir caba, valuacion arba, bienes personales, ganancias, impuesto inmobiliario, base imponible]
audience: ["propietario", "contador", "developer", "chat"]
confidence: "alta"
---

# Tasación de mercado vs. valuación fiscal

## TL;DR
- **Valuación fiscal** = la que fija el fisco para calcular impuestos.
- **Tasación de mercado** = lo que un comprador pagaría hoy.
- En AR la valuación fiscal suele ser **menor** al valor de mercado, aunque con vaivenes históricos.
- Cada tributo puede tener su propia base de valuación (no siempre coinciden entre AGIP, ARBA, AFIP, municipios).

## 1. Definiciones

### 1.1 Valuación fiscal
- Valor del inmueble determinado por el fisco para liquidar impuestos:
  - **Impuesto inmobiliario** (provincial).
  - **ABL / TSG** (municipal).
  - **Bienes Personales** (nacional — usa base fiscal mínima).
  - **Sellos** (toma valor de mercado o fiscal, el mayor).
  - **Cedular / Ganancias** (toma precio de venta declarado).

### 1.2 Valor de mercado (tasación)
- Lo que un comprador racional pagaría en un mercado normal.
- Se obtiene por los métodos profesionales (ver `./metodos-valuacion.md`).

### 1.3 Valor de origen / costo computable
- Valor histórico de adquisición (más mejoras), actualizado por índices oficiales (en AR, IPC para Cedular post-2018).

## 2. Bases de valuación fiscal por jurisdicción

### 2.1 Nacional — Bienes Personales
- Base: **mayor** entre valuación fiscal ajustada y costo computable actualizado.
- Para vivienda única: exenta hasta tope.
- Verificar AFIP.

### 2.2 Cedular (Ley 27.430)
- Base: **precio de venta declarado** − **costo computable actualizado** (IPC) − mejoras − gastos.
- Si el precio declarado es notoriamente menor al de mercado, AFIP puede impugnar (riesgo).

### 2.3 ABL — CABA (AGIP)
- Base: **valuación fiscal homogénea** (VFH) que actualiza periódicamente AGIP.
- Componentes: valor terreno + valor construcciones.
- Tarifa progresiva.

### 2.4 Impuesto inmobiliario PBA (ARBA)
- Base: **valuación fiscal** del inmueble + alícuota progresiva por tramo.
- Se actualiza por ley impositiva anual.

### 2.5 Sellos
- Base: el **mayor** entre precio de operación y valuación fiscal.

### 2.6 Otras provincias
- Cada Dirección de Rentas tiene su sistema; ver `../04-impuestos/provincial/`.

## 3. Por qué la valuación fiscal suele ser menor

- Inercia histórica: los registros de valuación se actualizan con menos velocidad que los precios reales.
- Decisión política: subir valuación significa subir impuestos → tema sensible.
- Sin embargo, los fiscos van cerrando la brecha periódicamente (revaluaciones).

## 4. Casos donde la diferencia importa mucho

### 4.1 Compraventa con sellos
- Sellos toma el **mayor**: si la operación se declara por debajo de la valuación fiscal, paga sobre la valuación.
- Imposible declarar "menos" para ahorrar sellos.

### 4.2 Bienes Personales
- Inmuebles entran a BP por la base mayor.
- Vivienda única exenta hasta tope.

### 4.3 Cedular
- AFIP puede impugnar precios irrisorios.
- Cuidado en transmisiones gratuitas o entre vinculados.

### 4.4 Tasación judicial en expropiación
- TTN parte de un valor objetivo (cercano a mercado), no de la valuación fiscal.

## 5. Cómo consultar la valuación fiscal

| Tributo | Dónde |
|---|---|
| ABL CABA | AGIP — boleta del inmueble o calculador en sitio |
| Impuesto inmobiliario PBA | ARBA — autogestión |
| Otras provincias | Sitio de cada DGR |
| Bienes Personales | Por inmueble en boleta + actualización AFIP |
| Sellos | Caso a caso al escriturar |

## 6. Implicancias para el developer

### 6.1 Al comprar suelo
- Verificar valuación fiscal para anticipar sellos.
- Valuación fiscal alta → más sellos pagados.

### 6.2 Durante la obra
- ABL/TSG del terreno baldío.
- Cuando se incorpora la construcción, se reevalúa.

### 6.3 Al vender UF
- Para sellos: base es mayor entre operación y valuación.
- Para Cedular: precio declarado define ganancia (con riesgo de impugnación si es bajo).

### 6.4 Al armar Bienes Personales del fideicomiso / sociedad
- Inmueble entra por base fiscal.

## 7. Errores comunes

- Asumir que se puede declarar la operación a valor menor para ahorrar sellos → no se puede (sellos toma el mayor).
- Confundir valuación fiscal con valor de mercado al hablar con un comprador.
- Olvidar que la valuación fiscal cambia (actualizaciones anuales o bianuales).
- No verificar la valuación fiscal antes de escriturar (sorpresa en sellos).

## 8. Reglas operativas para el chat

- **Estable:** diferencia conceptual, qué tributo usa qué base.
- **🔴 Volátil:** valuación fiscal puntual de un inmueble → AGIP / ARBA / DGR.
- Si la pregunta es "¿cuánto pago de sellos?", responder con metodología + pedir base + derivar a escribano/contador.

## Ver también
- `./metodos-valuacion.md`
- `../04-impuestos/nacional/bienes-personales.md`
- `../04-impuestos/nacional/cedular-inmuebles.md`
- `../04-impuestos/provincial/_overview.md`
- `../04-impuestos/municipal/abl-tsg.md`
