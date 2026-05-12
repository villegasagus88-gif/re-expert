---
title: "Change orders, variaciones y claims de obra"
topic: "construccion"
subtopic: "change-orders"
jurisdiction: "Argentina"
last_verified: "2026-05-12"
sources:
  - "CCyCN — locación de obra (arts. 1251-1279)"
  - "Decreto 1023/01 — obra pública (referencial)"
  - "Práctica habitual contratos privados AR"
keywords: [change order, orden de cambio, variacion, adicional, ampliacion, reclamo, claim, mayores costos, prorroga de plazo, gastos improductivos, fast track, vo, variation order]
audience: ["developer", "director de obra", "constructor", "project manager"]
confidence: "alta"
---

# Change orders, variaciones y claims

## TL;DR
- **Change order (CO) / Variation Order (VO)**: cambio formal al alcance, plazo o precio del contrato, acordado por las partes ANTES de ejecutar.
- **Claim**: reclamo de una parte por incumplimiento, demora o impacto de la otra. Se gestiona DESPUÉS del hecho.
- Un proyecto sin disciplina de CO termina en disputa millonaria por valores que nadie acuerda al final.
- En contextos inflacionarios AR, la **redeterminación** es un mecanismo distinto al CO: ajusta precio del contrato vigente, no cambia alcance.

---

## 1. Cambios vs reclamos: diferencia clave

| Variable | Change order | Claim |
|---|---|---|
| Cuándo | Antes de ejecutar | Después del hecho |
| Forma | Acuerdo bilateral | Pretensión unilateral |
| Resultado | Anexo al contrato | Negociación / arbitraje / juicio |
| Riesgo | Bajo si bien gestionado | Alto: sin acuerdo, escala |

---

## 2. Causas típicas de change order

### 2.1 Originadas por el comitente
- Cambio de programa (uso del espacio).
- Cambio de spec / terminación.
- Adición de superficie.
- Eliminación de items.
- Aceleración (acortar plazo a pedido).

### 2.2 Originadas por proyectista / DO
- Error u omisión en plano.
- Spec ambigua.
- Coordinación entre disciplinas que no cierra.

### 2.3 Originadas por el constructor
- Sugerencia de optimización (value engineering).
- Imposibilidad técnica que requiere alternativa.

### 2.4 Originadas por terceros
- Cambio normativo (código, ordenanza).
- Hallazgo arqueológico / restos enterrados.
- Hallazgo de instalaciones existentes no documentadas.
- Caso fortuito o fuerza mayor.

---

## 3. Procedimiento estándar de change order

### 3.1 Detección
- Por DO, constructor o comitente.
- Anotación en libro de órdenes.

### 3.2 Análisis de impacto
- Por el constructor:
  - Impacto en alcance (planos, spec).
  - Impacto en costo (cómputo + precio).
  - Impacto en plazo (cronograma).
  - Impacto en interfaces (otros gremios).

### 3.3 Cotización del cambio
- Cómputo + precio según APU contractual o nuevo precio si el ítem es nuevo.
- Margen contractual (típicamente: % de gastos generales + beneficio sobre el costo directo del cambio).

### 3.4 Análisis por el comitente
- Verificación técnica por DO.
- Aprobación de presupuesto.
- Aprobación de prórroga si aplica.

### 3.5 Emisión del CO
- Documento firmado por ambas partes.
- Anexo al contrato.
- Incluye: descripción, impacto en precio, impacto en plazo, fecha de aprobación.

### 3.6 Ejecución
- Recién después de emitido el CO.
- Si se ejecuta antes "por urgencia" → riesgo de no cobrar.

### 3.7 Cierre
- Verificación de ejecución.
- Pago certificado dentro del próximo certificado mensual.

---

## 4. Análisis de impacto de plazo: time impact analysis

### 4.1 Cuándo aplica
- Cuando el cambio afecta tareas del camino crítico.
- Si afecta tarea no crítica con holgura: no necesariamente da prórroga.

### 4.2 Metodología
- Identificar tareas afectadas.
- Recalcular cronograma con la tarea adicional o modificada.
- Comparar fecha de fin nueva vs original.
- La diferencia es la prórroga solicitada.

### 4.3 Documentación
- Cronograma as-planned, as-built, as-impacted.
- Análisis paso a paso.

---

## 5. Claims: tipos comunes en AR

### 5.1 Mayores costos
- Por demora en aprobación de muestras / planos.
- Por demora en pagos del comitente (costo financiero).
- Por cambio normativo sobreviniente.
- Por escalada de precios no prevista contractualmente.

### 5.2 Mayores gastos generales / costos improductivos
- Cuando la obra se extiende por causa atribuible al comitente, los gastos generales se diluyen mal:
  - Obrador funcionando más tiempo.
  - Profesionales con salario continuando.
  - Equipos alquilados sin uso pleno.
