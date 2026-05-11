---
title: "Customer journey post-compra: booking a posventa"
topic: "comercial"
subtopic: "customer-journey"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CCyCN (arts. 1170, 1183, 1184, 1273, 2037 ss)"
  - "Ley 24.240 Defensa del Consumidor"
  - "Ley 25.345 (bancarización)"
  - "Práctica del sector"
keywords: [customer journey, booking, reserva, sena, boleto, escritura, posesion, posventa, onboarding cliente, ciclo cliente, ciclo comprador]
audience: ["developer", "comercial", "broker", "administrador", "chat"]
confidence: "alta"
---

# Customer journey post-compra

## TL;DR
- Cadena estándar: **lead → booking → reserva → seña → boleto → escritura → posesión → posventa**.
- Cada hito tiene: documento, dinero, plazo, responsable y riesgo.
- Errores típicos: confundir reserva con seña, no formalizar boleto, escriturar antes de cumplir UIF, no formalizar posesión, abandono en posventa.
- Bien gestionado: reduce devoluciones, refuerza branding, genera referidos.

## 1. Mapa del journey

```
LEAD
 ↓ (visita / call / chatbot)
INTERESADO QUALIFICADO
 ↓ (BANT — Budget, Authority, Need, Timing)
BOOKING (intención formal, sin dinero o señal mínima)
 ↓ (decisión + selección de UF)
RESERVA (con depósito) → no es seña aún
 ↓ (DD legal + financiero del comprador)
SEÑA (compromiso fuerte)
 ↓ (firma boleto)
BOLETO COMPRAVENTA (contrato preparatorio)
 ↓ (pago de cuotas / financiamiento)
PRE-ENTREGA (inspección, finales, ajustes)
 ↓
ESCRITURA (transferencia dominio)
 ↓
POSESIÓN (entrega de llaves)
 ↓
POSVENTA (12-24 meses garantía)
 ↓
CLIENTE LARGO PLAZO / REFERIDO / RE-COMPRA
```

## 2. Etapa 1 — Lead y calificación

### 2.1 Origen
- Portales (ZonaProp, Argenprop, ML).
- Meta Ads / Google Ads.
- Referidos.
- Walk-in showroom.
- Web propia.

### 2.2 Calificación
- BANT: presupuesto, decisor, necesidad, timing.
- Score automático en CRM.

### 2.3 Output esperado
- Lead asignado a vendedor.
- Primera respuesta < 5 min (WhatsApp / call).

### 2.4 Pitfalls
- Tiempo de respuesta lento → lead se pierde (50% en 1ª hora).
- Sin CRM → seguimiento manual ineficiente.

## 3. Etapa 2 — Booking / reserva de interés

### 3.1 Qué es
- Manifestación de interés con expresión de voluntad documentada.
- A veces incluye depósito simbólico (USD 500-2.000).
- Tipicamente no vinculante para ninguna parte aún.

### 3.2 Documentación
- Formulario de booking + datos personales + UF reservada.
- Plazo: 5-15 días hábiles.

### 3.3 Función
- Bloquea la UF mientras el comprador decide.
- Habilita due diligence inicial.

### 3.4 Pitfalls
- Aceptar múltiples bookings sobre la misma UF → conflicto.
- Booking sin documento → confusión con seña.

## 4. Etapa 3 — Reserva (con depósito)

### 4.1 Qué es
- Depósito de mayor entidad (típicamente 1-5% del precio) con compromiso de avanzar a boleto.
- En AR es práctica común; legalmente próximo a "seña confirmatoria" si se redacta así.

### 4.2 Documentación
- Recibo de reserva firmado por ambas partes.
- Detalle UF + precio + plazo para boleto + condiciones.
- Aclaración si es seña confirmatoria (CCyCN art. 1059) o reserva pura.

### 4.3 Plazo a boleto
- 15-60 días.

### 4.4 Devolución
- Si el comprador desiste sin causa: pierde la reserva.
- Si el developer desiste: devuelve doblado (si es seña confirmatoria) o lo pactado.
- Si hay condición suspensiva no cumplida: devuelve sin penalidad.

### 4.5 UIF
- Si supera umbral: iniciar DDC.

## 5. Etapa 4 — Seña confirmatoria

