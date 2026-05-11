---
title: "Contingencias e imprevistos en obra"
topic: "costos-presupuesto"
subtopic: "contingencias"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [contingencias, imprevistos, reserva, change order, adicionales, modificaciones, riesgos obra, buffer]
audience: ["developer", "constructor", "PM", "chat"]
confidence: "alta"
---

# Contingencias e imprevistos

## TL;DR
- **Contingencia** = reserva financiera para cubrir lo inesperado.
- En obra **siempre** aparecen imprevistos: suelo, vecino, clima, cambios regulatorios, errores de proyecto.
- Reserva típica: 10-15% en anteproyecto, 5-10% en proyecto ejecutivo, 3-5% en obra avanzada.
- No tenerla = riesgo de quiebre del proyecto.

## 1. Tipos de imprevistos

### 1.1 Técnicos
- Suelo diferente al esperado (loess, napa, contaminación).
- Hallazgos arqueológicos / restos.
- Cambios estructurales por errores de proyecto.
- Patología de materiales (hormigón fuera de spec, etc.).

### 1.2 Regulatorios / administrativos
- Cambio normativo durante obra.
- Demora en habilitaciones.
- Requerimiento adicional de bomberos / municipalidad.

### 1.3 Vecinos / terceros
- Reclamos / cautelares.
- Daños a propiedades vecinas (medianeras, fisuras).
- Submuración no prevista.

### 1.4 Climáticos / externos
- Lluvias prolongadas, tormentas.
- Cortes de energía / agua.
- Conflictos gremiales.

### 1.5 Económicos / financieros
- Devaluación + retroceso de pre-ventas.
- Default de contratistas / subcontratistas.
- Cambio brusco de costo de materiales.

### 1.6 Pandemia / fuerza mayor
- Eventos extraordinarios (COVID-19 fue un ejemplo claro).

## 2. Reserva de contingencias

### 2.1 % típico por etapa
| Etapa del proyecto | Contingencia recomendada |
|---|---|
| Anteproyecto | 10-15% sobre costo directo |
| Proyecto ejecutivo | 5-10% |
| Obra avanzada (>50%) | 3-5% |
| Final de obra | 1-2% (cierre) |

### 2.2 Asignación
- **Buffer financiero del developer** (no se da al constructor).
- Se activa por **change order** documentado.

## 3. Change orders (modificaciones)

### 3.1 Definición
- Orden de cambio en el alcance del contrato de obra.
- Puede modificar plazo + costo + alcance.

### 3.2 Tipos
- **Por error de proyecto** (asume el proyectista / developer).
- **Por requerimiento del comitente** (asume el comitente).
- **Por condiciones imprevistas** (depende del contrato).

### 3.3 Procedimiento
1. Detección del cambio.
2. Cotización del impacto.
3. Aprobación formal.
4. Modificación de cronograma + presupuesto.
5. Documentación + firma de adenda.

### 3.4 Riesgo
- Change orders descontrolados = sobrecostos masivos.
- Procedimiento riguroso evita "filtraciones".

## 4. Documentación de imprevistos

### 4.1 Bitácora / libro de obra
- Toda novedad se registra.
- Soporte legal en eventuales disputas.

### 4.2 Reportes mensuales
- Avance + desvíos + uso de contingencia.
- Aprobación de gerencia / inversores.

### 4.3 Reportes a inversores
- Transparencia genera confianza.
- Mejor reportar a tiempo que esconder.

## 5. Mitigación de imprevistos

### 5.1 Pre-obra
- Estudio de suelos completo.
- Due diligence dominial.
- Proyecto coordinado (BIM).
- Revisión de proyecto ejecutivo por tercero (peer review).

### 5.2 En obra
- Director de obra activo + buen jefe de obra.
- Subcontratistas calificados con historia.
- Comunicación con vecinos pre-obra.
- Seguros adecuados (TRC, responsabilidad civil).

### 5.3 Financieros
- Acopio de materiales clave.
- Cobertura cambiaria si insumos importados.
- Líneas de crédito stand-by.

## 6. Seguros relevantes

### 6.1 TRC (Todo Riesgo Construcción)
- Cubre daños materiales en obra.
- Robos, incendios, derrumbes parciales.

### 6.2 Responsabilidad civil
- Daños a terceros (vecinos, transeúntes).
- Imprescindible.

### 6.3 ART (Aseguradora de Riesgos del Trabajo)
- Personal: obligatorio Ley 24.557.

### 6.4 Avales / garantías
- Adelanto, cumplimiento, vicios redhibitorios.

## 7. Casos típicos

### 7.1 Sorpresa de suelo
- Suelo blando descubierto en excavación → cambio de fundación (USD +100-500k).

### 7.2 Vecino con cautelar
- Suspensión 2-6 meses + costos legales.

### 7.3 Devaluación brusca
- Materiales suben +30% en 30 días → impacto cash flow.

### 7.4 Cambio de norma
- Nueva exigencia de eficiencia energética → adicionales 1-3%.

## 8. Errores comunes

- No reservar contingencia ("vamos a estar bien").
- Usar la contingencia para mejoras de alcance (no para imprevistos).
- No documentar change orders.
- Tener seguros mínimos por ahorrar prima.
- No comunicar a inversores hasta que el problema es grave.

## 9. Reglas operativas para el chat

- **Estable:** concepto, tipos, % típicos, mitigaciones.
- **🔴 Volátil:** primas de seguros, magnitud monetaria de imprevistos específicos.
- **Sensible:** la gestión de imprevistos la lleva el PM + director de obra + comité de proyecto.
- Si el usuario pregunta "¿cuánta contingencia poner?": 10-15% en anteproyecto es buen punto de partida; ajustar por complejidad.

## Ver también
- `./control-presupuestario.md`
- `./estructura-costos.md`
- `../05-construccion/garantias-vicios-ruina.md`
- `../05-construccion/modalidades-contratacion.md`
- `../18-seguros/` (pendiente)
