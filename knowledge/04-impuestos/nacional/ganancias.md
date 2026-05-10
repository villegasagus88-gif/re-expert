---
title: "Impuesto a las Ganancias — RE y desarrollo inmobiliario"
topic: "impuestos"
subtopic: "ganancias"
jurisdiction: "Nacional"
last_verified: "2026-05-10"
sources:
  - "Ley 20.628 — Impuesto a las Ganancias (texto ordenado y modif.)"
  - "Decreto 862/2019 reglamentario y modificaciones posteriores"
  - "AFIP — micrositio Ganancias"
keywords: [ganancias, ley 20628, primera categoria, tercera categoria, alquiler, venta inmueble, persona humana, persona juridica, deducciones]
audience: ["desarrollador", "inversor", "contador", "abogado tributario"]
confidence: "alta"
---

# Impuesto a las Ganancias — RE

## TL;DR
- Grava la renta o ganancia de fuente argentina (y mundial, para residentes).
- 4 categorías: 1ª renta del suelo (alquileres), 2ª capital (intereses, etc.), 3ª empresarial (developer), 4ª trabajo personal.
- **Persona humana**: escala progresiva por tramos.
- **Persona jurídica**: tasa fija (verificar tasa vigente).
- **Venta de inmuebles** por persona humana NO afectados a actividad: tributa por **Cedular** (impuesto separado), no por Ganancias general — ver `cedular-inmuebles.md`.
- 🔴 Volátil: tasas, mínimos no imponibles, deducciones generales y especiales, escala vigente. Verificar AFIP.

---

## 1. Categorías relevantes

### 1.1 Primera categoría — renta del suelo (art. 41)
Comprende:
- Locación de inmuebles urbanos y rurales.
- Cesión gratuita de inmuebles (valor locativo presunto).
- Sublocación: diferencia.
- Mejoras hechas por el inquilino que quedan al locador (cuando no se compensan).

Deducciones admitidas (art. 85 y reglamento):
- Impuestos y tasas vinculados al inmueble (Inmobiliario, ABL, etc.).
- Amortización del edificio (2% anual sobre el valor de construcción).
- Gastos de mantenimiento (régimen real o presunto del 5%).
- Intereses de hipoteca afectada al inmueble en alquiler.
- Honorarios de administración.

### 1.2 Tercera categoría — empresarial (art. 53)
Comprende rentas de empresas y explotaciones (incluido el developer).

Aplicable a:
- Desarrollador como persona humana con actividad organizada.
- SA, SRL, SAS, fideicomisos comerciales.
- Compraventa habitual de inmuebles.

### 1.3 Cuándo el alquiler pasa de 1ª a 3ª categoría
- Si el contribuyente actúa con organización empresaria (varias UFs, equipo, estructura): la renta puede recategorizarse como 3ª.

---

## 2. Persona humana — escala y tratamientos

### 2.1 Escala progresiva
- Tramos que van desde tasa baja al tramo máximo.
- Cifras 🔴 volátiles: verificar la escala vigente en AFIP.

### 2.2 Mínimo no imponible y deducciones personales
- Mínimo no imponible.
- Deducción especial.
- Cargas de familia (cónyuge, hijos).
- 🔴 Montos volátiles.

### 2.3 Deducciones generales (art. 85)
- Gastos médicos (hasta tope).
- Aportes a obra social y prepaga.
- Donaciones (con tope).
- Intereses de crédito hipotecario para vivienda única (con tope histórico, verificar vigencia).
- Alquiler de vivienda (40% con tope, sujeto a condiciones).

---

## 3. Persona jurídica — sociedad

### 3.1 Tasa
- Régimen escalonado por monto de utilidades imponibles, con tasa máxima cercana al 35% históricamente. Verificar tasa vigente.

### 3.2 Distribución de dividendos
- Retención sobre dividendos distribuidos a personas humanas (verificar tasa).

### 3.3 Deducciones permitidas
- Gastos necesarios para obtener, mantener y conservar la ganancia gravada.
- Amortizaciones.
- Intereses pagados.
- Sueldos y cargas sociales.
- Materiales y servicios incorporados al costo.

---

## 4. Venta de inmuebles — qué régimen aplica

