---
title: "Gestión diaria de obra: libro, partes, reuniones"
topic: "construccion"
subtopic: "gestion-diaria"
jurisdiction: "Nacional"
last_verified: "2026-05-12"
sources:
  - "Código Civil y Comercial — locación de obra"
  - "Práctica habitual CAC / colegios profesionales"
  - "Decreto 911/96 — higiene y seguridad"
keywords: [libro de obra, parte diario, parte semanal, reunion de obra, coordinacion, jefe de obra, director de obra, capataz, asistencia, look ahead, lookahead, last planner]
audience: ["desarrollador", "director de obra", "jefe de obra", "project manager"]
confidence: "alta"
---

# Gestión diaria de obra

## TL;DR
- La operativa diaria se sostiene sobre 3 instrumentos: **libro de órdenes**, **parte diario** y **reunión de coordinación**.
- El libro de órdenes es la única **prueba escrita oponible** entre Dirección de Obra y Constructor.
- El parte diario captura: personal, clima, avance, materiales recibidos, incidentes.
- La reunión semanal sigue un **look-ahead de 3 a 6 semanas** (planificación rolling).

---

## 1. Libro de Órdenes

### 1.1 Qué es
- Cuaderno foliado (o digital firmado) donde la Dirección de Obra (DO) asienta órdenes, observaciones y aprobaciones.
- Constructor firma cada asiento como notificación.

### 1.2 Quién escribe
- **DO**: órdenes, observaciones, aprobaciones de muestras, autorización de tareas críticas.
- **Constructor**: comunica avances, solicita aprobaciones, deja constancia de impedimentos.

### 1.3 Valor probatorio
- En caso de litigio, el libro firmado es la fuente primaria para reconstruir lo decidido.
- "Lo que no está en el libro no pasó."

### 1.4 Práctica recomendada
- Cierre diario, asientos con fecha y firma.
- Copia escaneada al gestor documental.
- Numeración correlativa.

---

## 2. Parte diario

### 2.1 Datos mínimos
- Fecha, clima, temperatura.
- Personal por gremio + total.
- Tareas ejecutadas por sector.
- Equipos en obra (grúa, hormigonera, autoelevador, etc.).
- Materiales recibidos (remito, cantidad, proveedor).
- Visitas (inspector, comitente, proveedor).
- Incidentes y near-misses.
- Hora de inicio / fin.

### 2.2 Para qué sirve
- Insumo del **certificado mensual**.
- Trazabilidad para reclamos por climatología o suspensiones.
- Soporte de productividad por gremio.
- Compliance con Decreto 911/96 (registro accidentes).

### 2.3 Frecuencia
- Diario. Sin excepción.
- Quien lo firma: capataz general o jefe de obra.

---

## 3. Parte semanal

### 3.1 Contenido
- Consolidado del parte diario.
- Avance físico por capítulo vs plan.
- Curva S del mes en curso.
- Issues abiertos y propietarios.
- Próximas semanas (look-ahead).

### 3.2 Destinatarios
- Comitente / developer.
- DO.
- Project manager.

---

## 4. Reunión de coordinación

### 4.1 Cadencia
- **Semanal** (lunes o martes temprano).
- 60 a 90 minutos.

### 4.2 Participantes
- Constructor (jefe de obra, capataz general).
- DO.
- Subcontratistas principales (estructura, instalaciones, fachada).
- Comitente o Project Manager.

### 4.3 Agenda tipo
1. Repaso seguridad e incidentes (5 min, no negociable).
2. Avance vs plan semana anterior.
3. Look-ahead 3-6 semanas (qué hay que tener resuelto: muestras, planos, compras).
4. Issues / RFIs abiertos.
5. Decisiones pendientes.
6. Compromisos para la próxima semana (con responsable + fecha).

### 4.4 Minuta
- Quien la redacta: DO o Project Manager.
- Circulada en 24 hs.
- Items con responsable + fecha de compromiso.

---

## 5. Look-ahead y Last Planner

### 5.1 Concepto
- Planificación rolling de las próximas 3 a 6 semanas.
- Foco: qué condiciones tienen que estar dadas (planos, materiales, equipo, mano de obra, permisos) para ejecutar cada tarea.

### 5.2 PPC — Percent Plan Complete
- Métrica del Last Planner System.
- % de tareas comprometidas que se ejecutaron en tiempo y forma.
- PPC saludable: 75-85%. Por debajo de 60% indica plan poco confiable.

### 5.3 Análisis de no-cumplimiento
- Para cada tarea no completada, identificar causa raíz: información tardía, material no llegado, mano de obra, clima, predecesora no terminada, cambio de alcance.
- Acción: corregir el flujo, no a la persona.

---

## 6. RFI — Request for Information

### 6.1 Qué es
- Pedido formal del Constructor a la DO o al Proyectista cuando falta información o hay ambigüedad.
- Se enumera, fecha, asunto, archivo asociado.

### 6.2 Plazo
- Contractual. Típicamente 5 a 10 días hábiles.
- RFIs sin respuesta a tiempo son causa frecuente de reclamo por **prórroga de plazo**.

### 6.3 Registro
- Planilla RFI con: número, fecha emisión, asunto, fecha respuesta, plano/spec afectado, impacto (plazo, costo, calidad).

---

## 7. Asistencia y control de acceso

### 7.1 Libro de asistencia
- Personal propio + subcontratistas.
- Firma de entrada/salida.
- En obras grandes: lectores biométricos o RFID.

### 7.2 Verificación previa al ingreso
- ART vigente.
- Aviso de inicio de actividad cargado.
- Inducción de seguridad (charla de 1 día).
- EPP entregado.

### 7.3 IERIC
- En obras formales registradas, control vía libreta IERIC.

---

## 8. Documentación crítica que debe estar siempre en obra

- Plano municipal aprobado.
- Pliego y especificaciones técnicas.
- Plano as-planned actualizado.
- Libro de órdenes vigente.
- Libro de asistencia.
- Plan de seguridad e higiene aprobado.
- ART de toda la nómina.
- F931 del mes anterior de cada subcontratista.
- Habilitaciones de equipos (grúa, plataformas).
- Comprobantes de aporte UOCRA / IERIC.

> Ver `./documentacion-obra.md` para detalle.

---

## 9. KPIs operativos sugeridos

- **Avance físico vs plan** (curva S).
- **PPC semanal**.
- **Productividad** por gremio (m² / hora-hombre, m³ / hora-hombre).
- **Días de retraso acumulados**.
- **Incidentes** (TRIR, LTIFR) — frecuencia y gravedad.
- **RFIs abiertos** y antigüedad media.
- **Cumplimiento de compromisos** de reunión.

---

## 10. Errores comunes

- Reuniones sin minuta circulada → todo se discute de nuevo la semana siguiente.
- Parte diario llenado al final de la semana → datos perdidos.
- Libro de órdenes en blanco → todo reclamo termina perdiéndose.
- Look-ahead que no se actualiza → planificación de papel.
- No medir PPC → no hay aprendizaje del sistema.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** rol del libro de órdenes, estructura del parte diario, cadencia de reuniones, mecánica de look-ahead, RFIs.
- **🔴 Volátil:** plazos contractuales específicos, valores de productividad por gremio (varían según obra y mercado), porcentajes de PPC aceptables (dependen del contexto).

---

**Ver también:**
- `./documentacion-obra.md`
- `./certificacion-obra.md`
- `./higiene-seguridad.md`
- `./change-orders-claims.md`
- `./gestion-subcontratistas.md`