- Reclamo: pago de gastos generales del período adicional.

### 5.3 Prórroga de plazo
- Por causa no atribuible al constructor.
- Sin extensión de costo si la causa es fuerza mayor.
- Con extensión de costo si la causa es el comitente.

### 5.4 Reclamo por aceleración
- Cuando el comitente pide acortar plazo más allá del plan.
- Mayor costo por turnos extras, mano de obra adicional, equipos.

---

## 6. Estructura de un claim

### 6.1 Componentes mínimos
1. **Hechos**: cronología documentada de lo ocurrido.
2. **Causa**: factor disparador atribuible a la otra parte.
3. **Impacto**: cómo afectó plazo / costo / calidad.
4. **Cuantificación**: monto reclamado con cálculo verificable.
5. **Documentación**: libro de obra, RFIs, fotos, partes diarios, planos as-planned vs as-built, cronograma.
6. **Pretensión**: monto + prórroga + ajustes.

### 6.2 Notificación
- Fehaciente (carta documento o medio contractualmente válido).
- Dentro del plazo contractual (típicamente 15-30 días desde el hecho).
- Notificación tardía = pérdida del derecho al reclamo en muchos contratos.

### 6.3 Resolución
- Negociación directa primero.
- Mediación.
- Arbitraje (si contrato lo prevé).
- Juicio (último recurso).

---

## 7. Redeterminación vs change order vs claim

| Mecanismo | Disparador | Resultado |
|---|---|---|
| **Redeterminación** | Inflación / variación de índices | Ajuste de precio del contrato vigente |
| **Change order** | Cambio de alcance o aceleración acordada | Modificación bilateral del contrato |
| **Claim** | Incumplimiento, demora o evento no acordado | Reclamo unilateral a negociar |

> Ver `./certificacion-obra.md` § 5 para mecánica de redeterminación.

---

## 8. Buenas prácticas para evitar claims

### 8.1 Contrato bien armado
- Alcance preciso con plano y spec.
- Mecanismo claro de redeterminación.
- Plazos de notificación de cambios y claims.
- Resolución de disputas (mediación / arbitraje pactado).
- Cláusula clara de aceleración.

### 8.2 Documentación impecable
- Libro de obra completo y firmado.
- RFIs respondidos en plazo.
- Partes diarios completos.
- Fotos datadas.
- Cronograma actualizado mensualmente.
- Minutas de reunión circuladas.

### 8.3 Gestión proactiva
- Detectar el problema antes de que se materialice.
- Reportar en reunión y registrar en minuta.
- Cotizar antes de ejecutar.
- No "hacer y después facturar".

### 8.4 Comunicación
- Cuando hay disenso, escalar formalmente.
- No dejar el reclamo para el final de la obra.

---

## 9. Negociación de claims (técnica)

### 9.1 Apertura
- Plantear el monto bien fundamentado.
- Anclar en hechos concretos y documentados.
- Evitar agregados emocionales.

### 9.2 Posición vs interés
- La posición es el monto; el interés es la salida pragmática (cobrar rápido, mantener relación, terminar la obra).
- Buscar acuerdos que satisfagan interés sin requerir admisión total de la posición.

### 9.3 Trade-offs
- Reducción de monto a cambio de pago rápido.
- Renuncia parcial a cambio de obra futura.
- Compensación cruzada de varios items.

### 9.4 Salida
- Acta-acuerdo con renuncia a reclamo futuro por los hechos cubiertos.
- Pago en cuotas si aplica.
- Cierre limpio.

---

## 10. Errores comunes

- Ejecutar el cambio antes de firmar el CO → no se cobra después.
- No notificar el claim a tiempo → caduca el derecho.
- "Anotar todo de palabra" en libro de obra: no alcanza, hay que cuantificar e impactar el cronograma.
- Cotizar el CO mal (precio sin gastos generales) → recortar margen para siempre.
- Confundir redeterminación con CO → pelear por algo que ya está en el contrato.
- No tener cronograma as-planned firmado al inicio → cualquier análisis posterior es discutible.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** diferencia CO vs claim, procedimiento de gestión, mecanismos contractuales (redeterminación, prórroga, aceleración), documentación requerida.
- **🔴 Volátil:** montos típicos de gastos generales (varían por contrato), porcentajes de margen sobre CO (varían), tipos de cláusulas específicas (varían por borrador).

---

**Ver también:**
- `./certificacion-obra.md`
- `./modalidades-contratacion.md`
- `./documentacion-obra.md`
- `./gestion-diaria-obra.md`
- `../02-normativa/ccyc-locacion-obra.md`
- `../10-estrategia/gestion-riesgos.md`
