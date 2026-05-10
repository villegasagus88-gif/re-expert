---
title: "IVA aplicado a desarrollo inmobiliario y locación"
topic: "impuestos"
subtopic: "iva"
jurisdiction: "Nacional"
last_verified: "2026-05-10"
sources:
  - "Ley 23.349 — IVA (texto ordenado 1997 con modificaciones)"
  - "Decreto 692/98 — Reglamentación"
  - "AFIP — micrositio IVA (afip.gob.ar)"
keywords: [iva, ley 23349, obra sobre inmueble propio, locacion, alicuota, credito fiscal, debito fiscal, exencion, vivienda]
audience: ["desarrollador", "contador", "abogado tributario"]
confidence: "alta"
---

# IVA — desarrollo inmobiliario y locación

## TL;DR
- IVA grava la **venta de cosa mueble**, **obra sobre inmueble propio** (developer), **prestaciones y locaciones de servicios**, e importaciones.
- La **venta de inmuebles entre privados sin construcción nueva NO está alcanzada**.
- **Obra sobre inmueble propio** del developer SÍ está alcanzada (art. 3 inc. b).
- Locación con destino vivienda: **exenta** hasta cierto monto mensual; comercial: **gravada**.
- Alícuota general 21%; alícuota reducida 10,5% para algunas obras nuevas destinadas a vivienda (con condiciones).
- 🔴 Volátil: alícuotas vigentes, montos mínimos, percepciones. Verificar AFIP.

---

## 1. Hechos imponibles relevantes para RE (art. 1)

### 1.1 Venta de cosa mueble en el país
- Materiales de construcción: gravados al venderse al contratista.
- Equipamiento: gravado.

### 1.2 Obra sobre inmueble propio (art. 3 inc. b)
- **Empresa constructora** (sentido amplio: cualquiera que construya con propósito de lucro o para vender) es sujeto de IVA cuando vende la UF o el inmueble construido.
- Diferencia clave con un particular: el particular que vende su casa NO está alcanzado. El developer SÍ.

### 1.3 Locaciones y prestaciones de servicios (art. 3 inc. e)
- Honorarios de proyecto, dirección, construcción.
- Servicios profesionales: gravados.

### 1.4 Locación de inmuebles
- Habitacional: **exenta** hasta el tope que fije AFIP (art. 7, modificado por leyes y resoluciones — verificar tope vigente).
- Comercial / industrial: **gravada** al 21%.
- Turística (alquiler temporario): tratamiento específico — verificar.

---

## 2. Sujetos

### 2.1 Empresa constructora (art. 4)
- Quien construye, directamente o a través de terceros, sobre inmueble propio, **con la intención de obtener lucro de la enajenación**.
- Incluye al developer aunque no construya con sus propias manos.
- Incluye al fideicomiso al costo o a la SAS dueña del proyecto.

### 2.2 Inscripción
- Responsable Inscripto: caso típico developer.
- Monotributo: posible para profesionales individuales con tope de facturación (verificar).
- Exento: no aplica para developer.

---

## 3. Base imponible

### 3.1 Venta de obra sobre inmueble propio
- Precio total de la operación menos:
  - Valor del **terreno** (dado que el terreno en sí no es obra).
  - Conceptos no integrantes (intereses pactados separadamente, etc.).
- Resultado: la base es el **valor agregado por la construcción + utilidad**.

### 3.2 Locación gravada
- Precio del alquiler.

### 3.3 Servicios
- Honorarios netos.

---

## 4. Alícuotas

### 4.1 General
- **21%** sobre la base.

### 4.2 Reducida 10,5%
Aplica a (entre otros, verificar versión vigente):
- Construcción de vivienda destinada a casa-habitación.
- Trabajos sobre inmueble propio cuando se trate de obras destinadas a vivienda.
- Algunas locaciones específicas.

### 4.3 Tasa cero / exenciones
- Exportaciones: tasa cero (con recupero de crédito fiscal).
- Locación habitacional bajo tope: exenta.

> 🔴 Las alícuotas reducidas y los topes de exención cambian. Verificar normativa vigente.

---

## 5. Crédito y débito fiscal

