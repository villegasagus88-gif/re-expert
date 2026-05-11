---
title: "Usucapión / prescripción adquisitiva"
topic: "suelo-dominio"
subtopic: "usucapion"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CCyCN — arts. 1897-1905, 1909, 1910, 2565"
  - "Ley 14.159 — Juicio de información sumaria"
keywords: [usucapion, prescripcion adquisitiva, posesion 20 anos, posesion 10 anos, justo titulo, buena fe, mala fe, ccycn 1897, ccycn 1899, juicio usucapion]
audience: ["desarrollador", "abogado", "comprador", "chat"]
confidence: "alta"
---

# Usucapión (prescripción adquisitiva)

## TL;DR
- Modo de adquirir un derecho real por la **posesión continuada en el tiempo** (CCyCN 1897).
- Dos tipos:
  - **Breve (10 años)**: con justo título + buena fe (CCyCN 1898).
  - **Larga (20 años)**: sin necesidad de título ni buena fe (CCyCN 1899).
- Requiere acción judicial (Ley 14.159) — no opera automáticamente.
- Riesgo importante para developer: comprar terreno con ocupantes que ya cumplen plazos.

## 1. Marco legal — CCyCN

### 1.1 Concepto (art. 1897)
- "La prescripción para adquirir es el modo por el cual el poseedor de una cosa adquiere un derecho real sobre ella, mediante la posesión durante el tiempo fijado por la ley."

### 1.2 Posesión (art. 1909)
- Hay posesión cuando una persona tiene una cosa **bajo su poder con intención de someterla al ejercicio de un derecho real**.
- Posesión = corpus + animus.

### 1.3 Justo título y buena fe (art. 1902)
- **Justo título**: acto jurídico apto en sus condiciones de forma y fondo para transmitir el derecho real, otorgado por quien no es titular del derecho (ej: alguien me vendió como suyo lo que no era suyo, pero por escritura).
- **Buena fe**: convicción de que el transmitente era titular y que el acto era válido.

### 1.4 Prescripción breve — 10 años (art. 1898)
Requisitos:
- Justo título.
- Buena fe.
- Posesión continua durante **10 años**.
- Pública, pacífica e ininterrumpida.

### 1.5 Prescripción larga — 20 años (art. 1899)
Requisitos:
- Posesión durante **20 años**.
- Pública, pacífica, continua e ininterrumpida.
- NO requiere ni título ni buena fe.

## 2. Calidad de la posesión

### 2.1 Pública
- Ostensible, no clandestina.
- No interrumpida por actos de violencia.

### 2.2 Pacífica
- Sin violencia / clandestinidad / abuso de confianza.

### 2.3 Continua
- No interrumpida por:
  - **Causa natural** (cese material).
  - **Causa civil** (acción judicial del titular).

### 2.4 Ininterrumpida
- Sin actos de reconocimiento del derecho del titular.

## 3. Procedimiento — juicio de usucapión

### 3.1 Sustento legal
- Ley 14.159 (modificada por Ley 17.711).
- Códigos procesales provinciales.

### 3.2 Requisitos
- Acreditar posesión 20 años (o 10 con justo título y buena fe).
- Pruebas: testimonial, pericial, documental (boletas de servicios, impuesto, mejoras realizadas), informativa.
- Plano de mensura para usucapión (registrado).
- Citación al titular registral (publicación de edictos si está incierto).

### 3.3 Sentencia
- Declara la adquisición del dominio por usucapión.
- Se inscribe en RPI a favor del usucapiente.
- Cancela la inscripción del titular anterior.

## 4. Riesgos en compraventa de terreno

### 4.1 Ocupantes con tiempo cumplido
- Si al hacer DD se detectan ocupantes que llevan 18-20 años → riesgo inminente.
- Mitigación: desalojo + desocupación previa a la compra; o desistir.

### 4.2 Vecinos que ocupan parte del terreno
- Construcciones invadiendo la línea de muro vecino.
- Tomas o avances de cerco.

### 4.3 Aparceros / encargados con vivienda
- En zonas rurales / quintas, riesgo de transformar relación laboral en posesión.

## 5. Defensas del titular

### 5.1 Interrupción civil
- Demanda judicial (reivindicación, desalojo, posesoria) → corta la prescripción.

### 5.2 Reconocimiento del ocupante
- Si el ocupante reconoce al titular (firma contrato de comodato, locación) → no hay animus domini.

### 5.3 Pago de impuestos por el titular
- Argumento procesal frecuente, aunque no concluyente por sí solo.

## 6. Usucapión y boleto

- Un boleto + posesión + tiempo puede consolidar la situación del comprador frente al vendedor que no escritura.
- Pero esto no es usucapión clásica: es prescripción para conseguir la escritura (acción del 1170).

## 7. Usucapión administrativa (Ley 24.374 — "Ley Pierri")

- Régimen especial para vivienda única familiar de bajos recursos en CABA y otros.
- Acreditación administrativa + inscripción.
- Más simple que el juicio clásico.

## 8. Errores comunes

- Asumir que pagar impuestos sin posesión es usucapión — no lo es.
- Permitir un ocupante "temporal" que se prolonga 20 años.
- No iniciar acción civil cuando se detecta ocupación.
- Comprar sin verificar ocupantes en el terreno.
- Asumir que el cerco perimetral basta — la posesión es ejercicio efectivo.

## 9. Reglas operativas para el chat

- **Estable:** marco legal, plazos, calidad de la posesión, procedimiento.
- **Sensible — derivar a abogado:** evaluar si una situación concreta cumple los requisitos.
- Recordar: la usucapión **requiere sentencia judicial**. No es automática.

## Ver también
- `./due-diligence-dominial.md`
- `./escritura-y-rpi.md`
- `../02-normativa/ccyc-real-estate.md`
