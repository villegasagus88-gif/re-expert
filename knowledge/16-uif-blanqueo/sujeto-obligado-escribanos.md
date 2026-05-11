---
title: "Escribanos como sujeto obligado UIF — Res. 21/2018"
topic: "uif-blanqueo"
subtopic: "escribanos"
jurisdiction: "Nacional"
last_verified: "2026-05-11"
sources:
  - "Resolución UIF 21/2018"
  - "Ley 25.246"
  - "Consejo Federal del Notariado Argentino"
keywords: [escribano, escribano sujeto obligado, resolucion uif 21 2018, ddc, kyc escribano, ros escribano, escritura, libre deuda, origen fondos]
audience: ["escribano", "comprador", "vendedor", "developer", "chat"]
confidence: "alta"
---

# Escribanos como sujeto obligado UIF — Resolución 21/2018

## TL;DR
- Los **escribanos** son sujetos obligados desde la Ley 25.246 y la Res. UIF 21/2018 detalla el régimen aplicable.
- En toda operación inmobiliaria que celebren, deben:
  - Identificar al cliente y al beneficiario final.
  - Aplicar DDC según el riesgo.
  - Verificar origen de fondos en operaciones grandes.
  - Reportar operaciones sospechosas a UIF.
  - Conservar documentación.
- Sus controles son la primera línea anti-lavado en RE.

## 1. Cuándo el escribano actúa como sujeto obligado

### 1.1 Operaciones alcanzadas (típicas en RE)
- Compraventa de inmuebles.
- Constitución de hipotecas.
- Cesión de derechos.
- Constitución y modificación de fideicomisos.
- Constitución y reforma de sociedades.
- Mandatos y poderes especiales para operaciones financieras.

### 1.2 Cuándo NO aplica
- Algunas certificaciones de firma o autenticaciones no implican el régimen completo (verificar caso).

## 2. Obligaciones específicas

### 2.1 Identificación del cliente
**Persona física**:
- DNI vigente.
- Domicilio real comprobado (servicio o constancia).
- Profesión / ocupación / actividad económica.
- CUIT / CUIL.
- Estado civil + cónyuge si aplica.

**Persona jurídica**:
- Estatuto y modificaciones.
- Acta autorizando la operación.
- Poderes vigentes.
- Inscripción en IGJ / Registro Público.
- Estados contables.
- **Beneficiario final** identificado (último controlante natural — accionista titular de >25%, o quien ejerza control efectivo).

### 2.2 Categorización por riesgo
- **Bajo riesgo**: cliente conocido, operación pequeña, origen claro.
- **Medio riesgo**: operación estándar.
- **Alto riesgo**: PEP, jurisdicción de riesgo, operación atípica, monto significativo.

### 2.3 Debida diligencia reforzada (alto riesgo)
- Mayor documentación.
- Aprobación por niveles superiores.
- Origen de fondos detallado.

### 2.4 Origen de fondos
- En operaciones por encima de umbrales: documentar origen.
- Aceptable: comprobantes de ingresos previos, ventas anteriores, herencias, créditos, aportes societarios, blanqueos.
- NO aceptable: explicaciones genéricas sin respaldo.

### 2.5 Perfil del cliente
- Coherencia entre operación y perfil económico.
- Cliente de bajos ingresos haciendo compra millonaria sin explicación → ROS.

### 2.6 PEP — Personas Expuestas Políticamente
- Identificar si el cliente o el beneficiario final es PEP.
- DDC reforzada obligatoria si lo es.
- Ver `./pep-personas-expuestas.md`.

### 2.7 Conservación
- Documentos de DDC, copias de operaciones: mínimo 10 años.

### 2.8 Capacitación
- El escribano y su personal deben capacitarse periódicamente.
- Registro de capacitaciones.

### 2.9 Oficial de cumplimiento
- En estudios grandes, designar oficial.
- En escribanos individuales, el propio escribano lo es.