### 4.1 Persona humana NO habitualista
- Inmueble adquirido **antes del 1-ene-2018**: NO está alcanzado por Ganancias ni Cedular (ITI, en cambio, sí — ver más abajo).
- Inmueble adquirido **a partir del 1-ene-2018**: tributa **Impuesto Cedular a la transferencia de inmuebles** (15% sobre la ganancia, con cómputo de costo actualizado).

> Ver `./cedular-inmuebles.md` para detalle.

### 4.2 Persona habitualista (compra-venta como negocio)
- Tributa por Ganancias 3ª categoría sobre la ganancia.

### 4.3 Persona jurídica
- Siempre 3ª categoría: la ganancia neta integra la base.

### 4.4 Vivienda única
- Régimen de **reemplazo de vivienda** (art. 71): permite diferir el impuesto si se reinvierte en otro inmueble destinado a vivienda dentro del plazo legal.

---

## 5. ITI — Impuesto a la Transferencia de Inmuebles (Ley 23.905)

### 5.1 Cuándo aplica
- Personas humanas no afectadas a actividad, vendedoras de inmuebles **adquiridos antes del 1-ene-2018**.
- Tasa: 1,5% sobre el precio de transferencia.
- Pago: por el escribano al momento de la escritura.

### 5.2 Cuándo NO aplica
- Si aplica Cedular (inmueble adquirido post 2018).
- Si se opta por reemplazo de vivienda con certificado de no retención.

### 5.3 Certificado de no retención
- Por reemplazo de vivienda única dentro del plazo de 1 año (antes o después).
- Tramitado en AFIP.

---

## 6. Rentas presuntas y valor locativo

### 6.1 Inmueble cedido gratuitamente
- Se imputa un **valor locativo presunto** equivalente al alquiler de mercado.
- Aplica a 1ª categoría.

### 6.2 Inmueble usado por el dueño y por familiares
- Si lo usa el propio contribuyente como casa-habitación: no tributa.
- Si lo usa otro familiar gratuitamente: valor locativo presunto.

---

## 7. Fideicomisos en Ganancias

### 7.1 Fideicomiso ordinario sujeto a Ganancias
- Tributa como persona jurídica (3ª categoría).
- Distribución a beneficiarios: tratamiento de dividendos.

### 7.2 Fideicomiso al costo (no comercial)
- Consideración: cada fiduciante-beneficiario tributa como si fuese dueño directo.
- Específico: ver `../estructuras-fiscales/fideicomiso-al-costo.md`.

### 7.3 Fideicomiso financiero
- Régimen específico — ver `../estructuras-fiscales/fideicomiso-financiero.md`.

---

## 8. Quebrantos

### 8.1 Quebranto general
- Compensable con ganancias del mismo período.
- Trasladable hacia adelante por **5 ejercicios**.

### 8.2 Quebrantos específicos
- Inversiones en acciones, instrumentos derivados: solo compensables con ganancias de la misma fuente.

---

## 9. Liquidación e ingreso

### 9.1 Persona humana
- DDJJ anual (vencimiento típico junio del año siguiente).
- Anticipos durante el año (5 anticipos sobre el impuesto del período anterior).

### 9.2 Persona jurídica
- DDJJ anual al cierre del ejercicio fiscal.
- 10 anticipos durante el ejercicio siguiente.

### 9.3 Régimen de retención
- RG 830/00 AFIP: retenciones sobre pagos por servicios, locaciones, etc.
- RG 2139/06 y otras para casos específicos.

---

## 10. Errores comunes

- Confundir alquiler de 1ª con 3ª cuando hay actividad organizada.
- No actualizar la base de costo al vender un inmueble (afecta el cómputo del Cedular).
- No optar por reemplazo de vivienda cuando corresponde.
- Olvidar la amortización del 2% anual del edificio en 1ª categoría.
- Imputar gastos personales al inmueble en alquiler.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** estructura del impuesto, categorías, sujetos, deducciones permitidas en concepto, lógica del régimen de inmueble pre/post 2018, ITI vs Cedular, reemplazo de vivienda.
- **🔴 Volátil — derivar a AFIP / contador:** escala vigente para personas humanas, mínimos no imponibles, tasas para sociedades, montos de retenciones, planillas y formularios concretos.

---

**Ver también:**
- `./cedular-inmuebles.md`
- `./bienes-personales.md`
- `./iva.md`
- `../estructuras-fiscales/comparativa-vehiculos.md`