### 5.1 Crédito fiscal
- IVA pagado en compras vinculadas a la actividad gravada.
- Materiales, mano de obra contratada, honorarios profesionales, servicios.
- Para que sea computable: factura A, vinculación con la actividad gravada, registro contable.

### 5.2 Débito fiscal
- IVA generado en ventas/locaciones gravadas.

### 5.3 Saldo técnico vs saldo de libre disponibilidad
- Saldo técnico (DF < CF acumulado): se traslada al período siguiente.
- Saldo de libre disponibilidad: se origina en retenciones/percepciones sufridas; puede pedirse devolución o compensar otros impuestos.

---

## 6. Régimen específico de obra sobre inmueble propio

### 6.1 Momento del hecho imponible
- Al **transferir el dominio** (escritura) o al **otorgar la posesión**, lo que sea anterior (art. 5).

### 6.2 Cómo se factura
- A clientes consumidores finales: **factura B**.
- A clientes responsables inscriptos: **factura A**.

### 6.3 Anticipos y boletos
- Los pagos a cuenta antes de la entrega de posesión generan **percepciones** y **retenciones**, pero el hecho imponible se perfecciona al momento de la posesión/escritura.

---

## 7. Locación de inmueble destinado a vivienda

### 7.1 Exención
- Locación con destino vivienda, hasta monto mensual fijado por AFIP. Por encima del monto: gravada.
- Locador profesional o no: la exención aplica al destino, no al sujeto.

### 7.2 Locación comercial
- Gravada al 21%.
- Locador inscripto debe facturar con IVA.

### 7.3 Locación de cocheras separadas
- Si va con la vivienda en un mismo contrato: sigue la suerte de la vivienda.
- Si es contrato separado: tratamiento independiente.

---

## 8. Construcción para terceros vs obra sobre inmueble propio

| Concepto | Construcción para terceros | Obra sobre inmueble propio |
|---|---|---|
| Sujeto | Contratista | Developer |
| Hecho imponible | Servicio prestado | Venta del inmueble |
| Cuándo se devenga | Avance de obra / certificación | Posesión / escritura |
| Cliente | Comitente (developer, etc.) | Adquirente final |

---

## 9. Fideicomiso de construcción

- Fideicomiso al costo: el fiduciario actúa como representante de los fiduciantes-beneficiarios. Tratamiento del IVA: complejo, depende de la calificación.
- Fideicomiso ordinario con fines de lucro: sujeto IVA por la obra sobre inmueble propio.

> Ver `../estructuras-fiscales/fideicomiso-al-costo.md` y `fideicomiso-ordinario.md`.

---

## 10. Casos prácticos

### 10.1 Venta de UF nueva por developer
- Developer es sujeto de IVA.
- Base: precio menos terreno.
- Alícuota: 10,5% si destino vivienda y se cumplen condiciones; 21% otros casos.

### 10.2 Reventa de UF por particular no profesional
- No alcanzada.

### 10.3 Reventa de UF por inversor que es responsable inscripto
- Discusión doctrinaria. Si se considera "empresa constructora" (compra para vender), puede quedar alcanzada por la primera transferencia.

### 10.4 Alquiler de UF terminada por developer
- Si destino vivienda y bajo tope: exento.
- Si comercial: gravado.

---

## 11. Errores comunes

- Confundir "venta de inmueble" con "obra sobre inmueble propio" — el primero es no alcanzado (entre privados); el segundo SÍ.
- No deducir el valor del terreno de la base.
- No documentar el crédito fiscal con factura A.
- Asumir que toda construcción nueva está al 10,5% sin verificar las condiciones del régimen reducido.
- Olvidar las percepciones IVA en pagos durante el pozo.

---

## 12. Reglas operativas para el chat

- **Estable y respondible:** quién es sujeto, hechos imponibles, lógica de base imponible, diferencia entre obra sobre inmueble propio y construcción para terceros, exención de locación habitacional.
- **🔴 Volátil — derivar a AFIP / contador:** alícuotas vigentes, topes de exención, percepciones, casos límite (fideicomiso al costo, monotributista, dación en pago).

---

**Ver también:**
- `./ganancias.md`
- `./bienes-personales.md`
- `../estructuras-fiscales/fideicomiso-ordinario.md`
- `../estructuras-fiscales/fideicomiso-al-costo.md`
