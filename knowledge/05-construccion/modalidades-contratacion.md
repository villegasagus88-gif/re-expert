---
title: "Modalidades de contratación de obra"
topic: "construccion"
subtopic: "modalidades-contratacion"
jurisdiction: "Nacional"
last_verified: "2026-05-10"
sources:
  - "CCyCN arts. 1251-1279 (locación de obra)"
  - "Cámara Argentina de la Construcción — pliegos y prácticas"
keywords: [modalidades obra, precio cerrado, costo + honorarios, llave en mano, ajuste alzado, administracion, redeterminacion]
audience: ["desarrollador", "constructor", "arquitecto"]
confidence: "alta"
---

# Modalidades de contratación de obra

## TL;DR
- Cinco modalidades clásicas: **ajuste alzado / precio cerrado**, **costo + honorarios** ("administración"), **unidad de medida**, **llave en mano**, **mixta**.
- Elección depende de: certeza del proyecto, tolerancia al riesgo, control deseado, plazo, financiamiento.
- Cada modalidad tiene perfil de riesgo + exposición a inflación + estructura de incentivos distinta.

---

## 1. Ajuste alzado / Precio cerrado

### 1.1 Concepto
- El constructor se obliga a ejecutar la **obra completa por un precio total fijo**.
- Riesgo de costos adicionales: del **constructor**.

### 1.2 Variantes
- **Ajuste alzado absoluto**: precio fijo sin redeterminación.
- **Ajuste alzado relativo**: precio fijo con cláusula de redeterminación por índices (CAC, ICC).

### 1.3 Cuándo conviene
- Proyecto con pliego cerrado, planos definitivos.
- Inflación controlada o cláusula de redeterminación.
- Developer quiere certeza de costo.

### 1.4 Riesgos
- Constructor "se queda corto" → conflicto + reclamo de adicionales.
- Discusiones por adicionales: cualquier cambio fuera del pliego dispara renegociación.

---

## 2. Costo + honorarios (administración)

### 2.1 Concepto
- El constructor cobra **honorarios fijos o porcentuales** y traslada **el costo real** al developer.
- Riesgo de costos: del **developer**.

### 2.2 Variantes
- Honorarios % sobre costo total ejecutado.
- Honorarios fijos por mes + bonificación al cierre.
- Honorarios + bonus por ahorro respecto a presupuesto inicial.

### 2.3 Cuándo conviene
- Proyectos con definición incompleta al inicio.
- Inflación alta y dinámica.
- Developer con experiencia y equipo de control propio.

### 2.4 Riesgos
- Falta de incentivo del constructor para optimizar costos.
- Necesidad de control fuerte por parte del developer.
- Conflicto al determinar qué se imputa como "costo real".

---

## 3. Unidad de medida

### 3.1 Concepto
- Pago por unidad ejecutada (m² de losa, m³ de hormigón, m de mampostería).
- Cantidades estimativas; el pago real depende de lo ejecutado.

### 3.2 Cuándo conviene
- Obras con cantidades inciertas al inicio (movimiento de suelos, infraestructura).
- Obra pública con licitaciones unitarias.

### 3.3 Riesgos
- Desbalance si las cantidades reales se desvían del estimado.
- Posible discusión por unidades cobradas vs ejecutadas.

---

## 4. Llave en mano (turnkey)

### 4.1 Concepto
- El constructor se obliga a entregar la **obra terminada y operativa** a un precio total.
- Incluye proyecto + ejecución + a veces gestión de habilitaciones.

### 4.2 Cuándo conviene
- Developer que solo quiere recibir la obra terminada sin gestión.
- Proyectos industriales o equipamiento complejo.
- Plantas, hoteles, hospitales.

### 4.3 Riesgos
- Precio típicamente más alto (riesgo trasladado).
- Calidad/especificaciones discutidas a posteriori.

---

## 5. Mixta

### 5.1 Concepto
- Combinación de modalidades por capítulo.
- Ej: estructura por ajuste alzado, instalaciones por costo + honorarios, terminaciones por unidad de medida.

### 5.2 Cuándo conviene
- Proyectos grandes con secciones de distinta certeza.

---

## 6. Redeterminación de precios

### 6.1 Concepto
- Cláusula que actualiza el precio por inflación a través de índices.

### 6.2 Índices habituales en RE AR
- **CAC** (Cámara Argentina de la Construcción): índice del costo de construcción.
- **ICC** (INDEC): Índice del Costo de la Construcción.
- **IPC** (INDEC): Índice de Precios al Consumidor.
- **UVA / UVI**.
- Tipos de cambio (USD oficial, MEP, blue) en construcciones dolarizadas.

### 6.3 Estructura típica
- Fórmula polinómica: F = a*Mat + b*MO + c*Equip + d*GG.
- Cada componente con su índice.
- Periodicidad: trimestral o por certificación.

### 6.4 Buenas prácticas
- Cláusula clara y verificable.
- Tope o ventana de redeterminación.
- Mecanismo de resolución de disputas.

---

## 7. Componentes del costo de obra

### 7.1 Materiales
- 30–45% del total (varía por proyecto y momento).

### 7.2 Mano de obra
- 35–50% del total.

### 7.3 Equipos / amortización
- 5–10%.

### 7.4 Gastos generales
- 8–15% (oficina técnica, dirección, administración).

### 7.5 Beneficio del constructor
- 8–15% según riesgo y modalidad.

### 7.6 Impuestos asociados
- IIBB, IVA en MO contratada, sellos.

---

## 8. Estructura de pago

### 8.1 Anticipo
- Típicamente 10–20% al firmar.
- Garantizado con póliza de caución.

### 8.2 Certificaciones mensuales
- Por avance medido.
- Acumulado descontando anticipo.
- Retención del 5–10% como garantía hasta final de obra.

### 8.3 Final de obra
- Liberación de la retención.
- Recepción provisional + definitiva (pasados 6-12 meses).

---

## 9. Garantías habituales

### 9.1 De anticipo
- Póliza de caución por el monto del anticipo.

### 9.2 De cumplimiento
- Póliza de caución del 5–10% del contrato.

### 9.3 De fondos de reparo
- Retención sobre certificaciones.

### 9.4 De vicios redhibitorios y ruina (CCyCN)
- Por años después de la entrega.

> Ver `./garantias-vicios-ruina.md`.

---

## 10. Errores comunes

- Firmar precio cerrado con planos incompletos → adicionales explosivos.
- Gestionar costo + honorarios sin equipo de control propio.
- No tener cláusula de redeterminación en contexto inflacionario.
- Anticipo sin póliza → pérdida si el constructor quiebra.
- Falta de tope a los adicionales.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** modalidades y sus características, ventajas/desventajas, índices de redeterminación, estructura de pago.
- **🔴 Volátil:** valor de los índices, costos por m² actual.
- **🔴 Caso particular:** elección de modalidad para un proyecto concreto → arquitecto + abogado + financiero.

---

**Ver también:**
- `./certificacion-obra.md`
- `./garantias-vicios-ruina.md`
- `./documentacion-obra.md`
- `../06-financiero/cashflow-real-estate.md` (TBD)
