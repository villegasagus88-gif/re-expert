---
title: "Cesión de boleto de compraventa"
topic: "suelo-dominio"
subtopic: "cesion-boleto"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CCyCN — arts. 1614-1631 (cesión de derechos)"
  - "CCyCN — art. 1170 (oponibilidad del boleto)"
keywords: [cesion boleto, cesion derechos, posicion contractual, pozo, comprador en pozo, transferir boleto, cesion contrato, notificacion al vendedor]
audience: ["desarrollador", "comprador", "abogado", "chat"]
confidence: "alta"
---

# Cesión de boleto

## TL;DR
- La cesión de boleto es la transferencia, del comprador original (cedente) a un tercero (cesionario), de los derechos y obligaciones del boleto.
- Marco: **cesión de derechos** (CCyCN 1614-1631) y **cesión de posición contractual** (CCyCN 1636-1640).
- Requiere **conformidad del vendedor** si hay obligaciones pendientes del comprador.
- Es la forma típica de "vender" una reserva o boleto de pozo antes de escriturar.
- Tiene implicancia fiscal (Ganancias, Cedular, Sellos en algunas jurisdicciones).

## 1. Marco legal

### 1.1 Cesión de derechos (CCyCN 1614)
- Transferencia de un derecho creditorio del cedente al cesionario.
- No requiere conformidad del deudor cedido (salvo pacto contrario), pero sí su **notificación** para que la cesión le sea oponible.

### 1.2 Cesión de posición contractual (CCyCN 1636)
- Cuando el contrato tiene prestaciones pendientes de ambas partes → cesión de TODA la posición contractual.
- **Requiere conformidad** del contratante cedido (el vendedor del boleto).

### 1.3 Cuál aplica al boleto
- Si el comprador ya pagó todo y solo le falta escriturar → cesión de derechos (notificación al vendedor).
- Si quedan saldos del precio → cesión de posición contractual (conformidad del vendedor).
- En la práctica AR, se llama "cesión de boleto" en ambos casos.

## 2. Operatoria típica

### 2.1 Documento
- **Contrato de cesión de boleto** firmado por:
  - Cedente (comprador original).
  - Cesionario (nuevo comprador).
  - Conformidad del vendedor (developer / titular).

### 2.2 Contenido mínimo
- Identificación del boleto original.
- Identificación de las partes (con DNI, estado civil, domicilio).
- Precio de la cesión.
- Saldo del precio pendiente del boleto + responsabilidad del cesionario por su pago.
- Notificación / conformidad del vendedor.
- Asentimiento conyugal si corresponde.
- Fecha cierta (certificación notarial).

### 2.3 Forma
- Instrumento privado (puede ser).
- Recomendable: certificación notarial para fecha cierta.
- En algunos casos, escritura pública (especialmente si el boleto era por escritura pública).

## 3. Implicancias fiscales

### 3.1 Ganancias / Cedular
- La cesión puede generar **ganancia para el cedente** (diferencia entre lo pagado y lo cobrado en la cesión).
- Régimen aplicable: **Cedular** (Ley 27.430) si la operación está alcanzada (inmuebles adquiridos a partir de 2018).
- Pre-2018: ITI (impuesto a la transferencia de inmuebles) si fue adquirido antes.

### 3.2 IVA
- Cesión entre particulares: no alcanzada.
- Cesión por sujeto del IVA (developer revendiendo posición): caso a analizar.

### 3.3 Sellos
- En CABA y muchas provincias, la cesión paga sellos (porcentaje del valor cedido o del saldo).
- Verificar jurisdicción del inmueble.

### 3.4 UIF
- Si la cesión supera tope de operaciones inmobiliarias → DD UIF (origen de fondos).

## 4. Cesión en proyectos de pozo

### 4.1 Casos típicos
- Inversor especulativo que compra al pozo y "rota" antes de escriturar.
- Comprador que necesita liquidez antes del cierre de obra.
- Reasignación entre socios del fideicomiso al costo.

### 4.2 Restricciones contractuales
- Muchos boletos en pozo limitan la cesión sin conformidad del developer.
- Algunos cobran un **arancel de cesión** (1-3% del precio del boleto).
- Otros exigen que el cesionario pase por la misma DD UIF que el original.

### 4.3 Prehorizontalidad
- Si el boleto original tenía cobertura del seguro de prehorizontalidad, la cesión debe mantenerla.
- El cesionario se subroga en la posición del cedente.

## 5. Riesgos a controlar

| Riesgo | Mitigación |
|---|---|
| Vendedor no conforma → cesión inoponible | Conformidad expresa y por escrito |
| Cedente no era titular del derecho | DD del boleto original |
| Doble cesión por el cedente | Notificación con fecha cierta |
| Cesión sin pagar sellos → multa fiscal | Liquidación correcta de sellos |
| Cesionario asume saldos sin saberlo | Cláusula clara y soportes |
| Falta de asentimiento conyugal | Pedir asentimiento si corresponde |

## 6. Cesión a título oneroso vs gratuito

### 6.1 Onerosa
- A cambio de precio.
- Tiene impacto fiscal en Ganancias.

### 6.2 Gratuita
- Donación de los derechos.
- Riesgo: acción de colación si el cesionario es heredero (CCyCN 2385-2391).
- Tributo: impuesto a la transmisión gratuita en algunas provincias (Buenos Aires, Entre Ríos).

## 7. Cesión y escritura final

- En la escritura final, **el vendedor escritura a favor del cesionario** (no del cedente).
- Si la cesión fue de derechos puros → vendedor reconoce al cesionario como adquirente.
- Si fue de posición contractual con conformidad → idem.
- El escribano pedirá la documentación completa de la cesión.

## 8. Errores comunes

- Ceder sin conformidad del vendedor cuando el boleto la exige.
- No pagar sellos de la cesión.
- No considerar el impacto en Ganancias / Cedular.
- Ceder y olvidar dar cuenta al banco si hay hipoteca involucrada.
- Doble cesión por descuido del cedente.

## 9. Reglas operativas para el chat

- **Estable:** marco legal CCyCN, requisitos, documentación, riesgos típicos.
- **🟡 Volátil — derivar:** alícuotas de sellos, alícuota de Cedular, impuesto a la donación por jurisdicción.
- **Sensible — derivar a profesional:** redacción del contrato, casos de conflicto, fiscalidad compleja.
- Recordar: si el boleto tiene saldo pendiente, la cesión requiere conformidad del vendedor.

## Ver también
- `./boleto-compraventa.md`
- `./escritura-y-rpi.md`
- `./prehorizontalidad.md`
- `../04-impuestos/nacional/cedular-inmuebles.md`
- `../04-impuestos/provincial/_overview.md`
- `../16-uif-blanqueo/`