### 5.1 Qué es
- CCyCN art. 1059: la entrega de cosa o dinero como seña confirmatoria importa principio de ejecución.
- A diferencia de "arras" tradicionales, las señas en AR se presumen confirmatorias salvo pacto en contrario.

### 5.2 Monto típico
- 5-10% del precio.

### 5.3 Documentación
- Recibo + cláusulas de seña claras.

### 5.4 Función
- Compromete a ambas partes.
- Habilita avance a boleto en plazo corto.

## 6. Etapa 5 — Boleto de compraventa

### 6.1 Marco legal
- CCyCN arts. 1170-1171 (compraventa de inmuebles + boleto).
- Boleto = contrato preparatorio de la escritura.
- Oponibilidad si: hay buena fe + pago de al menos 25% + posesión.

### 6.2 Contenido típico
- Partes (vendedor + comprador).
- Identificación de la UF (plano + nomenclatura).
- Precio total + moneda + forma de pago + cronograma.
- Plazo de escrituración + condiciones.
- Penalidades por incumplimiento.
- Cláusula cesión (sí / no).
- Reglamento de copropiedad si aplica.
- Garantías ofrecidas (caución, hipoteca).
- Cláusula UIF + DDC.
- Cláusula moneda (Ley 25.345 si USD billete).
- Domicilios + jurisdicción.

### 6.3 Firma
- Por instrumento privado con firma certificada (escribano).
- O directamente ante escribano.

### 6.4 Sellos
- Tributo provincial.
- CABA: 1% (con reducciones para vivienda única).
- PBA: 3.6% típico.
- Verificar `04-impuestos/provincial/`.

### 6.5 Plazo de pago
- En pozo: 12-36 meses según producto.
- Usado: 30-60 días a escritura.

## 7. Etapa 6 — Pago de cuotas (si aplica)

### 7.1 Mecanismos
- Transferencia bancaria con CBU del proyecto / fideicomiso.
- USD billete bancarizado (Ley 25.345 si > umbral).
- Stablecoin con PSAV (ver `17-cnv-bcra/psav-cripto.md`).
- Cheques diferidos.

### 7.2 Ajuste
- CAC, ICC, UVA o USD según contrato.

### 7.3 Documentación
- Recibo numerado por cada pago.
- Estado de cuenta mensual disponible.
- Portal del cliente (recomendado).

### 7.4 Mora
- Cláusulas claras: intereses + plazo de regularización.

## 8. Etapa 7 — Pre-entrega

### 8.1 Inspección técnica
- Visita guiada con planos.
- Lista de observaciones (punch list).
- Plazo de corrección: 15-30 días.

### 8.2 Documentación a entregar
- Plano municipal de la UF.
- Certificados (instalaciones, ascensor, gas, electricidad).
- Reglamento de copropiedad.
- Manual del propietario.
- Llaves + tarjetas + accesos.

### 8.3 Saldo
- Pago del saldo previo a escritura.

## 9. Etapa 8 — Escritura

### 9.1 Marco legal
- CCyCN art. 1017 (forma escritura pública para inmuebles).
- Ley 17.801 (Registro de la Propiedad Inmueble).

### 9.2 Quién escritura
- Escribano público designado (por la parte que paga sellos / por acuerdo).

### 9.3 Documentos requeridos
- Boleto + recibos.
- Plano + reglamento.
- Certificado de dominio + gravámenes + inhibiciones.
- Libre deuda municipal + provincial.
- Certificado catastral.
- Constancia AFIP.
- Documentación UIF (KYC + origen fondos).

### 9.4 Plazo
- 30-90 días desde solicitud de escritura.

### 9.5 Inscripción RPI
- Escribano inscribe la escritura.
- Plazo legal: 45 días.

### 9.6 Costos
- Honorarios escribano: 1-2% del valor.
- Impuestos: sellos (ver provincia) + ITI (1.5%) o cedular (15%) del vendedor.
- Gastos registrales + certificados.

## 10. Etapa 9 — Posesión

### 10.1 Acta de entrega
- Documento firmado por ambas partes.
- Estado del inmueble + observaciones.
- Inicia plazos de garantía.

### 10.2 Servicios
- Activación de cuentas (luz, gas, agua, internet).
- Empresa instaladora si aplica.

### 10.3 Consorcio (si aplica)
- Alta en el consorcio.
- Reglamento + expensas iniciales.

## 11. Etapa 10 — Posventa

