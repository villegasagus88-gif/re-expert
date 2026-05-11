---
title: "ABL (CABA) y TSG (municipios PBA)"
topic: "impuestos"
subtopic: "abl-tsg"
jurisdiction: "Municipal — CABA + PBA"
last_verified: "2026-05-11"
sources:
  - "Código Fiscal CABA — AGIP"
  - "Códigos Fiscales municipales PBA (Pilar, Tigre, Vicente López, San Isidro, La Plata, etc.)"
  - "Ordenanzas tarifarias anuales"
keywords: [abl, alumbrado barrido limpieza, tsg, tasa servicios generales, caba, pba, municipios, contribuyente, base imponible]
audience: ["desarrollador", "propietario", "contador", "chat"]
confidence: "alta"
---

# ABL (CABA) y TSG (PBA)

## TL;DR
- **ABL** (Alumbrado, Barrido y Limpieza) en CABA — recauda AGIP.
- **TSG / Tasa Servicios Generales / Servicios Indirectos** en municipios PBA — recauda cada municipio.
- En interior: nombres varían (Tasa General de Inmuebles en Santa Fe; Contribución Inmobiliaria en Mendoza; etc.).
- Es un tributo sobre el inmueble; lo paga el titular registral o usufructuario.
- Cuotas mensuales o bimestrales; ajuste anual por ordenanza tarifaria.
- 🔴 Alícuotas y valuación cambian anualmente — verificar AGIP / municipio.

## 1. ABL — CABA

### 1.1 Hecho imponible
- Tenencia de inmueble en CABA.
- Servicios financiados: alumbrado, barrido, limpieza, conservación de calles y plazas.

### 1.2 Contribuyente
- Titular del dominio.
- Usufructuario.
- Poseedor a título de dueño (boleto consolidado).

### 1.3 Base imponible
- **Valuación fiscal** del inmueble.
- Componentes: valor del terreno + valor de las construcciones.
- Se actualiza periódicamente por AGIP.

### 1.4 Tarifa
- Tarifa progresiva por tramos de valuación fiscal.
- Bonificaciones: pago anual adelantado (descuento), pago al día.
- Exenciones: jubilados con vivienda única e ingresos bajo tope, mutuales, organizaciones civiles, otros casos puntuales.

### 1.5 Vencimientos
- Cuotas distribuidas a lo largo del año (típicamente bimestrales o mensuales según partida).

### 1.6 Mora
- Intereses resarcitorios + punitorios.
- Embargo administrativo si la deuda es alta.

### 1.7 Trámites comunes
- Cambio de titularidad (al escriturar): obligatorio para que la próxima boleta llegue al nuevo titular.
- División o unificación de partidas.
- Reclamo de valuación: vía recurso administrativo.

## 2. TSG / equivalentes — PBA

### 2.1 Variaciones por municipio
- Cada municipio bonaerense tiene su tasa de servicios generales.
- Nombres: TSG, Tasa por Servicios Indirectos, Servicios Generales.
- Cobertura: alumbrado, barrido, limpieza, mantenimiento.

### 2.2 Base
- Generalmente sobre valuación municipal del inmueble + frente / superficie.
- Algunos municipios incorporan zonas tarifarias (barrios distintas tarifas).

### 2.3 Acumulación con impuesto inmobiliario provincial
- En PBA conviven:
  - **Impuesto Inmobiliario** (provincial — ARBA).
  - **TSG** (municipal).
- No se grava dos veces el mismo concepto, pero son tributos distintos por hechos distintos (servicios vs. propiedad).

### 2.4 Trámites
- Mismo esquema: cambio titularidad, división, reclamo de valuación.

## 3. Interior — equivalentes (ejemplos)

| Provincia / capital | Nombre típico |
|---|---|
| Santa Fe (Rosario, Santa Fe ciudad) | Tasa General de Inmuebles (TGI) |
| Córdoba Capital | Contribución sobre los Inmuebles |
| Mendoza | Tasa Municipal por Servicios |
| Tucumán | Contribución que incide sobre Inmuebles |
| Neuquén | Tasa por Servicios Retributivos |

> En cada provincia ver `../provincial/{provincia}.md` para el detalle de su régimen tributario, y dentro de eso el remitir al municipal.

## 4. Cómo computar ABL/TSG en el flujo de un proyecto

### 4.1 Durante la obra
- Si el inmueble es un terreno baldío: ABL/TSG por valuación del terreno.
- Algunos códigos prevén alícuotas mayores para baldíos urbanos (incentivo a construir).

### 4.2 Durante el período de venta de unidades
- Hasta que se subdivide y se generan partidas individuales por UF, el ABL del proyecto sigue siendo del developer/fideicomiso.
- Al subdividir (PH), se generan partidas por UF.

### 4.3 Pasaje al comprador
- Al escriturar, la boleta de ABL pasa al adquirente.
- Imprescindible **libre deuda** ABL al momento de escriturar.

## 5. ABL como variable de costo del proyecto

- Para análisis de factibilidad, estimar ABL del proyecto entero por valuación fiscal proyectada.
- Pequeño en magnitud (típicamente fracción de 1% anual sobre valuación) pero relevante si la obra se demora.
- Para PH ya entregada: cargar al gasto operativo de la UF (no expensa común, salvo amenities comunes).

## 6. Errores comunes

- Asumir que el ABL del comprador empieza a contar al escriturar — en muchas operaciones el comprador asume desde la posesión.
- No pedir libre deuda ABL antes de la escritura.
- Confundir ABL (municipal) con impuesto inmobiliario (provincial) — son dos tributos distintos.
- Olvidar que la valuación fiscal AGIP cambia con cada nuevo Código Urbanístico / reordenamiento.

## 7. Reglas operativas para el chat

- **Estable:** quién es contribuyente, hecho imponible, sobre qué base, lógica de bonificaciones, libre deuda al escriturar.
- **🔴 Volátil — derivar:**
  - Alícuotas y valuación fiscal actual → AGIP (caba.gob.ar/agip) o municipio.
  - Monto en pesos del año.
  - Plan de facilidades vigente.
- Si la pregunta es "¿cuánto pago de ABL?", responder con metodología + derivar a calculador AGIP / boleta del inmueble.

## Ver también
- `./derechos-construccion.md`
- `./tasas-municipales.md`
- `./contribuciones-y-plusvalia.md`
- `../provincial/caba.md`
- `../provincial/pba.md`
