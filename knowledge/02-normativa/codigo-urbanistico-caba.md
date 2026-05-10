---
title: "Código Urbanístico CABA — estructura general"
topic: "normativa"
subtopic: "codigo-urbanistico"
jurisdiction: "CABA"
last_verified: "2026-05-10"
sources:
  - "Ley 6099 CABA — Código Urbanístico (BO CABA 21-dic-2018, vigente desde 1-mar-2019)"
  - "Ley 6589 CABA y modificatorias posteriores — VERIFICAR última actualización vigente"
  - "GCBA — Portal del Código Urbanístico: buenosaires.gob.ar/codigourbanistico"
keywords: [codigo urbanistico, CUR, CABA, FOT, FOS, distritos, USAA, USAB, alturas, plano limite, indicadores]
audience: ["desarrollador", "arquitecto", "broker"]
confidence: "alta"
---

# Código Urbanístico CABA — estructura

> ⚠️ **Indicadores numéricos por parcela son volátiles y específicos.** Este archivo describe la **estructura del código**, no los valores puntuales.
> Para FOT/FOS/altura de una parcela específica, consultar el visor oficial del GCBA o Manzanas y Parcelas (mensura).

## TL;DR
- Vigente desde **1-mar-2019** (Ley 6099 CABA).
- Reemplazó al Código de Planeamiento Urbano (1977, con sucesivas reformas).
- Cambia el paradigma: de **distritos por uso** a **morfología por área de la ciudad**.
- Se complementa con el **Código de Edificación** (Ley 6100) — la edificabilidad se rige por el CUR; la construcción técnica, por el CE.

---

## 1. Estructura general del CUR

| Sección | Contenido |
|---|---|
| Sección 1 | Disposiciones generales |
| Sección 2 | Áreas de la ciudad y subdivisión del suelo |
| Sección 3 | **Tejido urbano** (FOT, FOS, alturas, retiros) |
| Sección 4 | Usos del suelo |
| Sección 5 | Áreas Especiales (APH, AOC, etc.) |
| Sección 6 | Régimen sancionatorio |
| Anexos | Atlas de áreas, listado de usos, premios, vías |

---

## 2. Subdivisión del suelo (Sección 2)

### 2.1 Áreas de la ciudad
- **U** — Áreas Urbanas.
- **AE** — Áreas Especiales (parques, costas, áreas portuarias, etc.).
- **APH** — Áreas de Protección Histórica (con régimen específico).

### 2.2 Áreas de los corredores
- Eje de transporte público.
- Permiten mayor edificabilidad.

### 2.3 Áreas de tejido
- **USAA** — Urbanización Semejante Alta y Alta.
- **USAB** — Urbanización Semejante Alta Baja.
- **USAM** — Urbanización Semejante Media.
- **USAA-1, USAA-2, USAB-1, USAB-2, USAM-1, USAM-2** — variantes según morfología.
- **U** — Urbanizaciones específicas (catálogos por barrio).

> Para saber el área de tu parcela: visor oficial GCBA → ingresar manzana y parcela.

---

## 3. Tejido urbano (Sección 3)

Fija para cada distrito:

### 3.1 Indicadores
- **FOT** — Factor de Ocupación Total = m² construibles / m² parcela.
- **FOS** — Factor de Ocupación del Suelo = m² ocupados en planta baja / m² parcela.
- **Altura máxima** del edificio.
- **Plano límite** — altura tope absoluta.
- **Retiros** — distancia a líneas oficiales (frente, fondo, laterales).
- **Línea de Frente Interno (LFI)** — define dónde se admite construir hacia el corazón de manzana.
- **Línea de Edificación (LE)** — sobre la calle.

### 3.2 Premios y compensaciones
El CUR introduce **premios por contraprestación**:
- Vivienda asequible.
- Espacio público.
- Conservación patrimonial.
- Eficiencia energética.

Cada premio otorga m² adicionales a cambio de la prestación específica.
Se regulan en anexos del código.

### 3.3 Capacidad constructiva (CC)
- Concepto unificador del FOT.
- Se calcula con la fórmula del CUR para cada parcela.
- Incluye los premios alcanzados.

---

## 4. Usos del suelo (Sección 4)

