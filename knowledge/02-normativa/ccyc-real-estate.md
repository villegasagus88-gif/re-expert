---
title: "Código Civil y Comercial — artículos relevantes para Real Estate"
topic: "normativa"
subtopic: "ccyc"
jurisdiction: "Nacional"
last_verified: "2026-05-10"
sources:
  - "Código Civil y Comercial de la Nación — Ley 26.994 (BO 08-oct-2014, vigente desde 1-ago-2015)"
  - "InfoLEG — texto consolidado: servicios.infoleg.gob.ar"
keywords: [ccyc, codigo civil, ley 26994, real estate, contratos, derechos reales, dominio, condominio, hipoteca, locacion, fideicomiso, propiedad horizontal, boleto]
audience: ["desarrollador", "estudiante", "abogado"]
confidence: "alta"
---

# CCyCN — mapa de artículos clave para desarrollo inmobiliario

> Marco general. Para una decisión concreta consultá un abogado o escribano matriculado.

## TL;DR
- Ley 26.994 (vigente desde 1-ago-2015) unifica derecho civil y comercial.
- Para RE importan: **derechos reales** (Libro IV), **contratos** (Libro III) y partes de **familia/sucesiones** (cuando hay sucesiones en juego).
- Los regímenes que **derogó** y reemplazó: Ley 13.512 (PH), Ley 24.441 (fideicomiso), Ley 14.005 (boleto loteos), entre otras.

---

## 1. Estructura del Código

| Libro | Contenido |
|---|---|
| Libro I | Parte General |
| Libro II | Relaciones de familia |
| Libro III | Derechos personales (contratos) |
| **Libro IV** | **Derechos reales** ← núcleo de RE |
| Libro V | Sucesiones |
| Libro VI | Disposiciones comunes |

---

## 2. Derechos reales — Libro IV (arts. 1882–2276)

### 2.1 Disposiciones generales (arts. 1882–1907)
- **Art. 1882** — Concepto: poder jurídico sobre cosa que confiere atributos.
- **Art. 1883** — Objeto: cosas; partes materiales o inmateriales.
- **Art. 1887** — Enumeración cerrada (numerus clausus). Los DR están taxativamente enumerados:
  - Dominio
  - Condominio
  - Propiedad horizontal
  - Conjuntos inmobiliarios
  - Tiempo compartido
  - Cementerios privados
  - Superficie
  - Usufructo
  - Uso
  - Habitación
  - Servidumbre
  - Hipoteca
  - Anticresis
  - Prenda

### 2.2 Dominio (arts. 1941–1986)
- Es el DR de mayor amplitud: usar, gozar y disponer.
- **Modos de adquisición**: contrato + tradición + inscripción en RPI.
- **Tradición** (art. 1924): entrega material o ficta; sin tradición no hay dominio aunque haya escritura.

### 2.3 Condominio (arts. 1983–2036)
- Pluralidad de titulares sobre la misma cosa.
- Cada uno tiene una **alícuota ideal**.
- División: cualquier condómino puede pedirla, salvo pacto de indivisión (máx. 10 años renovables).
- Aplicación en RE: socios sobre tierra; condominio sobre cocheras o sum.

### 2.4 Propiedad Horizontal (arts. 2037–2072)
- Régimen autónomo (reemplaza a Ley 13.512).
- Ver archivo dedicado: `./propiedad-horizontal.md`.

### 2.5 Conjuntos inmobiliarios (arts. 2073–2086)
- Barrios cerrados, clubes de campo, parques industriales.
- Marco unificado.
- Reglamento + reservas obligatorias.

### 2.6 Superficie (arts. 2114–2128)
- DR temporario que separa la propiedad del suelo de la propiedad de lo construido o plantado.
- **Plazo máx. 70 años** (construcción) o **50 años** (plantaciones).
- Útil en RE para concesiones, leasing inmobiliario complejo, partnerships entre dueño de tierra y desarrollador.

### 2.7 Hipoteca (arts. 2205–2211)
- DR de garantía sobre inmueble; el deudor mantiene posesión.
- Plazo máximo: **20 años** (renovable por nuevo acto registral antes del vencimiento).
- Se inscribe en el Registro de Propiedad Inmueble.

### 2.8 Servidumbres (arts. 2162–2183)
- Carga sobre un inmueble en beneficio de otro.
- Tipos: paso, acueducto, vista, etc.

---

## 3. Contratos — Libro III (arts. 957–1707)

