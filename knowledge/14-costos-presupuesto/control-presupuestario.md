---
title: "Control presupuestario y reporting de obra"
topic: "costos-presupuesto"
subtopic: "control"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [control presupuesto, earned value, desvios, cpi, spi, reporte mensual, certificacion, kpi obra, valor ganado]
audience: ["developer", "constructor", "PM", "chat"]
confidence: "alta"
---

# Control presupuestario

## TL;DR
- **Sin control, el presupuesto se va.** En AR + inflación + complejidad de obra, el control mensual es no-negociable.
- Herramientas clave: **certificación mensual + EVM + reporte de desvíos + curva S real vs plan**.
- KPIs: CPI (costo), SPI (avance), % contingencia usada, % avance físico vs financiero.

## 1. Componentes del control

### 1.1 Certificación de obra
- Mensual.
- Constructora presenta avance por ítem.
- Director de obra audita.
- Se libera el pago contra avance certificado.

### 1.2 Comparación plan vs real
- **Plan**: cronograma + curva S inicial.
- **Real**: avance medido + costos ejecutados.
- **Desvío**: diferencia, en tiempo y dinero.

### 1.3 Reporte mensual
- 1-3 páginas máximo.
- Cuadro de avance físico + financiero.
- Top desvíos del mes.
- Acciones correctivas.
- Forecast a final de obra.

## 2. Earned Value Management (EVM)

### 2.1 Definiciones
- **PV** (Planned Value / Valor Planificado): costo planeado para el avance previsto a la fecha.
- **EV** (Earned Value / Valor Ganado): costo planeado del avance **real** a la fecha.
- **AC** (Actual Cost / Costo Real): costo realmente incurrido a la fecha.

### 2.2 Índices
- **SPI** = EV / PV → > 1 adelanto, < 1 atraso.
- **CPI** = EV / AC → > 1 ahorro, < 1 sobrecosto.

### 2.3 Forecast
- **EAC** (Estimate At Completion) = AC + (BAC - EV) / CPI.
- Proyecta costo final del proyecto.

### 2.4 Umbrales de alerta
- CPI < 0.95 → revisión.
- CPI < 0.90 → reunión de crisis.
- SPI < 0.90 → revisar cronograma.

## 3. KPIs clave

### 3.1 De avance
- % avance físico (sumar pesos ponderados).
- % avance financiero (gastado / presupuesto).
- Días de atraso vs plan.

### 3.2 De costo
- CPI.
- % contingencia consumida (alerta si > 50% antes del 50% de avance).
- Variación FX / inflación intra-período.

### 3.3 De calidad
- Cantidad de no-conformidades.
- Re-trabajos.
- Reclamos de inspecciones.

### 3.4 De seguridad
- Accidentes / incidentes.
- Días sin accidentes.
- Cumplimiento de inspecciones ART.

## 4. Frecuencia del reporting

### 4.1 Diario (interno obra)
- Parte de obra: personal, clima, novedades.

### 4.2 Semanal (PM)
- Avance semanal, próximas tareas, riesgos.

### 4.3 Mensual (gerencia + inversores)
- Reporte ejecutivo.
- Curva S real vs plan.
- EVM.
- Forecast.

### 4.4 Trimestral (junta / comité inversores)
- Visión integral.
- Decisiones de gobierno (cambio de alcance, capital adicional).

## 5. Software / herramientas

### 5.1 Especializados
- **Procore** — gestión integral de obra.
- **PlanGrid / Autodesk Build**.
- **Primavera P6** — cronograma.
- **MS Project**.
- **BIM 360 / Autodesk Construction Cloud**.

### 5.2 ERP financiero
- **SAP**, **Oracle**, **Tango**, **Bejerman** (constructoras AR).

### 5.3 Excel
- Aún común en proyectos medianos.
- Riesgo: errores manuales, version control.

## 6. Roles en el control

### 6.1 Director de obra
- Audita certificaciones.
- Aprueba/rechaza change orders.
- Firma avances.

### 6.2 Project Manager (PM)
- Coordina todos los actores.
- Arma reportes.
- Lidera reuniones de control.

### 6.3 Controller financiero
- Cierra costos mensual.
- Valida facturación.
- Cuadra con contabilidad.

### 6.4 Comité de proyecto
- Developer + inversores + asesores.
- Decisiones estratégicas mensuales.

## 7. Gestión de desvíos

### 7.1 Diagnóstico
- Identificar la causa raíz (mat, MO, equipo, proyecto, externo).
- Cuantificar impacto (tiempo + dinero).

### 7.2 Plan de acción
- Acciones correctivas (acelerar, sub-contratar, cambiar proveedor).
- Plan de remediación con dueño + plazo.

### 7.3 Seguimiento
- Re-medir al mes siguiente.
- Escalar si no mejora.

## 8. Cierre del proyecto

### 8.1 Lessons learned
- Revisión post-mortem del control presupuestario.
- ¿Dónde fallaron las estimaciones?
- Ajustes para próximo proyecto.

### 8.2 Liquidación final
- Cierre de contratos.
- Devolución de garantías.
- As-built definitivo.

## 9. Errores comunes

- No certificar mensualmente → sorpresa al final.
- Confundir avance físico con financiero.
- No actualizar la curva S real.
- No aplicar EVM en proyectos complejos.
- Comité de proyecto sin reunirse → decisiones tardías.
- Reportes con demasiada data y poca acción.

## 10. Reglas operativas para el chat

- **Estable:** EVM, KPIs, frecuencia, roles.
- **🔴 Volátil:** software específico, ARS/USD de cada certificación.
- **Sensible:** todo control formal lo lleva el PM + director de obra + controller.
- Si el usuario pregunta "¿cómo controlo mi obra?", recomendar: certificación mensual + EVM + reporte ejecutivo + comité.

## Ver también
- `./curva-s.md`
- `./contingencias-imprevistos.md`
- `./estructura-costos.md`
- `../05-construccion/`
- `../06-financiero/`
