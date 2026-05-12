---
title: "Compras y gestión de proveedores en obra"
topic: "construccion"
subtopic: "compras"
jurisdiction: "Argentina"
last_verified: "2026-05-12"
sources:
  - "Práctica habitual desarrollos AR"
  - "Cámara Argentina de la Construcción — pliegos referenciales"
keywords: [compras, proveedores, orden de compra, oc, homologacion, comparativa, terna, pedido de cotizacion, rfq, just in time, acopio, presupuesto, materiales criticos]
audience: ["desarrollador", "project manager", "jefe de obra", "comprador"]
confidence: "alta"
---

# Compras y gestión de proveedores

## TL;DR
- Ahorro de obra **se gana o se pierde en compras**. Los gremios + materiales explican 70-85% del costo directo.
- Materiales **críticos** (estructura, fachada, ascensores, climatización) requieren comparativa por terna mínimo + homologación técnica.
- La **orden de compra (OC)** es el contrato real con el proveedor. El email no alcanza.
- Política habitual: 30/50/20 = anticipo / entrega / instalación-aprobación.

---

## 1. Clasificación de compras

### 1.1 Por criticidad
- **A** (críticos, alto valor, largo lead time): estructura metálica, ascensores, fachada, climatización, generadores. Requieren homologación previa, comparativa y plan de seguimiento.
- **B** (importantes, valor medio): pisos, aberturas, sanitarios, griferías. Comparativa y muestras aprobadas.
- **C** (commodities, bajo valor unitario, alta rotación): ferretería, EPP, materiales secos. Compras recurrentes con proveedores homologados.

### 1.2 Por momento
- **Pre-obra**: estructura, hormigón premezclado, hierro, mano de obra estructura.
- **Casco**: mampostería, instalaciones gruesas, contrapisos, carpetas.
- **Terminaciones**: pisos, revestimientos, aberturas, sanitarios, pintura.
- **Fin de obra**: muebles fijos, electrodomésticos, climatización, ascensores.

---

## 2. Proceso de compra estándar

### 2.1 Detección de necesidad
- Disparada por el cronograma + cómputo métrico.
- Lead time del rubro determina el momento del pedido.

### 2.2 Especificación
- Plano + spec + protocolo de aceptación.
- En commodities: catálogo o norma IRAM.

### 2.3 Pedido de cotización (RFQ)
- A terna como mínimo (3 proveedores).
- Mismo alcance, misma forma de pago, mismo plazo de entrega, mismas condiciones técnicas.

### 2.4 Comparativa
- Planilla con columnas: precio, plazo, forma de pago, garantía, alcance incluido / excluido, antigüedad del proveedor, referencias.
- Ojo con la "comparativa de oferta más barata": el alcance puede ser distinto.

### 2.5 Negociación
- Sobre precio, plazo, forma de pago, garantía.
- En commodities con volumen recurrente: precio fijo trimestral o convenio anual con ajuste por índice.

### 2.6 Adjudicación + OC
- OC firmada antes de iniciar fabricación o despacho.
- Sin OC ≠ pedido.

### 2.7 Seguimiento
- Status calls con proveedores A (semanal).
- Aviso anticipado de despacho.

### 2.8 Recepción + control
- Remito conforme alcance.
- Inspección visual + control técnico.
- Aceptación o rechazo por escrito.

### 2.9 Liquidación + pago
- Factura cruzada con OC y remito.
- Pago según forma pactada.

---

## 3. Homologación de proveedores

### 3.1 Por qué
- Estandariza calidad y reduce riesgo.
- Acelera compras recurrentes.

### 3.2 Criterios típicos
- Antigüedad (mínimo 3-5 años en el rubro).
- Capacidad financiera (situación BCRA, balance último ejercicio).
- Referencias verificables (obras similares).
- Cumplimiento impositivo (constancia AFIP, no estar en bases de problemáticos).
- Capacidad técnica (planta, equipos, dotación).
- ART + ARL al día (si tiene personal en obra).
- Cumplimiento ambiental cuando aplica.

### 3.3 Lista negra
- Proveedores que fallaron por calidad, plazo o solvencia → registrados.
- Política: no se vuelve a comprar sin justificación explícita.

---

## 4. Orden de compra (OC)

### 4.1 Datos mínimos
- Número correlativo.
- Fecha.
- Proveedor (razón social, CUIT).
- Obra / proyecto / centro de costo.
- Descripción detallada del item, cantidad, unidad, precio unitario, precio total.
- Forma de pago.
- Plazo de entrega.
- Lugar de entrega.
- Condiciones particulares (muestra previa, certificado de origen, garantía, etc.).
- Firma autorizada.

