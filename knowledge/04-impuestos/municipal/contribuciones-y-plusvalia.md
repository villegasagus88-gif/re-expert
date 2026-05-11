---
title: "Contribuciones por mejoras y captación de plusvalía urbanística"
topic: "impuestos"
subtopic: "contribuciones-plusvalia"
jurisdiction: "Municipal — CABA + PBA + otras"
last_verified: "2026-05-11"
sources:
  - "Ley 6099 — Código Urbanístico CABA (capítulo de plusvalía)"
  - "Ley 14.449 PBA — Hábitat (mecanismos de captación de plusvalía)"
  - "Códigos Fiscales municipales"
keywords: [contribucion por mejoras, plusvalia urbana, captura de plusvalia, codigo urbanistico caba, ley 14449 habitat, premios urbanisticos, suelo creado]
audience: ["desarrollador", "abogado", "chat"]
confidence: "alta"
---

# Contribuciones por mejoras y plusvalía urbanística

## TL;DR
- **Contribución por mejoras**: tributo que paga el propietario beneficiado por una obra pública que aumenta el valor de su inmueble (asfalto, cloaca, plaza nueva).
- **Plusvalía urbanística**: mecanismo de captación, por el Estado, de parte del aumento de valor del suelo cuando un cambio normativo (mayor FOT, cambio de zonificación) genera un upside privado.
- En CABA está dentro del **Código Urbanístico (Ley 6099)**.
- En PBA opera vía **Ley 14.449 (Hábitat)** y normativas municipales.
- Su impacto en factibilidad puede ser alto si se usa en el proyecto un **premio urbanístico**.

## 1. Contribución por mejoras (clásica)

### 1.1 Concepto
- Tributo singular vinculado a una obra pública concreta.
- Hecho imponible: la obra pública que aumenta el valor del inmueble.
- Sujeto: propietario del inmueble beneficiado.
- Base: aumento de valor del inmueble (o prorrateo del costo de la obra).

### 1.2 Ejemplos típicos
- Asfaltado de una calle de tierra.
- Construcción de cloaca cuando no había.
- Veredas nuevas.
- Iluminación.

### 1.3 Forma de pago
- Generalmente en cuotas, atadas a la obra pública.
- Inscripción en el inmueble; afecta libre deuda.

### 1.4 Sustento normativo
- Constitución Nacional art. 75 (potestad tributaria).
- Códigos fiscales municipales / provinciales (cada uno regula).

## 2. Plusvalía urbanística

### 2.1 Concepto
- Captación, por el Estado, de parte del aumento de valor del suelo cuando una decisión pública (planificación, reordenamiento) genera mayor edificabilidad o cambio de uso.
- Lógica: la plusvalía es generada por la sociedad (por el planeamiento) → parte vuelve a la sociedad.

### 2.2 Hechos generadores típicos
- Cambio de zonificación que aumenta FOT.
- Cambio de uso del suelo (industrial → residencial).
- Incorporación al área urbanizable.
- Cesión de premios urbanísticos a un proyecto.

### 2.3 Mecanismos de captación
- **Pago dinerario** al fisco proporcional a la valorización.
- **Cesión de m² construidos** al Estado.
- **Cesión de tierra** o aporte a fondos urbanos.
- **Obras complementarias** (vialidad, equipamiento) ejecutadas por el privado.

## 3. CABA — Código Urbanístico (Ley 6099)

### 3.1 Premios y mayor edificabilidad
- El CUR permite aprovechar **capacidad constructiva extra** (mayor FOT) bajo ciertas condiciones:
  - Sostenibilidad (certificaciones ambientales).
  - Vivienda asequible (incorporación de UFs accesibles).
  - Conservación patrimonial.
  - Espacios públicos / verdes en el proyecto.
- A cambio, el desarrollador paga **contribución compensatoria** o cede algo de valor.

### 3.2 Distritos especiales
- Distrito Audiovisual, Tecnológico, Diseño, Arte: incentivos fiscales + criterios urbanísticos diferenciados.
- Beneficios condicionados a uso y permanencia.

### 3.3 Operativa
- El cálculo de la contribución compensatoria depende de la capacidad extra que se utilice y de la valuación.
- Resolución técnica del DGROC + intervención del Consejo del Plan Urbano Ambiental (CoPUA).

## 4. PBA — Ley 14.449 (Acceso Justo al Hábitat)

### 4.1 Mecanismos previstos
- **Participación del municipio en la valorización inmobiliaria** generada por procesos de:
  - Incorporación al área urbana.
  - Cambio de zonificación.
  - Cambio de indicadores urbanísticos (FOT, FOS).
  - Autorización de mayor altura.
- Implementación: cada municipio debe regular vía ordenanza local.

### 4.2 Destino de los recursos
- Fondo Fiduciario Público de Hábitat — financia vivienda social, regularización dominial, infraestructura.

### 4.3 Casos típicos
- Pilar, Tigre, La Plata, Vicente López tienen ordenanzas que aplican.

## 5. Otras jurisdicciones

- Rosario, Córdoba Capital, Mendoza y otras ciudades grandes tienen mecanismos similares en sus códigos urbanísticos / planes directores.
- Ver detalles en `../provincial/{provincia}.md`.

## 6. Impacto en factibilidad de un proyecto

### 6.1 Cuando NO uso premio urbanístico
- Solo pago derechos de construcción estándar.
- No hay plusvalía a captar (FOT base).

### 6.2 Cuando uso premio urbanístico o aprovecho cambio de zonificación
- Costo extra a sumar al estudio de factibilidad:
  - Contribución compensatoria CABA.
  - Plusvalía PBA (donde aplique).
  - Cesiones físicas o dinerarias.
- Este costo puede ser **significativo** (varios % del valor del proyecto) y se equilibra con el upside del m² extra.

### 6.3 Cómo modelar
- Comparar:
  - Proyecto con FOT base, sin premio, sin plusvalía a pagar.
  - Proyecto con premio, con plusvalía, con m² extra a vender.
- El delta de utilidad indica si vale la pena.

## 7. Errores comunes

- Asumir que el premio urbanístico es "gratis" — siempre tiene contrapartida.
- No descontar la plusvalía del análisis cuando el proyecto se "estira" para usar premio.
- Omitir las cesiones físicas obligatorias en proyectos grandes.
- No verificar si la ordenanza municipal de plusvalía ya fue dictada (en PBA muchos municipios no la reglamentaron).

## 8. Reglas operativas para el chat

- **Estable:** qué es contribución por mejoras vs plusvalía urbanística, lógica, mecanismos, dónde regula.
- **🔴 Volátil — derivar:**
  - Alícuotas y montos vigentes → CUR CABA + DGROC; ordenanza municipal PBA.
  - Beneficios de cada distrito especial CABA.
- Si el usuario pregunta "¿cuánto plusvalía pago?", responder con metodología + pedir ubicación, FOT base, FOT objetivo + derivar a estudio profesional.

## Ver también
- `./abl-tsg.md`
- `./derechos-construccion.md`
- `../../02-normativa/codigo-urbanistico-caba.md`
- `../../02-normativa/ley-8912-pba.md`
