---
title: "Marco regulatorio: SSN — Superintendencia de Seguros de la Nación"
topic: "seguros"
subtopic: "marco"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Ley 20.091 — Entidades Aseguradoras"
  - "Ley 17.418 — Contrato de Seguro"
  - "Ley 22.400 — Productores de Seguros"
  - "Resoluciones SSN"
keywords: [ssn, superintendencia seguros, ley 20091, ley 17418, productor asesor, broker, asegurador, poliza, prima, prima pura, suma asegurada]
audience: ["developer", "constructor", "broker seguros", "abogado", "chat"]
confidence: "alta"
---

# Marco regulatorio de seguros

## TL;DR
- **SSN** = autoridad nacional que regula la actividad aseguradora en AR.
- Marco legal: **Ley 20.091** (entidades), **Ley 17.418** (contrato), **Ley 22.400** (productores).
- En RE: relevante para conocer obligaciones del developer/constructor y derechos del asegurado.

## 1. SSN — Superintendencia de Seguros de la Nación

### 1.1 Función
- Autoridad federal del mercado asegurador.
- Bajo Ministerio de Economía.

### 1.2 Atribuciones
- Autorizar aseguradoras.
- Aprobar productos / pólizas.
- Supervisar solvencia.
- Sancionar.
- Educar.

### 1.3 Registro de productores
- Productor Asesor (matrícula individual).
- Sociedad de productores.
- Asesor / Broker (figura más amplia).

## 2. Marco normativo

### 2.1 Ley 20.091 — Entidades aseguradoras
- Quiénes pueden operar.
- Capital mínimo.
- Reservas.
- Supervisión.

### 2.2 Ley 17.418 — Contrato de seguro
- Marco contractual.
- Obligaciones del asegurador y asegurado.
- Plazo de denuncia del siniestro.
- Caducidad.
- Prescripción (1 año desde el evento).

### 2.3 Ley 22.400 — Productores asesores
- Matrícula obligatoria.
- Régimen disciplinario.
- Responsabilidad solidaria con asegurado.

### 2.4 Resoluciones SSN
- Productos aprobados.
- Cláusulas técnicas.
- Solvencia.

## 3. Componentes del seguro

### 3.1 Asegurador
- Compañía autorizada SSN.

### 3.2 Asegurado / Tomador
- Quien firma la póliza y paga la prima.
- Puede tener beneficiarios distintos.

### 3.3 Productor asesor (broker)
- Intermediario matriculado.
- Asesora + coloca + asiste siniestros.

### 3.4 Póliza
- Contrato escrito.
- Condiciones generales + particulares.

### 3.5 Prima
- Precio del seguro.
- Componentes: prima pura + cargas + impuestos.

### 3.6 Suma asegurada
- Tope máximo de cobertura.

### 3.7 Franquicia / deducible
- Monto a cargo del asegurado.

### 3.8 Vigencia
- Período de cobertura.

## 4. Tipos de seguros relevantes en RE

### 4.1 Patrimoniales
- TRC (Todo Riesgo Construcción) — `./trc-construccion.md`.
- Responsabilidad Civil — `./responsabilidad-civil.md`.
- Caución — `./caucion-y-garantias.md`.
- Hogar / Copropiedad — `./hogar-copropiedad.md`.

### 4.2 Personales
- ART obra — `./art-decreto-911.md`.
- Vida (en hipoteca UVA, asociado).
- Salud (no aplica directo a RE).

### 4.3 Especiales
- Avales / fianzas.
- Errores y omisiones profesionales.
- Cyber risk (creciente).

## 5. Aseguradoras en AR (orientativo)

### 5.1 Generales / grupos grandes
- La Caja, Sancor, San Cristóbal, Federación Patronal, Provincia Seguros, Mercantil Andina, Berkley, Allianz, Zurich, Mapfre, La Segunda, Galicia Seguros, RUS, HDI, Chubb, ATM, Orígenes.

### 5.2 Especializadas en RE / construcción
- Reaseguradoras + compañías con departamentos técnicos.
- Brokers especializados: Marsh, Aon, WTW, Loma Negra Brokers, Solunion, otros.

## 6. Costo y prima

### 6.1 Componentes de la prima
- Prima pura (riesgo).
- Gastos administrativos.
- Comisión productor.
- Impuestos (IVA + IIBB).
- Tasa SSN.

### 6.2 Factores que afectan la prima
- Riesgo objetivo (tipo + ubicación + valor).
- Antecedentes del asegurado.
- Suma asegurada y franquicia.
- Mercado (capacidad reaseguradora).

### 6.3 Ajuste
- Pólizas anuales suelen renovar con ajuste.
- En AR contexto inflación: ajuste por índice o suma asegurada en USD.

## 7. Siniestro

### 7.1 Denuncia
- Plazo: típicamente 72 hs hábiles desde que se conoce.
- Documentación.

### 7.2 Liquidación
- Liquidador designado por aseguradora.
- Verifica cobertura + cuantifica daño.

### 7.3 Pago
- Indemnización dentro de plazo legal (30 días desde aceptación).
- Negativa fundada en plazo.

### 7.4 Reclamos
- Vía judicial.
- Defensa del consumidor (Ley 24.240).
- SSN (administrativo).

## 8. Subrogación

### 8.1 Concepto
- Aseguradora indemniza al asegurado y asume sus derechos contra el responsable del daño.

### 8.2 Aplicación
- Si un tercero causó el daño, la aseguradora luego le reclama.

## 9. Coaseguro y reaseguro

### 9.1 Coaseguro
- Varias aseguradoras comparten un riesgo grande.
- Cada una cubre un %.

### 9.2 Reaseguro
- Aseguradora transfiere parte del riesgo a reaseguradora.
- Para grandes obras es siempre con reaseguro internacional.

## 10. Errores comunes

- Tomar mínimo legal sin analizar exposición real.
- No leer las exclusiones (lo no cubierto).
- Sub-asegurar (suma asegurada menor a valor real → regla proporcional → cobro reducido).
- Olvidar actualizar suma asegurada en contexto inflación / FX.
- No tener broker matriculado (mala asesoría).
- Denunciar siniestro tarde → riesgo caducidad.

## 11. Reglas operativas para el chat

- **Estable:** marco regulatorio + actores + conceptos.
- **🔴 Volátil:** primas, productos vigentes, aseguradoras → broker / SSN al día.
- **Sensible:** elección de pólizas requiere broker matriculado SSN.
- Si el usuario pregunta "¿qué seguro necesito para mi obra?": mínimo TRC + RC + ART. Detalles: broker.

## Ver también
- `./trc-construccion.md`
- `./responsabilidad-civil.md`
- `./art-decreto-911.md`
- `./caucion-y-garantias.md`
- `./hogar-copropiedad.md`
- `../05-construccion/higiene-seguridad.md`