### 4.1 Categorías de uso
- **Vivienda** (V)
- **Comercio** (C)
- **Industria** (I)
- **Servicio** (S)
- **Equipamiento** (E)
- Otros (educación, salud, religioso, etc.)

### 4.2 Tablas de admisión por área
- Para cada área (USAA, USAM, etc.), un cuadro de usos:
  - Permitido.
  - Permitido condicionado.
  - No permitido.

### 4.3 Estacionamientos requeridos
- Variable por uso, escala y área.
- En general el CUR redujo la exigencia para fomentar construcción cerca de transporte.
- Para tipologías compactas, en muchos distritos no se exige.

---

## 5. Áreas especiales (Sección 5)

### 5.1 APH (Área de Protección Histórica)
- 50+ APH definidas en el código.
- En APH **no se aplica el régimen general**: hay reglas específicas de morfología, materiales, alturas.
- Pueden requerir aprobación del **Consejo Asesor de Asuntos Patrimoniales (CAAP)**.

### 5.2 AOC (Área de Oportunidad Concertada)
- Grandes parcelas con normativa concertada con el GCBA.
- Ejemplos históricos: Catalinas, Casa Amarilla, Núñez, Saldías.

### 5.3 Áreas de borde / costaneras / parques
- Restricciones de altura y uso para preservar valores paisajísticos.

---

## 6. Procedimiento de obra (cómo se aprueba)

1. **Pre-anteproyecto** — verificación de viabilidad normativa.
2. **Visado profesional** del Consejo (CPAU para arquitectura).
3. **Presentación al GCBA**: portal de Habilitaciones y Permisos / DGROC.
4. **Observaciones** del organismo técnico.
5. **Aprobación** del permiso de obra.
6. **Obra** con inspecciones periódicas.
7. **Final de Obra (FO)** otorgado por el GCBA.
8. Recién con FO se puede escriturar y habilitar comercialmente.

---

## 7. Premios — esquema general

| Premio | Contraprestación | Beneficio |
|---|---|---|
| Vivienda asequible | % UFs a precio social bajo regulación | m² adicionales |
| Espacio público | Cesión en planta baja | m² adicionales |
| Patrimonio | Conservación de fachada/edificio catalogado | m² adicionales |
| Sostenibilidad | Cumplimiento criterios ambientales | m² adicionales |

> Cifras y umbrales: ver anexos del CUR vigente. **VERIFICAR** porque hubo modificaciones.

---

## 8. Cómo verificar una parcela

1. **Visor oficial**: buenosaires.gob.ar → Mapa Interactivo → ingresar manzana y parcela.
2. Te devuelve:
   - Área del CUR (USAA, USAM, etc.).
   - FOT, FOS, alturas aplicables.
   - APH si corresponde.
   - Restricciones especiales.
   - Capacidad constructiva.
3. Cruzar con catastro provincial para mensura y dominio.

---

## 9. Códigos previos y transición

- **CPU 1977** y modificatorias (Códigos por distritos R, R1, R2, C, etc.) — **derogado** por CUR.
- Edificios construidos antes mantienen su situación; las modificaciones se rigen por CUR.
- Algunos distritos del CPU aún se mencionan en escrituras viejas — son referencias históricas.

---

## 10. Errores comunes

- Comprar una parcela basándose en el FOT del distrito vecino.
- No verificar APH (puede tirar abajo el proyecto entero).
- No considerar las restricciones aeronáuticas (Aeroparque).
- No considerar las restricciones por línea de subte / colectores.
- Asumir que el premio de vivienda asequible "se compensa" comercialmente sin hacer el modelo.

---

## 11. Reglas operativas para el chat

- **No dar FOT/FOS de un barrio o distrito de memoria.** Pedir manzana y parcela y derivar al visor oficial.
- **Sí explicar la mecánica de los indicadores y los premios** (estable).
- **Sí mencionar los distritos USAA / USAM / USAB y su lógica morfológica** (estable).
- **Sí guiar el proceso de aprobación** (estable).

---

**Fuentes:**
- Ley 6099 CABA + texto consolidado.
- Portal CUR GCBA: buenosaires.gob.ar/codigourbanistico
- CPAU — visados.

**Ver también:**
- `./codigo-edificacion-caba.md` (TBD)
- `./aph-patrimonio.md` (TBD)
- `../00-fundamentos/analisis-factibilidad.md`
