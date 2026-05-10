---
title: "Financiamiento de proyectos inmobiliarios"
topic: "financiero"
subtopic: "financiamiento"
jurisdiction: "Argentina"
last_verified: "2026-05-10"
sources:
  - "BCRA — Comunicaciones sobre crédito hipotecario"
  - "CNV — fideicomisos financieros"
  - "Práctica de mercado RE AR"
keywords: [financiamiento, credito hipotecario, UVA, fideicomiso financiero, ON, equity, deuda, preventa, club deal]
audience: ["developer", "inversor", "fideicomiso"]
confidence: "alta"
---

# Financiamiento de proyectos inmobiliarios

## TL;DR
- **Equity** (capital propio) + **deuda** + **preventa** = mezcla habitual.
- Fuentes: capital del developer + inversores + boletos preventa + crédito bancario + obligaciones negociables (ON) + fideicomiso financiero.
- Crédito hipotecario al usuario final: estructural pero **muy volátil** según el contexto macro.
- Costos del financiamiento: tasa + fees + sellos + impuestos al cheque + garantías + estructuración.

---

## 1. Mezcla típica

### 1.1 Proyecto al costo (al-costo)
- 100% equity de los fiduciantes.
- No hay deuda formal.
- Riesgo y retorno totalmente del fiduciante-beneficiario.

### 1.2 Proyecto a precio cerrado / con desarrollo profesional
- Equity del developer (10-30%).
- Preventa (30-50%).
- Crédito (10-30%).
- Mix se ajusta al ciclo macro.

### 1.3 Proyecto financiero / "joint venture"
- Equity del developer (sweat equity / aporte mínimo).
- Equity de inversores (mayoría del aporte).
- Preventa.
- Eventualmente deuda.

---

## 2. Equity del developer e inversores

### 2.1 Aporte directo
- Capital efectivo en el fideicomiso o sociedad.
- Genera derecho a participación.

### 2.2 Sweat equity
- Aporte en gestión y management, valorizado como % del proyecto.

### 2.3 Tierra como aporte
- Permuta: el dueño de la tierra recibe UFs en lugar de dinero.
- Estructura común (ver `../10-estrategia/permuta.md` TBD).

### 2.4 Llamadas de capital
- Aportes escalonados según el cashflow del proyecto.
- Ratificadas por el órgano de gobierno del fideicomiso o sociedad.

---

## 3. Preventa como financiamiento

### 3.1 Mecánica
- Boleto firmado con anticipo + cuotas durante obra.
- Funciona como deuda de hecho (pasivo a entregar UF).

### 3.2 Ventajas
- No hay tasa explícita: el "costo" es el descuento dado al precio de venta vs precio finalizado.
- No requiere garantía bancaria.
- Genera demanda probada (acelera siguientes ventas).

### 3.3 Desventajas
- Limita la flexibilidad: las UFs vendidas están comprometidas.
- Si la preventa se desploma → riesgo de iliquidez.
- Cuotas suelen ajustarse por índice (CAC, IPC, USD), creando fricción.

---

## 4. Crédito bancario — proyecto

### 4.1 Crédito constructor
- Banco financia parte del costo de obra.
- Garantía: hipoteca sobre el inmueble (terreno + obra).
- Desembolso por avance medido (no de una vez).
- Tasa: típicamente UVA + spread, BADLAR + spread, o USD-Libor + spread (cuando aplica).

### 4.2 Crédito puente
- Para cubrir gaps temporarios.
- Plazo corto (6-18 meses).
- Garantía mixta.

### 4.3 Líneas oficiales
- Cuando existen (programas FONDEP, ProCreAr empresas, etc.) — 🔴 volátil, depende del gobierno de turno.

---

## 5. Crédito hipotecario al usuario final

### 5.1 UVA
- Préstamos ajustables por inflación (CER).
- Funcionaron 2016-2018 con masa crítica.
- Volúmenes muy variables según contexto. 🔴 verificar BCRA al momento.

### 5.2 USD vendor financing
- Algunos developers ofrecen plan de pagos en USD propios.
- Sin intermediación bancaria.
- Riesgo crediticio absorbido por el developer.

### 5.3 Importancia
- En mercados sanos (Chile, Brasil, etc.), el hipotecario al consumidor mueve la mayor parte de la demanda.
- En AR, el hipotecario es históricamente cíclico → el desarrollador no puede asumir su disponibilidad.

---

## 6. Fideicomiso financiero / ON

### 6.1 Fideicomiso financiero (CNV)
- Estructura por oferta pública.
- Para proyectos grandes con garantías sobre cobranzas.
- Costos de estructuración significativos.
- Suscripción por inversores institucionales y minoristas.

### 6.2 Obligaciones negociables (ON)
- Emitidas por sociedades (no FF).
- En USD o pesos.
- Para developers con track record y escala.

### 6.3 Cuándo conviene
- Proyectos grandes (USD 20M+).
- Estructura de pago previsible (alquileres futuros, cuotas firmes).
- Búsqueda de tasas mejores que las bancarias.

---

## 7. Crowdfunding inmobiliario

### 7.1 Plataformas
- En AR: en desarrollo, marco regulatorio aún no maduro.
- En EE.UU. y Europa más avanzado.

### 7.2 Mecánica
- Capital fraccionado en montos chicos.
- Inversor recibe % de un fideicomiso o ingreso de alquiler.

### 7.3 Riesgo
- Verificar habilitación de la plataforma ante CNV.
- Diligencia previa al proyecto.

---

## 8. Costos asociados al financiamiento

### 8.1 Componentes
- Tasa nominal.
- Comisión de apertura / estructuración.
- Sellos (provincia donde se firma el contrato).
- Impuesto al cheque (cuando aplica).
- Honorarios escribanos / asesores.
- Costo de garantías (pólizas, hipoteca).

### 8.2 CFT (Costo Financiero Total)
- Métrica que integra todos los costos.
- Comparable entre alternativas.

---

## 9. Garantías

### 9.1 Tipos
- Hipoteca sobre el inmueble.
- Cesión de derechos de cobro de boletos.
- Avales personales / cruzados de socios.
- Pólizas de caución.

### 9.2 Implicancias
- A mayor garantía, menor tasa.
- Garantías personales pueden bloquear el patrimonio del socio.

---

## 10. Errores comunes

- Asumir disponibilidad permanente del crédito hipotecario al usuario.
- No estructurar correctamente la garantía → tasa cara.
- No prever fees y costos accesorios → CFT mucho mayor a la tasa nominal.
- Mezclar moneda de deuda (USD) con moneda de ingreso (pesos a oficial) → riesgo cambiario explosivo.
- Calcular el modelo asumiendo siempre la opción más barata.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** estructura del financiamiento, fuentes, mecánica de cada uno, costos asociados, garantías típicas.
- **🔴 Volátil:** tasas vigentes, líneas oficiales activas, condiciones del crédito hipotecario actual → BCRA / banco / CNV en tiempo real.
- **🔴 Caso particular:** estructuración para un proyecto específico → financiero + abogado.

---

**Ver también:**
- `./tir-van.md`
- `./cashflow-real-estate.md`
- `./apalancamiento.md`
- `../04-impuestos/estructuras-fiscales/fideicomiso-financiero.md`
- `../04-impuestos/estructuras-fiscales/comparativa-vehiculos.md`
