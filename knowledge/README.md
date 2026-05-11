# Knowledge Base — Chat Experto Real Estate AR

Base de conocimiento curada que alimenta el system prompt del chat experto.
Toda la información acá es **profesional, validada y trazable a fuentes oficiales**.

---

## 🎯 Principios de diseño (optimizado para velocidad de respuesta)

1. **Un tema = un archivo.** Archivos chicos (≤ ~3k tokens) cargan más rápido y son más fáciles de citar.
2. **Frontmatter YAML obligatorio.** Permite filtrar por jurisdicción, tópico, fecha de verificación.
3. **Estructura predecible.** Todo doc empieza con TL;DR (≤ 5 bullets) → secciones → fuentes.
4. **Cero ruido.** No copiar y pegar de blogs random. Sólo BCRA, INDEC, AFIP, ARBA, BORA, IGJ, CNV, INAES, normativa publicada, papers académicos, organismos del rubro (CEDU, AEV, CAC, CACAC, COCAMBA, CPAU, SCA).
5. **Marcar verificación.** Si un dato necesita refresh: `[VERIFICAR YYYY-MM]`. Si no se pudo verificar la fuente: `[REVISAR FUENTE]`.
6. **Volátil ≠ estable.** Datos que cambian seguido (FX, jornales, precios materiales, alícuotas) **NO se guardan** con valor concreto: el chat los referencia a la fuente oficial. Lo estable (teoría, normativa estructural, fórmulas, glosario) sí está pre-cargado para que el chat responda al instante. Ver **`_meta/politica-datos.md`**.

---

## ⚖️ Lectura obligatoria del chat (autoridad central)

| Archivo | Para qué |
|---|---|
| **`_meta/politica-datos.md`** | Define qué es volátil / semivolátil / estable. Reglas duras de qué se guarda y qué no. |
| **`_meta/instrucciones-chat.md`** | Protocolo de respuesta: identidad, tono, templates, qué nunca hacer. |
| `_meta/fuentes-oficiales.md` | Catálogo de fuentes a las que el chat manda al usuario para datos volátiles. |
| `_meta/indice-rapido.md` | Mapa keyword → archivo del KB (búsqueda en O(1)). |
| `_meta/glosario.md` | Términos del rubro definidos. |

---

## 📁 Estructura

```
knowledge/
├─ _meta/                        # Índices y reglas internas — lectura obligatoria del chat
│  ├─ politica-datos.md          # ⚖️ Volátil vs estable — qué se guarda y qué no
│  ├─ instrucciones-chat.md      # ⚖️ Protocolo de respuesta del chat
│  ├─ fuentes-oficiales.md       # Catálogo de fuentes confiables AR
│  ├─ glosario.md                # Diccionario del rubro
│  └─ indice-rapido.md           # Mapa keyword → archivo
│
├─ 00-fundamentos/               # Teoría del desarrollador, ciclo, factibilidad
├─ 01-mercado-argentino/         # Estado de mercado, segmentos, zonas
├─ 02-normativa/                 # PH, urbanística, códigos de edificación
├─ 03-laboral/                   # LCT, UOCRA, ART, contrataciones
├─ 04-impuestos/                 # Tributos por nivel + estructuras fiscales
│  ├─ nacional/                  # IVA, Ganancias, Bs Personales, Sellos nacionales
│  ├─ provincial/                # IIBB, Sellos, Inmobiliario por provincia
│  ├─ municipal/                 # ABL/TSG, Derechos de construcción
│  └─ estructuras-fiscales/      # Fideicomisos, SAS, condominio, leasing
├─ 05-construccion/              # Rubros de obra, rendimientos, materiales
├─ 06-financiero/                # Análisis financiero, TIR/VAN, financiamiento
├─ 07-comercial/                 # Pricing, marketing, ventas, posventa
├─ 08-macro-argentina/           # Inflación, FX, tasas, contexto país
├─ 09-triple-impacto/            # ESG, B Corp, sostenibilidad, normas IRAM/LEED
├─ 10-estrategia/                # Frameworks de decisión, modelos de negocio
├─ 11-tasacion/                  # Métodos de valuación, residual, TTN, normas profesionales
├─ 12-suelo-y-dominio/           # DD dominial, boleto, escritura, prehorizontalidad, usucapión, expropiación
├─ 13-arquitectura-ingenieria/   # Programa, CIRSOC, suelos, sismicidad, instalaciones, BIM
├─ 14-costos-presupuesto/        # APU, estructura costos, curva S, índices, contingencias, control
└─ 16-uif-blanqueo/              # UIF, sujetos obligados, KYC, PEP, blanqueos
```

