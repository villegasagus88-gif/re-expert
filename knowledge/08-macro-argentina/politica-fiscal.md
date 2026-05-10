---
title: "Política fiscal argentina y su impacto en real estate"
topic: "macro"
subtopic: "politica-fiscal"
jurisdiction: "Argentina"
last_verified: "2026-05-10"
sources:
  - "Ministerio de Economía — informes fiscales"
  - "AFIP / ARCA — recaudación"
  - "INDEC — cuentas nacionales"
keywords: [politica fiscal, deficit, primario, financiero, gasto publico, recaudacion, presion fiscal, deuda, tax]
audience: ["financiero", "developer", "analista"]
confidence: "alta"
---

# Política fiscal argentina

## TL;DR
- La política fiscal define cómo el Estado **recauda** (impuestos) y **gasta**.
- Argentina suele tener déficit fiscal estructural → presión inflacionaria por monetización.
- Real estate AR está expuesto a:
  - Cambios en impuestos nacionales (IVA, Ganancias, Bienes Personales, Cedular, ITI).
  - Cambios en provinciales (IIBB, Sellos).
  - Cambios en municipales (ABL, derechos de construcción).
- Presión fiscal global elevada vs PIB.

---

## 1. Conceptos básicos

### 1.1 Resultado primario
- Ingresos - Gastos (sin contar intereses de la deuda).
- Si > 0: superávit primario.
- Si < 0: déficit primario.

### 1.2 Resultado financiero
- Resultado primario - Intereses de la deuda.

### 1.3 Brechas
- Argentina suele tener déficit primario y financiero.
- Excepciones: 2003-2007 (boom), 2024 (ajuste reciente, 🔴 volátil).

### 1.4 Cobertura del déficit
- Emisión monetaria (BCRA financia al Tesoro).
- Endeudamiento doméstico (LELIQ, pases, bonos en pesos).
- Endeudamiento externo (FMI, mercado internacional).

---

## 2. Estructura del gasto público

### 2.1 Componentes
- Gasto previsional (jubilaciones, pensiones).
- Salarios públicos.
- Subsidios (energía, transporte).
- Transferencias (provincias, asignaciones).
- Inversión pública (infraestructura).
- Servicio de deuda.

### 2.2 Distribución
- 🔴 Volátil — verificar Ministerio de Economía.
- Históricamente: gasto previsional + salarios concentran la mayor parte.

### 2.3 Rigideces
- Salarios y jubilaciones tienen ajustes automáticos por ley.
- Subsidios: reducirlos genera tensiones políticas.

---

## 3. Recaudación

### 3.1 Composición típica
- IVA (mayor recaudador, ~30% del total).
- Ganancias.
- Cargas sociales.
- Derechos de exportación (retenciones).
- Combustibles e impuestos internos.
- Bienes Personales.
- Otros.

### 3.2 Coparticipación federal
- Ley 23.548: distribución entre Nación y provincias.
- Asuntos contenciosos: Convenio Multilateral, leyes especiales.

### 3.3 Presión fiscal
- Total impuestos / PIB.
- AR: 🔴 volátil, históricamente alta entre 30-35% del PIB.

---

## 4. Impuestos relevantes para RE

### 4.1 Nacionales
- IVA en obra sobre inmueble propio (developer constructor).
- Ganancias 3ª categoría / Cedular para personas físicas.
- Bienes Personales.
- ITI (operaciones pre-2018 + algunos casos).
- Monotributo (locación 3 unidades).

> Ver `../04-impuestos/nacional/`.

### 4.2 Provinciales
- IIBB sobre desarrollo y comercialización.
- Sellos sobre boletos / escrituras.
- Inmobiliario provincial.

> Ver `../04-impuestos/provincial/`.

### 4.3 Municipales
- ABL.
- Derechos de construcción.
- Tasas varias.

---

## 5. Cambios fiscales y real estate