### 11.1 Período de garantía
- 12-24 meses para defectos no estructurales.
- 10 años para ruina total / parcial (CCyCN art. 1273).

### 11.2 Gestión
- Canal claro de reclamos (mail, WhatsApp, portal).
- SLA: respuesta < 48 hs, resolución < 30 días según gravedad.
- Categorización: urgente (filtración activa) / no urgente (ajustes).

### 11.3 Documentación
- Cada reclamo registrado con foto + fecha + responsable.
- Cierre con conformidad del cliente.

### 11.4 NPS
- Encuesta a los 30, 90 y 365 días post-posesión.
- Métrica clave para mejora continua.

### 11.5 Referidos
- Programa de referidos: bonificación monetaria o regalo.
- Posventa cuidada → 30-50% de leads orgánicos por referido.

## 12. Tabla maestra por etapa

| Etapa | Documento | Dinero | Plazo típico | Riesgo principal |
|---|---|---|---|---|
| Lead | (CRM) | — | — | Pérdida por respuesta lenta |
| Booking | Formulario | 0 - USD 2.000 | 5-15 d | Bloqueo de UF mal gestionado |
| Reserva | Recibo | 1-5% | 15-60 d | Conflicto si es / no es seña |
| Seña | Recibo + cláusula | 5-10% | 7-30 d a boleto | Devolución doblada |
| Boleto | Contrato firmado | hasta 25-30% | escritura en 24-36 m si pozo | Sellos + UIF |
| Cuotas | Recibos | balance | 12-36 m | Mora / cobranza |
| Pre-entrega | Punch list | — | 15-60 d | Observaciones sin resolver |
| Escritura | Escritura pública | saldo | 30-90 d | Documentación incompleta |
| Posesión | Acta entrega | — | 1 día | Estado del inmueble |
| Posventa | Reclamos | — | 12-24 m | Reputación + reincidencia |

## 13. CRM y automatizaciones

### 13.1 Estado por contacto
- Pipeline visible: lead → booking → reserva → seña → boleto → cuotas → entrega → posventa.
- Tokko / HubSpot / propio (ver `./crm-stack-tecnologico.md`).

### 13.2 Automatizaciones útiles
- Recordatorios de pago + email automático.
- Notificación de avance de obra (mensual con foto).
- Encuesta NPS automatizada.
- Alerta de mora a comercial + finanzas.

## 14. UIF a lo largo del journey

- **Booking / Reserva**: KYC inicial.
- **Seña / Boleto**: DDC + origen de fondos.
- **Escritura**: documentación final + escribano sujeto obligado.
- **Cripto / USD billete**: documentación reforzada.
- Ver `16-uif-blanqueo/kyc-y-origen-de-fondos.md`.

## 15. Errores comunes

- Confundir reserva con seña (consecuencias jurídicas distintas).
- No documentar formalmente cada paso.
- Acelerar a escritura sin completar UIF.
- Aceptar pagos en USD billete sin bancarizar (Ley 25.345).
- Boleto con cláusulas ambiguas (moneda, ajuste, plazo escritura).
- No formalizar la entrega con acta.
- Posventa reactiva sin canal claro → reclamos públicos.
- Cero seguimiento NPS → no aprende de errores.
- Pricing distinto al comprador A vs comprador B sin justificar → defensa del consumidor.

## 16. Reglas operativas para el chat

- **Estable:** cadena de hitos + documentos + responsables.
- **🔴 Volátil:** % típicos pueden variar — confirmar con asesor legal por operación específica.
- **Sensible:** redacción de boleto y reserva exige escribano / abogado. Chat orienta, no redacta contratos vinculantes.
- Si el usuario pregunta "¿la reserva se devuelve si me arrepiento?": depende de cómo se redactó (reserva pura vs seña confirmatoria — CCyCN art. 1059).
- Si pregunta "¿en qué momento entro al RPI?": al inscribir la escritura (no antes; el boleto da derechos pero no dominio).

## Ver también
- `./crm-stack-tecnologico.md`
- `./pricing.md`
- `./preventa.md`
- `./posventa.md`
- `../12-suelo-y-dominio/boleto-compraventa.md`
- `../12-suelo-y-dominio/escritura-y-rpi.md`
- `../16-uif-blanqueo/kyc-y-origen-de-fondos.md`
- `../19-casos-de-estudio/edificio-residencial-amba.md`