> Archivos en la raíz (`formulas.md`, `materiales-precios.csv`, `normativa-basica.md`, `rendimientos.md`, `rubros-obra.md`, `rules.md`) son legacy y se irán migrando a las carpetas temáticas.

---

## 📝 Frontmatter estándar

Todo archivo `.md` (excepto este README y los del `_meta/`) debe empezar con:

```yaml
---
title: "Título humano legible"
topic: "fundamentos|mercado|normativa|laboral|impuestos|construccion|financiero|comercial|macro|triple-impacto|estrategia"
subtopic: "ej: propiedad-horizontal"
jurisdiction: "Nacional|CABA|PBA|Cordoba|Mendoza|...|N/A"
last_verified: "YYYY-MM-DD"
sources:
  - "https://... (link oficial)"
  - "Ley XX.XXX, art. Y (BO YYYY-MM-DD)"
keywords: [palabra1, palabra2, ...]
audience: ["desarrollador", "inversor", "estudiante", "broker"]
confidence: "alta|media|baja"
---
```

`confidence`:
- **alta** → fuente oficial directa, verificada en último mes.
- **media** → fuente secundaria seria, o oficial pero >3 meses sin verificar.
- **baja** → conocimiento general del rubro, requiere doble check para decisiones legales/fiscales.

---

## 🤖 Cómo lo usa el chat

`backend/services/anthropic_service.py::load_knowledge_context()` lee el bucket
Supabase Storage `knowledge/`, filtra `.md`, los concatena en el system prompt
y los cachea (`@lru_cache`).

**Implicancia operativa:** todo lo que vive acá se inyecta en CADA request al
LLM. Por eso:

- Mantener archivos chicos.
- Evitar duplicación entre archivos (rompe el caché y dispara tokens).
- Si un tema crece > ~3k tokens, partirlo (ej: `iva-construccion.md` vs `iva-locacion.md`).
- Cuando el total supere ~50KB, migrar a **RAG con pgvector** (ver `_meta/roadmap.md`).

**Para que el chat encuentre rápido:** cada archivo lleva `keywords` ricos en el frontmatter.
El asistente usa esos para decidir qué información priorizar al armar la respuesta.

---

## ✍️ Cómo agregar contenido

1. Elegir carpeta correcta (si dudás, mirá `_meta/indice-rapido.md`).
2. Crear archivo con kebab-case: `propiedad-horizontal-caba.md`.
3. Pegar el frontmatter del template y completarlo (NO inventar fuentes).
4. Estructura sugerida:
   ```
   # Título
   ## TL;DR (≤5 bullets)
   ## Concepto
   ## Detalle / Articulado / Cálculos
   ## Casos prácticos
   ## Errores comunes
   ## Fuentes
   ```
5. Si referís a otro doc del KB, usá ruta relativa: `[ver](./04-impuestos/nacional/iva.md)`.
6. Antes de commitear: verificar que ninguna URL apunta a blog opinado o cuenta de Twitter.

---

## 🚫 Reglas anti-contaminación

- **NO** pegar opinión sin atribución.
- **NO** copiar bloques largos de fuentes con copyright (resumir + linkear).
- **NO** dejar precios o tasas sin `last_verified`.
- **NO** mezclar jurisdicciones en un mismo archivo (separar CABA / PBA / etc.).
- **NO** usar IA generativa para llenar contenido sin validación humana.

---

## 🗺️ Roadmap

