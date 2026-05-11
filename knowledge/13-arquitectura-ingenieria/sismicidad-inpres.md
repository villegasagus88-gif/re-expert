---
title: "Sismicidad — INPRES-CIRSOC 103 y zonas sísmicas AR"
topic: "arquitectura-ingenieria"
subtopic: "sismicidad"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "INPRES — Instituto Nacional de Prevención Sísmica (San Juan)"
  - "INPRES-CIRSOC 103 — Reglamento Argentino para Construcciones Sismorresistentes"
  - "Códigos de edificación provinciales"
keywords: [sismicidad, inpres, cirsoc 103, zona sismica, zona 0, zona 1, zona 2, zona 3, zona 4, mendoza, san juan, salta, neuquen, sismo, antisismico, espectro respuesta]
audience: ["arquitecto", "ingeniero", "developer", "chat"]
confidence: "alta"
---

# Sismicidad e INPRES-CIRSOC 103

## TL;DR
- AR tiene riesgo sísmico significativo en la **zona andina** y norte (Mendoza, San Juan, La Rioja, Catamarca, Salta, Jujuy, Tucumán, Neuquén, Río Negro).
- **INPRES-CIRSOC 103** es el reglamento argentino de construcciones sismorresistentes.
- 5 zonas: **0** (muy baja), **1** (reducida), **2** (moderada), **3** (elevada), **4** (muy elevada).
- En zonas 3-4 el diseño antisísmico encarece la obra y exige diseño específico.
- BO/CABA están en zona 0 (muy baja), pero hay focos sísmicos en el AMBA.

## 1. Marco institucional

### 1.1 INPRES
- Instituto Nacional de Prevención Sísmica.
- Sede: San Juan (la provincia con mayor actividad histórica).
- Estudia, mide, regula la construcción sismorresistente.

### 1.2 INPRES-CIRSOC 103
- Reglamento argentino emitido en conjunto.
- Define zonas, coeficientes, métodos de cálculo.
- Versión actual: verificar con INPRES.

## 2. Zonas sísmicas de AR

### 2.1 Mapa simplificado (orden por riesgo)

| Zona | Riesgo | Provincias / Regiones representativas |
|---|---|---|
| **0** | Muy reducido | CABA, GBA, Buenos Aires central/este, Litoral norte (Entre Ríos, Corrientes, Misiones), Pampa Húmeda |
| **1** | Reducido | Buenos Aires oeste, sur de Santa Fe / Córdoba, Patagonia este |
| **2** | Moderado | Sur de Córdoba, La Pampa oeste, parte de Neuquén / Río Negro, Chaco oeste |
| **3** | Elevado | Mendoza, San Juan parcial, Salta, Jujuy, Tucumán, Catamarca, La Rioja, Neuquén Andina, San Luis oeste |
| **4** | Muy elevado | San Juan oeste y centro, parte de Mendoza, Salta oeste, Jujuy oeste |

> Mapa exacto y coeficientes por localidad: consultar INPRES.

### 2.2 Eventos históricos relevantes
- 1944 — San Juan (Mw ≈ 7.0) — devastó la ciudad.
- 1977 — Caucete (San Juan, Mw 7.4).
- 2010 — Maule, Chile (afectó zonas argentinas vecinas).
- Eventos periódicos en zona andina.

## 3. Diseño sismorresistente

### 3.1 Principios
- **Capacidad** > demanda sísmica esperada.
- Estructura debe **ser dúctil**: resistir y deformarse sin colapsar.
- Continuidad y regularidad: edificios simétricos, plantas regulares.
- Conexiones sólidas.

### 3.2 Métodos de cálculo
- **Análisis estático**: para edificios bajos/regulares.
- **Análisis modal espectral**: edificios medios.
- **Análisis dinámico no-lineal**: edificios complejos o críticos.

### 3.3 Coeficiente sísmico
- Función de la zona + categoría del edificio + tipo de suelo + período de la estructura.
- En zonas 3-4 puede multiplicar las cargas sobre la estructura.

### 3.4 Categoría del edificio
- A: edificios críticos (hospitales, bomberos, escuelas estratégicas) — mayor exigencia.
- B: residencial / comercial común.
- C: estructuras no críticas.

## 4. Impacto en el costo de obra

### 4.1 Zona 0
- Sobre-costo mínimo (mejor confort estructural, pero no antisísmico explícito).

### 4.2 Zona 2
- Sobre-costo 3-8% por mayor armado, conexiones, ductilidad.

### 4.3 Zonas 3-4
- Sobre-costo 10-25% por:
  - Mayor cuantía de hormigón y acero.
  - Diafragmas rígidos.
  - Núcleos rigidizadores.
  - Detalles especiales en uniones.
  - Posiblemente aisladores sísmicos en edificios estratégicos.

## 5. Suelos y sismicidad

### 5.1 Tipo de suelo amplifica el sismo
- Suelos blandos amplifican.
- Roca firme atenúa.
- Clasificación de suelos en INPRES-CIRSOC 103.

### 5.2 Mendoza y San Juan
- Estudio de suelos especialmente exigente.
- Fundaciones profundas, plateas reforzadas.

## 6. Profesionales y aprobaciones

### 6.1 Quién firma
- Ingeniero civil estructuralista con experiencia sismorresistente.

### 6.2 Aprobaciones
- Municipio aprueba conforme INPRES-CIRSOC 103.
- En provincias 3-4 hay revisión adicional.

## 7. Casos típicos

### 7.1 Edificio residencial AMBA (zona 0)
- Diseño estándar; sin sobre-costo significativo.

### 7.2 Edificio en Mendoza (zona 4)
- Diseño antisísmico explícito + revisión.
- Sobre-costo 15-25%.
- Plantas regulares preferidas.
- Núcleos centrales rigidizadores.

### 7.3 Hospital / escuela en zona sísmica
- Categoría A: diseño + sobreresistencia.
- Equipamiento sísmicamente sostenible.

### 7.4 Patrimonio histórico en zona sísmica
- Refuerzo sin alterar valor patrimonial.
- Técnicas especializadas.

## 8. BIM / análisis dinámico

- Modelado FEM (elementos finitos) para edificios complejos.
- BIM coordina estructura + arquitectura + instalaciones, asegurando continuidad sísmica.

## 9. Errores comunes

- Asumir que el AMBA está libre de riesgo sísmico (zona 0 pero hay focos).
- Subestimar el sobre-costo en zonas 3-4 al armar factibilidad.
- Adoptar plantas asimétricas en zonas sísmicas sin compensar.
- Olvidar tipo de suelo (suelo blando amplifica).
- Saltarse revisión externa en zonas críticas.

## 10. Reglas operativas para el chat

- **Estable:** zonificación, principios de diseño, impacto en costo, profesional firmante.
- **🔴 Volátil:** coeficientes exactos del INPRES-CIRSOC 103 vigente, valores de aceleración → INPRES.
- **Sensible:** todo cálculo sismorresistente lo firma ingeniero estructuralista. Chat NO calcula sismo.
- Si el usuario pregunta "¿mi terreno es sísmico?", responder: depende de localidad → consultar mapa INPRES + estudio de suelos.

## Ver también
- `./cirsoc.md`
- `./estudio-suelos.md`
- `../04-impuestos/provincial/mendoza.md`
- `../04-impuestos/provincial/san-juan.md`
- `../04-impuestos/provincial/salta.md`