### 5.1 Sensibilidad
- RE es muy sensible a cambios en alícuotas y bases imponibles.
- Modificaciones en Bienes Personales (alícuotas, mínimo no imponible) → impacto patrimonial.
- Cambios en IVA → cashflow.
- Modificaciones en Cedular / Ganancias → ROI del comprador.

### 5.2 Reformas frecuentes
- Reforma tributaria 2017 (Ley 27.430): introdujo Cedular sobre inmuebles.
- Ley 27.541 (Solidaridad y Reactivación 2019): cambios en BP, Ganancias.
- DNU 70/2023 + Ley Bases (2024): desregulación en alquileres y otros.
- 🔴 Continuamente cambia. Verificar normativa vigente.

### 5.3 Beneficios y exenciones
- A veces se crean regímenes promocionales (Tierra del Fuego Ley 19.640, RIGI Ley 27.742).
- Beneficios para vivienda social.
- Reembolso de IVA en algunos casos.

---

## 6. Deuda pública

### 6.1 Composición
- Por moneda: pesos vs USD.
- Por acreedor: organismos internacionales, mercado, intra-sector público.

### 6.2 Riesgos
- Renegociaciones / defaults.
- Costos crecientes del servicio.
- Impacto en tasa de interés y tipo de cambio.

### 6.3 Riesgo país (EMBI+)
- Spread sobre activos del Tesoro USA.
- Refleja percepción de los inversores.

---

## 7. Política fiscal y ciclo económico

### 7.1 Pro-cíclica vs contra-cíclica
- Pro-cíclica: gasto cuando crece, recorte cuando cae → amplifica el ciclo.
- Contra-cíclica: ahorra en bonanza, gasta en crisis → suaviza.
- AR suele ser pro-cíclica históricamente.

### 7.2 Implicancia
- En recesiones, recortes fiscales pueden agravar la caída de la actividad → impacto en demanda RE.
- En auge, ajustes pueden ser improbables → más inflación.

---

## 8. Presupuesto

### 8.1 Ciclo
- Elaboración por el Ejecutivo.
- Tratamiento legislativo.
- Aprobación o "presupuesto prorrogado".

### 8.2 Monitoreo
- Ejecución mensual.
- Ajustes por ampliaciones.

### 8.3 Implicancias
- Cuando hay presupuesto prorrogado: incertidumbre sobre obras públicas y políticas activas.

---

## 9. Indicadores fiscales a seguir

- Resultado primario y financiero (% del PIB).
- Recaudación total y por impuesto (variación interanual real).
- Coparticipación a provincias.
- Stock de deuda y servicio.
- Riesgo país.

---

## 10. Implicancias para developers

### 10.1 Costo total del proyecto
- Sumar todos los impuestos.
- Sensibilizar a cambios de alícuotas.

### 10.2 Decisiones de timing
- Vender antes vs después de un cambio fiscal anunciado.
- Reorganizar estructuras (de SAS a fideicomiso, etc.) según conveniencia.

### 10.3 Lobby sectorial
- Cámaras (CADRE, CIA, CAC) intervienen en proyectos de ley.
- Developers grandes participan.

---

## 11. Errores comunes

- Modelar sin considerar todos los impuestos.
- Asumir alícuotas estables a 5 años.
- No tener escenarios de cambio fiscal.
- Confundir tasas marginales con efectivas.
- Ignorar el peso del impuesto al cheque (Ley 25.413).

---

## 12. Reglas operativas para el chat

- **Estable y respondible:** marco fiscal, conceptos, taxonomía de impuestos, ciclo presupuestario.
- **🔴 Volátil:** alícuotas, mínimos, anuncios recientes → consultar AFIP / Ministerio de Economía.
- **🔴 Caso particular:** estructuración de un proyecto con criterio fiscal → contador + abogado.

---

**Ver también:**
- `./inflacion.md`
- `./fx-cambiario.md`
- `./politica-monetaria.md`
- `./ciclos-mercado.md`
- `../04-impuestos/`