- **Fase 1 (actual):** estructura + fundamentos + meta. ~10–15 archivos.
- **Fase 2:** normativa + impuestos nacionales + laboral. ~30 archivos.
- **Fase 3:** impuestos provinciales (CABA + PBA primero) + construcción detallada.
- **Fase 4:** financiero + macro + comercial + triple impacto.
- **Fase 5:** migración a RAG con pgvector (cuando KB > 50KB o > 100 archivos).

Detalle vivo: `_meta/roadmap.md`.

---

## 📋 Estado de la base

Última actualización: **2026-05-11**
Archivos productivos: ver `_meta/indice-rapido.md`.

### Bloques completados

| Bloque | Carpeta(s) | Contenido |
|---|---|---|
| 1 | `_meta/`, `00-fundamentos/` | Reglas, glosario, fundamentos del developer |
| 2A | `02-normativa/` | CCyCN, PH, CE/CU CABA, 8912 PBA, alquileres, defensa consumidor, ambiental |
| 2B | `04-impuestos/nacional/` + `estructuras-fiscales/` | IVA, Ganancias, Bs Personales, Cedular, Monotributo + Fideicomisos, SAS, Condominio |
| 2C | `04-impuestos/provincial/` | 24 jurisdicciones + overview |
| 2D | `03-laboral/` | LCT, UOCRA, IERIC, ART, modalidades, solidaridad |
| 2E | `05-construccion/` | Modalidades, certificación, HyS, garantías, documentación, Final de Obra |
| 3A | `06-financiero/` | TIR/VAN, cashflow, sensibilidad, financiamiento, apalancamiento, métricas |
| 3B | `07-comercial/` | Pricing, mix, preventa, embudo, posventa, segmentación |
| 3C | `10-estrategia/` | Modelos de negocio, JV, permuta, riesgos, decisiones |
| 4A | `08-macro-argentina/` | Inflación, FX, política monetaria/fiscal, ciclos, escenarios |
| 4B | `09-triple-impacto/` | Marco, certificaciones, huella carbono, eficiencia, accesibilidad, ESG |
| **Fase 1 (2026-05-11)** | `01-mercado-argentino/`, `04-impuestos/municipal/`, `11-tasacion/`, `12-suelo-y-dominio/`, `16-uif-blanqueo/` | Mercado AR + municipal + tasación + suelo/dominio + UIF/blanqueo |
| **Fase 2 (2026-05-11)** | `13-arquitectura-ingenieria/`, `14-costos-presupuesto/`, profundización `06-financiero/` + `07-comercial/` | Arquitectura/ingeniería (CIRSOC, suelos, sismo, BIM, instalaciones) + costos/presupuesto (APU, curva S, EVM, contingencias) + waterfall/capital stack/UVA/FCI + CRM stack + marketing digital |
| **Fase 3 (2026-05-11)** | `15-tecnologia-proptech/` | Panorama PropTech AR, IA en RE (AVM, lead scoring, chatbots, generativa), automatización (Zapier/Make/n8n), datos y fuentes (INDEC/BCRA/AFIP/BI), tokenización/blockchain, tendencias frontier (gemelo digital, IoT, VR/AR, drones) |
| **Fase 4 (2026-05-11)** | `17-cnv-bcra/` | Marco CNV (Ley 26.831, 27.440), vehículos CNV RE (FF, FCI cerrado, ON, CEDEAR), oferta pública, cepo cambiario, MEP/CCL/cripto, PSAV (Res 1010/2024 + Ley 27.739) |
| **Fase 5 (2026-05-11)** | `18-seguros/` | Marco SSN (Ley 20.091, 17.418, 22.400), TRC, RC obra/cruzada/profesional, ART + Decreto 911/96, caución y garantías, hogar + copropiedad |
| **Fase 6 (2026-05-11)** | `19-casos-de-estudio/` | Edificio residencial AMBA, oficinas Puerto Madero, BTR multifamily, logística zona este, hotel boutique Recoleta, barrio cerrado PBA |
| **Fase 7 (2026-05-11)** | `_meta/` extendido | FAQ base (Q&A), personas (10 perfiles de usuario), templates (15 plantillas de respuesta) |

