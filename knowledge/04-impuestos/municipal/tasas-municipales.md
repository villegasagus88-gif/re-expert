---
title: "Tasas municipales — habilitación, inspección, publicidad, ocupación"
topic: "impuestos"
subtopic: "tasas-municipales"
jurisdiction: "Municipal"
last_verified: "2026-05-11"
sources:
  - "Códigos Fiscales municipales"
  - "Ordenanzas tarifarias anuales"
keywords: [tasas municipales, habilitacion comercial, inspeccion, ocupacion via publica, publicidad, cartel obra, lavado de auto, registro comercial]
audience: ["desarrollador", "comercial", "chat"]
confidence: "alta"
---

# Tasas municipales operativas

## TL;DR
- Familia de tasas por servicios concretos del municipio. Se cobran al iniciar / mantener una actividad o uso.
- Principales para RE: **habilitación comercial**, **inspección de seguridad e higiene**, **derechos de publicidad**, **ocupación de vía pública**.
- Distintas del ABL/TSG (que es sobre el inmueble) y de los derechos de construcción (que son sobre la obra).
- 🔴 Importes cambian anualmente por ordenanza tarifaria.

## 1. Habilitación comercial

### 1.1 Qué es
- Trámite municipal para autorizar el uso comercial de un local.
- Verifica: aptitud edilicia, seguridad (electricidad, incendios), higiene, accesibilidad.

### 1.2 Cuándo se necesita
- Locales comerciales, oficinas, depósitos, industrias, gastronomía, salud.
- Cambio de rubro requiere nuevo trámite o ampliación.
- Renta temporaria (Airbnb) en CABA: registro propio (Ley 6.255, no es habilitación clásica pero opera similar).

### 1.3 Categorías por riesgo
- Bajo riesgo (oficinas, comercio minorista no perecederos) → trámite simplificado / declaración jurada.
- Mediano y alto riesgo (gastronomía, industria, depósito combustible) → inspección previa.

### 1.4 Documentación típica
- Plano de instalaciones (electrico, gas, sanitario, incendios).
- Certificado de aptitud técnica (CAT) profesional.
- Plan de evacuación.
- Habilitación de bomberos si corresponde.
- Habilitación SENASA / ANMAT si el rubro lo exige.
- Tasa de habilitación (única) + aporte profesional.

### 1.5 CABA — operativa
- Plataforma TAD CABA.
- Áreas: DGFyCO (Fiscalización), DGHP (Habilitaciones).
- Plazos: variables según rubro (15-90 días típico para bajo/mediano).

### 1.6 PBA — variaciones
- Cada municipio gestiona sus habilitaciones.
- Algunos municipios (Vicente López, San Isidro) tienen sistemas digitales avanzados.

## 2. Inspección de seguridad e higiene (anual o periódica)

- Tasa periódica que mantiene la habilitación vigente.
- Suele asociarse a inspecciones (de oficio o programadas).
- En CABA: gestión vía AGIP + DGFyCO.

## 3. Derechos de publicidad

### 3.1 Conceptos típicos
- Cartelería identificatoria del local (frente, marquesina).
- Cartelería en obra (panel desarrollador).
- Publicidad en medianeras.
- Pantallas LED.
- Banderolas, totems, banners.

### 3.2 Quien paga
- Anunciante o propietario del soporte (depende del régimen municipal).

### 3.3 CABA
- Régimen unificado en AGIP.
- Clasificación por dimensiones, tipo de soporte, ubicación, zona.

### 3.4 PBA y otros
- Tarifa por municipio, generalmente por m² de superficie de cartel.

## 4. Ocupación de vía pública

### 4.1 Conceptos
- Vallados, andamios, contenedores de obra.
- Mesas de bar / café.
- Bicicleteros, terrazas semi-permanentes.
- Casillas de obra.

### 4.2 Tarifa
- Por m² de calzada / vereda ocupada + tiempo.

### 4.3 Operativa CABA
- Permiso por TAD + pago AGIP.
- Requiere póliza de seguro de responsabilidad civil.

## 5. Otras tasas relevantes (variables por municipio)

| Tasa | Hecho |
|---|---|
| Servicios sanitarios (cuando no AySA/ABSA) | Provisión de agua y cloaca |
| Conservación de pavimentos | Mantenimiento vial |
| Derecho de aprovechamiento de espacio aéreo | Voladizos sobre vereda |
| Salud pública | En algunos rubros |
| Derecho de cementerio | No aplicable a RE pero existe |

## 6. Cómo computar en un proyecto

### 6.1 Durante la obra
- Vallado / ocupación vía pública (mensual durante toda la obra).
- Cartelería en obra (al inicio).
- Conexiones provisorias.

### 6.2 Al finalizar / poner en uso
- Habilitación de cada local comercial / oficina.
- Inspecciones periódicas.

### 6.3 Operación corriente
- Mantenimiento de habilitación (tasa periódica).
- Publicidad (si aplica).

## 7. Errores comunes

- No prever la tasa de habilitación al lanzar un mix comercial.
- Subestimar la duración de la ocupación de vía pública.
- Operar sin habilitación o con habilitación vencida → multas y clausura.
- No registrarse en el régimen de alquileres temporarios en CABA (Ley 6.255).

## 8. Reglas operativas para el chat

- **Estable:** qué tasas existen, cuándo se pagan, qué autoridad las controla, lógica del trámite.
- **🔴 Volátil:** importe en pesos, requisitos administrativos del año (cambian con frecuencia).
- Si el usuario pregunta "¿cuánto sale habilitar?", responder con metodología + pedir rubro + jurisdicción + derivar a TAD CABA / municipio.

## Ver también
- `./abl-tsg.md`
- `./derechos-construccion.md`
- `./contribuciones-y-plusvalia.md`
- `../../02-normativa/codigo-edificacion-caba.md`