### 3.1 Compraventa (arts. 1123–1186)
- **Art. 1170** — Boleto de compraventa. Reconoce efectos jurídicos al boleto firmado antes de la escritura.
- **Art. 1171** — Si está pagado el 25% o más del precio, el boleto tiene **oponibilidad concursal frente al vendedor** (priori­dad sobre acreedores).
- Buena fe (art. 1198) — doctrina mantenida.

### 3.2 Locación (arts. 1187–1226)
- Marco general — los pisos vienen de leyes especiales (Ley 27.551 modificada, DNU 70/2023, ver `./regimen-alquileres.md` TBD).
- Plazo mínimo locación habitacional: el régimen actual (post DNU 70/2023) es de **libertad contractual** [VERIFICAR vigencia y eventuales fallos contradictorios].
- Locación comercial: plazo y moneda libres.

### 3.3 Leasing (arts. 1227–1250)
- Modalidades: financiero, operativo. Aplicación inmobiliaria: leasing inmobiliario.
- Ley 25.248 complementaria (en lo que no se opone).
- Útil para inversor que quiere entrar a un inmueble grande con opción de compra.

### 3.4 Locación de obra y servicios (arts. 1251–1279)
- **Art. 1251** — Locación de obra: contratista compromete resultado. **Locación de servicios**: compromete actividad.
- Régimen aplicable a contratistas, gerenciadores, profesionales.
- **Art. 1273** — Vicios y daños: responsabilidad del constructor por **ruina total o parcial** durante **10 años** desde la recepción de la obra.
- **Art. 1271** — Vicios aparentes: denunciables hasta la recepción.
- **Art. 1272** — Vicios ocultos: prescripción de **3 años** desde la manifestación.

### 3.5 Mandato y representación (arts. 1319–1334)
- Útil para apoderar al desarrollador en gestiones de los inversores.

### 3.6 Mutuo (arts. 1525–1532)
- Préstamo de cosas consumibles (típicamente dinero).
- Base de los contratos de financiación entre socios o de inversores al fideicomiso.

### 3.7 Fideicomiso (arts. 1666–1707)
- Régimen unificado. Reemplaza partes de Ley 24.441.
- Contrato por el cual el **fiduciante** transmite la propiedad **fiduciaria** al **fiduciario** quien la administra en beneficio del **beneficiario** y entrega al **fideicomisario** al cierre.
- **Art. 1670** — Patrimonio separado: los bienes del fideicomiso no responden por deudas del fiduciario, fiduciante ni beneficiario.
- **Plazo máx. 30 años** salvo beneficiario incapaz (hasta su muerte o cese).
- Tipos: ordinario, financiero (oferta pública, regulado por CNV), de garantía, testamentario.
- Ver archivo dedicado: `../04-impuestos/estructuras-fiscales/fideicomiso-ordinario.md` (TBD).

### 3.8 Otras figuras útiles
- **Permuta** (arts. 1172–1175 + 1126): cambio de cosa por cosa. Núcleo de la **permuta tierra por UFs**.
- **Donación** (arts. 1542–1573).
- **Cesión de derechos** (arts. 1614–1640): aplicable a posición contractual en boletos.

---

## 4. Sucesiones (Libro V) — alcance en RE

- Heredero adquiere a la muerte del causante (no en la declaratoria); pero para vender necesita declaratoria firme + inscripción.
- Particiones: judicial / extrajudicial.
- Implicancia para developer: **antes de comprar un inmueble heredado**, exigir declaratoria firme + inscripción a nombre del vendedor.

---

## 5. Cláusulas frecuentes en contratos de desarrollo

| Tema | Artículo CCyCN |
|---|---|
| Buena fe contractual | 9, 729, 961 |
| Imprevisión / teoría de la imprevisión | 1091 |
| Rescisión por culpa | 1083–1090 |
| Cláusulas abusivas | 988 |
| Mora automática | 886 |
| Intereses moratorios | 768 |
| Cláusula penal | 790–804 |
| Saneamiento por evicción y vicios | 1033–1058 |
| Garantía de buen funcionamiento | 1051 |

---

## 6. Cómo se cita en el KB

Convención: `CCyCN art. XXXX` (sin punto entre número y letras).
Ejemplo: `CCyCN art. 1170` (boleto de compraventa).

---

**Ver también:**
- `./propiedad-horizontal.md`
- `./defensa-consumidor.md` (TBD)
- `../04-impuestos/estructuras-fiscales/fideicomiso-ordinario.md` (TBD)