## 3. Documentación típica en compraventa inmobiliaria

### 3.1 Del comprador
- DNI.
- CUIT/CUIL + constancia AFIP.
- Domicilio real comprobado.
- Profesión / actividad económica.
- Estado civil + acta matrimonio + asentimiento si aplica.
- Origen de fondos en operaciones grandes:
  - Declaración jurada Ganancias / Bienes Personales.
  - Comprobantes bancarios (acreditaciones).
  - Documentos de operaciones previas (escrituras de venta anteriores).
  - Declaración patrimonial certificada.
  - Adhesión a blanqueo si corresponde.

### 3.2 Del vendedor
- Mismo paquete que comprador.
- Adicionalmente: comprobante de propiedad (escritura previa).

### 3.3 De ambos
- Constancia de no inhibición.
- Constancia de no PEP (o declaración como PEP).
- Información del beneficiario final si actúan por persona jurídica.

## 4. ROS — cuándo reporta el escribano

### 4.1 Indicadores típicos
- Cliente que se resiste a aportar información.
- Operación a precio notoriamente fuera de mercado (sub o sobrevaluación).
- Pago de terceros sin vínculo con el cliente.
- Comprador con perfil económico claramente inferior al monto operado.
- Operaciones en cadena rápida sin lógica económica.
- Estructura societaria opaca sin justificación.
- Origen de fondos no documentado o documentado deficientemente.
- Jurisdicción de origen de fondos: paraísos fiscales sin justificación.
- Cliente PEP sin DDC reforzada disponible.

### 4.2 Procedimiento
- Reporte interno al oficial de cumplimiento.
- Reporte UIF online dentro del plazo.
- Confidencialidad absoluta (no se avisa al cliente).

## 5. Cómo prepararse antes de ir al escribano (perspectiva cliente)

### 5.1 Para evitar fricciones
- Reunir documentación con anticipación.
- Documentar origen de fondos antes de la operación.
- Si hay aportes de terceros, justificarlos previamente.
- Si es PEP, comunicarlo y aportar DDC completa.

### 5.2 Tiempos
- DDC completa puede tomar 5-15 días.
- Operaciones complejas: planificar 30+ días.

## 6. Implicancias para el developer

### 6.1 Como vendedor
- Sus compradores serán sometidos a DDC.
- Anticipar la documentación para no demorar escrituras.
- En proyectos grandes, tener un protocolo de DDC pre-acordado con el escribano del proyecto.

### 6.2 Como comprador de tierra
- Recibirá la DDC del vendedor.
- Si el vendedor es sociedad, deberá identificar beneficiario final.
- Si hay aportes de socios extranjeros, prever DDC reforzada.

## 7. Sanciones al escribano

- UIF aplica sanciones administrativas.
- El Colegio de Escribanos sanciona disciplinariamente.
- En casos extremos, responsabilidad penal por encubrimiento.

## 8. Errores comunes

- Pretender escriturar sin documentación de origen.
- Querer "esquivar" la DDC con explicaciones genéricas.
- No declararse PEP cuando se es.
- Asumir que el escribano "se va a hacer el distraído" → no lo hará, son sujeto obligado con responsabilidad.

## 9. Reglas operativas para el chat

- **Estable:** marco, obligaciones del escribano, documentación típica.
- **🔴 Volátil:** umbrales monetarios específicos para distintos niveles de DDC, plazos puntuales → verificar UIF o consultar con el escribano.
- **CRÍTICO:** nunca sugerir formas de "evitar" la DDC. Si el cliente no puede documentar origen, debe asesorarse legalmente (puede haber blanqueos vigentes).

## Ver también
- `./marco-uif.md`
- `./sujeto-obligado-inmobiliarias.md`
- `./pep-personas-expuestas.md`
- `./kyc-y-origen-de-fondos.md`
- `./blanqueos.md`
- `../12-suelo-y-dominio/escritura-y-rpi.md`
