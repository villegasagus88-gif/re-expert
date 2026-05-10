---
title: "Certificación de obra y mecanismos de pago"
topic: "construccion"
subtopic: "certificacion-obra"
jurisdiction: "Nacional"
last_verified: "2026-05-10"
sources:
  - "CCyCN locación de obra"
  - "Decreto 1295/02 — redeterminación obra pública"
  - "Cámara Argentina de la Construcción — pliegos"
keywords: [certificacion, certificado, anticipo, retencion, gastos generales, redeterminacion, costo + honorarios, ajuste alzado]
audience: ["desarrollador", "constructor", "director de obra"]
confidence: "alta"
---

# Certificación de obra

## TL;DR
- **Certificado**: documento que valida el avance de obra ejecutado en un período (típicamente mensual).
- Es la base del **pago** al constructor + el control de avance.
- Cada certificado contiene: medición, precio unitario, monto del período, acumulado, descuentos, redeterminación.
- Buenas prácticas: medición conjunta, libro de obra firmado, fotos, planillas.

---

## 1. Tipos de certificado

### 1.1 De anticipo
- Único: al inicio del contrato.
- Típicamente 10–20% del total.
- Suele requerir **póliza de caución**.

### 1.2 De avance / parcial
- Mensual.
- Se mide lo ejecutado en el mes y se pondera al precio.

### 1.3 De ajuste / redeterminación
- Mensual o trimestral según contrato.
- Suma o resta el efecto del índice.

### 1.4 De recepción provisional
- A la finalización de la obra.
- Inicio del plazo de garantía.

### 1.5 De recepción definitiva
- Al cumplir el plazo de garantía sin observaciones.
- Liberación de retenciones.

---

## 2. Estructura de un certificado

### 2.1 Datos generales
- Empresa, obra, período, número de certificado.
- Director de obra, profesionales firmantes.
- Cantidad de personal.

### 2.2 Cómputo de avance
- Por capítulo / por rubro.
- Cantidades unitarias acumuladas hasta el mes.
- Cantidades del mes (acumulado actual − acumulado anterior).

### 2.3 Valuación
- Cantidades x precio unitario contractual = monto del mes por rubro.

### 2.4 Conceptos sumados
- Adicionales aprobados.
- Redeterminación del período.
- Reintegro de gastos cuando aplique.

### 2.5 Conceptos descontados
- Amortización del anticipo (proporcional).
- Retención de fondos de reparo (5–10%).
- Retenciones impositivas (IVA, IIBB, Ganancias).
- Multas por incumplimiento (cuando aplica).
- Adelantos del período.

### 2.6 Neto a pagar
- Resultado final que se factura.

---

## 3. Anticipo financiero

### 3.1 Para qué sirve
- Cubrir movilización inicial: traslado de equipos, compra de materiales críticos, instalación obrador.

### 3.2 Garantía
- Póliza de caución por el monto del anticipo.

### 3.3 Recupero
- Se descuenta de cada certificado proporcionalmente al avance.
- Algunos contratos: descuento lineal (si anticipo es 10%, se descuenta 10% de cada certificado hasta amortizar).

---

## 4. Retención de fondos de reparo

### 4.1 Concepto
- Porcentaje retenido (5–10%) sobre cada certificado.
- Garantía contra vicios y defectos durante el período de garantía.

### 4.2 Liberación
- Mitad al recibir provisionalmente la obra.
- Mitad al recibir definitivamente (pasado el período de garantía).

### 4.3 Sustitución
- En algunos contratos, el constructor puede sustituir la retención por una **póliza de caución** equivalente y cobrar el 100% del certificado.

---

## 5. Redeterminación de precios

### 5.1 Cuándo aplica
- En contextos inflacionarios o cuando el contrato lo prevé.
- Periodicidad: mensual, trimestral, semestral.

### 5.2 Fórmula polinómica
- Combinación ponderada de índices de los componentes del costo:
  - Materiales (varios subíndices: cemento, hierro, madera, etc.).
  - Mano de obra.
  - Equipos.
  - Gastos generales.

### 5.3 Mecánica
$$ P_n = P_0 \cdot \frac{\sum_i w_i \cdot I_{i,n}}{\sum_i w_i \cdot I_{i,0}} $$

Donde:
- P₀: precio original.
- Pₙ: precio redeterminado.
- wᵢ: peso de cada componente.
- Iᵢ,n: índice del componente al período n.
- Iᵢ,0: índice del componente al período base.

### 5.4 Decreto 1295/02 (obra pública)
- Régimen de referencia para obra pública nacional.
- Aplicado supletoriamente como práctica del mercado privado.

---

## 6. Gastos generales

### 6.1 Componentes típicos
- Obrador (oficina, depósito, sanitarios).
- Profesionales en obra (director, jefe, capataz general).
- Servicios (luz, agua, teléfono, conectividad).
- Vigilancia.
- Limpieza.
- Equipos menores.
- Seguros.
- Tasas y permisos.
- Vehículos.

### 6.2 Imputación
- Como % del costo directo (típicamente 8–15%).
- Cuando el período se prolonga: hay reclamos de **mayores gastos generales** ("costos improductivos").

---

## 7. Aprobación del certificado

### 7.1 Procedimiento estándar
1. Constructor presenta certificado al Director de Obra.
2. Medición conjunta en obra (con libro firmado).
3. Director de Obra aprueba/observa.
4. Si aprobado → factura del constructor.
5. Pago dentro del plazo contractual (30/60 días típicos).

### 7.2 Plazos contractuales
- Presentación: dentro de los 5–10 días del cierre del mes.
- Aprobación: 10–15 días.
- Facturación: tras aprobación.
- Pago: 30–60 días desde la factura.

### 7.3 Discrepancias
- Acta de divergencias.
- Pago de la parte no controvertida.
- Resolución por mediación / arbitraje / juicio según contrato.

---

## 8. Documentación de respaldo

- **Libro de Órdenes** firmado.
- **Libro de Asistencia** del personal.
- **Planillas de medición** firmadas por ambas partes.
- **Fotos** datadas.
- **Reportes de inspecciones** (estructura, instalaciones).
- **Comprobantes de aportes** del personal (F931).
- **Certificados ART**.

> Ver `./documentacion-obra.md`.

---

## 9. Errores comunes

- No medir conjuntamente → discusión cada certificado.
- No descontar anticipo correctamente.
- No documentar redeterminación → reclamo retroactivo.
- Pagar sin verificar F931 y aportes.
- Liberar fondos de reparo antes de la recepción definitiva.

---

## 10. Reglas operativas para el chat

- **Estable y respondible:** estructura del certificado, lógica de anticipo y retención, fórmula de redeterminación, mecánica de aprobación.
- **🔴 Volátil:** valor actual de los índices, plazos y porcentajes específicos según contrato.

---

**Ver también:**
- `./modalidades-contratacion.md`
- `./documentacion-obra.md`
- `./final-obra.md`
- `../06-financiero/cashflow-real-estate.md` (TBD)
