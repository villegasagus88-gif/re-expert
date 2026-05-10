---
title: "Fideicomiso financiero — RE con oferta pública"
topic: "impuestos"
subtopic: "fideicomiso-financiero"
jurisdiction: "Nacional"
last_verified: "2026-05-10"
sources:
  - "CCyCN arts. 1690–1695 (fideicomiso financiero)"
  - "Ley 24.083 (FCI) y Ley 26.831 (Mercado de Capitales)"
  - "CNV — Normas (T.O. 2013) y modificaciones"
keywords: [fideicomiso financiero, oferta publica, CNV, valores fiduciarios, certificados participacion, titulos deuda, securitizacion]
audience: ["desarrollador grande", "abogado mercado capitales", "estructurador"]
confidence: "alta"
---

# Fideicomiso financiero — RE

## TL;DR
- Variante del fideicomiso con autorización de **oferta pública** de los valores fiduciarios (VF) emitidos.
- Fiduciario: solo entidades autorizadas por CNV (entidades financieras / sociedad fiduciaria registrada).
- Permite **levantar capital del público** para financiar proyectos RE.
- Régimen tributario específico, con beneficios para los inversores (exenciones según el tipo de VF y el adquirente).
- Requiere prospecto, calificación y permanente reporting.

---

## 1. Marco legal

### 1.1 CCyCN arts. 1690–1695
- Define el fideicomiso financiero como aquel cuyos beneficiarios son los titulares de **certificados de participación (CP)** o **títulos representativos de deuda (TD)**.
- Fiduciario: entidad financiera o sociedad especialmente autorizada.
- Plazo y demás reglas generales del fideicomiso aplican.

### 1.2 Ley 26.831 — Mercado de Capitales
- Régimen general de oferta pública.
- Atribuciones de CNV.

### 1.3 CNV — Normas vigentes
- Capítulo específico sobre fideicomisos financieros.
- Requisitos de prospecto, contrato, calificación de riesgo, periodicidad de información.

---

## 2. Estructura típica

### 2.1 Partes
- **Fiduciante (originador)**: el que aporta los activos / proyecto.
- **Fiduciario**: entidad autorizada que administra y emite los VF.
- **Inversores**: tenedores de los VF (públicos o privados).
- **Agente de control y revisión**.
- **Calificadora de riesgo**.
- **Agente colocador / underwriter**.

### 2.2 Activos fideicomitidos típicos en RE
- Boletos de compraventa con flujo de cobro previsto.
- Hipotecas y/o flujos de créditos hipotecarios.
- Recibos de alquileres futuros (en algunos esquemas).
- Derechos sobre obras en construcción.

### 2.3 Valores fiduciarios
- **Certificados de participación (CP)**: dan derecho al producto del proyecto (riesgo equity).
- **Títulos de deuda (TD)**: deuda con tasa fija o variable, prioridad sobre los CP.
- **Tramos** (senior, mezzanine, junior) según prioridad.

---

## 3. Tributación

### 3.1 Para el fideicomiso
- Sujeto Ganancias: 3ª categoría.
- Posibilidad de deducir los pagos a tenedores de TD como interés.
- En ciertos casos, hay exención si distribuye el 100% a tenedores con oferta pública (verificar régimen vigente).

### 3.2 Para los tenedores de TD
- Renta financiera: tributa como interés.
- Persona humana: posible exención según régimen vigente.

### 3.3 Para los tenedores de CP
- Tratamiento similar a dividendos.

### 3.4 IVA
- En general no aplica (es un vehículo financiero, no realiza obra sobre inmueble propio).
- Si el fideicomiso desarrolla obra: aplica IVA por la parte productiva.

### 3.5 Sellos / IIBB
- Exenciones específicas en algunas jurisdicciones para fideicomisos financieros con oferta pública.

---

## 4. Procedimiento de constitución

1. Selección del fiduciario y estructurador.
2. Diseño del flujo (cómo se generará el cash flow).
3. Análisis legal e impositivo.
4. Calificación de riesgo (al menos una calificadora).
5. Prospecto.
6. Aprobación CNV.
7. Colocación: oferta primaria (subasta o book-building).
8. Listado en BYMA / MAE.
9. Reporting periódico (mensual / trimestral).

---

## 5. Casos de uso en RE argentino

### 5.1 Securitización de boletos
- Developer cede una cartera de boletos al fideicomiso.
- El fideicomiso emite TD y CP.
- Los inversores cobran de los pagos de los compradores.

### 5.2 Préstamos puente
- Developer financia construcción inicial con TD.
- Repaga con flujo de ventas.

### 5.3 Real Estate Investment Trust (REIT) — homologable
- Argentina no tiene un REIT formal con régimen específico, pero algunos fideicomisos financieros con renta de alquiler funcionan como aproximación.

---

## 6. Ventajas y desventajas

### 6.1 Ventajas
- Acceso a capital del público.
- Diversifica fuentes de financiamiento.
- Patrimonio aislado del fiduciante (mejor calificación).
- Posibilidad de tasa más baja vía calificación.

### 6.2 Desventajas
- Costo de estructuración alto (legal, calificadora, fiduciario).
- Reporting permanente.
- Mínimos de emisión que solo justifican proyectos grandes.
- Sensibilidad al mercado (puede no colocarse en condiciones adversas).

---

## 7. Errores comunes

- Lanzarse a fideicomiso financiero para proyectos chicos donde el costo absorbe la ventaja.
- Subestimar el plazo de aprobación CNV.
- No considerar la calificación de riesgo desde el día 1.
- Mal diseño del flujo (caso de stress no cubierto).
- Reporting incumplido → infracciones CNV.

---

## 8. Reglas operativas para el chat

- **Estable y respondible:** marco legal, partes, lógica de la securitización, diferencia con ordinario / al costo.
- **🟡 Semi-volátil — verificar:** régimen tributario específico (a veces hay incentivos por norma temporal), normas CNV vigentes para emisión.
- **🔴 Caso particular:** estructurar uno requiere mesa de mercado de capitales. El chat orienta, no diseña.

---

**Ver también:**
- `./fideicomiso-ordinario.md`
- `./fideicomiso-al-costo.md`
- `./comparativa-vehiculos.md`