### 4.2 Niveles de aprobación
- Política habitual:
  - Hasta X (5-10% del paquete): jefe de obra.
  - Hasta Y (10-30%): project manager.
  - Sobre Y: developer / directorio.

### 4.3 OC vs contrato
- En compras < X miles de USD: OC alcanza.
- Compras grandes (estructura, ascensores): contrato + OC.

---

## 5. Forma de pago habitual por categoría

| Categoría | Forma típica AR | Observaciones |
|---|---|---|
| Hormigón premezclado | 30 días fecha factura | Reglas comerciales del sector |
| Hierro | Contado / 7-15 días | Bajo riesgo financiero del proveedor |
| Estructura metálica | 30/50/20 | Anticipo / entrega / montaje |
| Aberturas alto valor | 40/40/20 | Anticipo importante por fabricación |
| Ascensores | 30/30/40 | Anticipo + intermedios + entrega operativa |
| Pisos / revestimientos | 50/50 | Anticipo + entrega |
| Sanitarios / griferías | Contado / 30 días | Stock proveedor |
| Mano de obra (subcontratista) | Certificación mensual | Ver `./gestion-subcontratistas.md` |

> Valores típicos del mercado AR. Negociables.

---

## 6. Materiales críticos: gestión específica

### 6.1 Identificación
- Por lead time > 60 días.
- Por valor > 5% del presupuesto.
- Por baja sustituibilidad.

### 6.2 Gestión
- Lock-in temprano (apenas se aprueba presupuesto, se firma OC).
- Plan de control de fabricación + visita a planta.
- Inspección antes del despacho.
- Plan de contingencia (proveedor alternativo identificado).

### 6.3 Riesgo cambiario
- Si el proveedor importa o factura en USD: cláusula de ajuste.
- Si se paga en cuotas: ajuste por índice o por dólar oficial / MEP según contrato.

---

## 7. Acopio: cuándo conviene

### 7.1 A favor
- Hedging contra inflación.
- Lock de precio en commodities (hierro, hormigón cemento).
- Asegurar disponibilidad cuando hay restricciones (escasez de hierro 2022-2024).

### 7.2 En contra
- Capital inmovilizado (impacto cashflow).
- Riesgo de robo / rotura.
- Necesidad de espacio (a veces obrador no da).
- Riesgo de obsolescencia en terminaciones (cambio de spec).

### 7.3 Decisión
- Acopiar **commodities estructurales** cuando hay alta volatilidad de precio (típico contexto AR).
- No acopiar terminaciones (alto riesgo de cambio).
- Negociar con el proveedor **precio fijo** sin acopio físico cuando se puede.

---

## 8. Just-in-time (JIT)

### 8.1 Cuándo aplica
- Proveedores confiables, lead time corto, alta rotación.
- Obras urbanas con espacio limitado.

### 8.2 Riesgos
- Falla del proveedor → frena obra.
- Logística (atrasos en entrega) impacta directo en plan.

### 8.3 Mix recomendado
- Crítico = acopio anticipado o lock de fabricación.
- Recurrente / commodity = JIT con proveedor homologado y stock de seguridad bajo.

---

## 9. Indicadores de compras

- **Saving vs presupuesto** (% logrado vs base).
- **OTD** — On Time Delivery (% entregas en tiempo).
- **OTQ** — On Time Quality (% entregas en spec a la primera).
- **Lead time real vs comprometido**.
- **% de OCs sin desvío** (precio, plazo, cantidad).
- **Concentración de compra** (% del gasto en top-5 proveedores; sano: 40-60%).

---

## 10. Errores comunes

- Comprar a un solo proveedor por "es el de siempre" → sin comparativa, sin saving.
- OC verbal o por mail → conflicto al recibir.
- No homologar proveedor crítico → falla por solvencia.
- Spec ambigua → discusión en recepción.
- No coordinar lead time con cronograma → frenadas evitables.
- Pago de anticipos sin cláusula de devolución.
- Olvidar la cláusula de **ajuste cambiario** en contexto AR → reclamo retroactivo.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** proceso de compra, criterios de homologación, contenido de OC, lógica de pagos por categoría, lógica acopio vs JIT.
- **🔴 Volátil:** valores específicos de precio, lead times concretos, condiciones puntuales del mercado AR (cambian por escenario macro).

---

**Ver también:**
- `./gestion-subcontratistas.md`
- `./logistica-acopio.md`
- `./certificacion-obra.md`
- `../14-costos-presupuesto/estructura-costos.md`
- `../14-costos-presupuesto/contingencias-imprevistos.md`
