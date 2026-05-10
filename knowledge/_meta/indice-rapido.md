---
title: "Índice rápido por keyword"
topic: "meta"
subtopic: "indice"
jurisdiction: "N/A"
last_verified: "2026-05-10"
sources: []
keywords: [indice, mapa, navegacion]
audience: ["desarrollador", "estudiante"]
confidence: "alta"
---

# Índice rápido — Keyword → archivo

Mapa para que el chat resuelva en O(1) qué archivo abrir según el tema.
Mantener actualizado al sumar archivos.

## Por keyword

| Keyword | Archivo |
|---|---|
| desarrollador, rol developer, qué hace un desarrollador | `00-fundamentos/teoria-desarrollador.md` |
| ciclo de desarrollo, etapas de un proyecto, fases | `00-fundamentos/ciclo-desarrollo-inmobiliario.md` |
| factibilidad, viabilidad, due diligence | `00-fundamentos/analisis-factibilidad.md` |
| triple impacto, esg, b corp, sostenibilidad | `00-fundamentos/triple-impacto.md` y `09-triple-impacto/*` |
| PH, propiedad horizontal, reglamento copropiedad | `02-normativa/propiedad-horizontal.md` (TBD) + `normativa-basica.md` (legacy) |
| FOT, FOS, indicadores urbanísticos, código urbanístico | `02-normativa/codigo-urbanistico-caba.md` (TBD) |
| fideicomiso, ordinario, al costo, financiero | `04-impuestos/estructuras-fiscales/fideicomiso.md` (TBD) |
| SAS, sociedad anónima simplificada | `04-impuestos/estructuras-fiscales/sas.md` (TBD) |
| IVA, débito fiscal, crédito fiscal | `04-impuestos/nacional/iva.md` (TBD) |
| Ganancias, impuesto a las ganancias | `04-impuestos/nacional/ganancias.md` (TBD) |
| Bs Personales, bienes personales | `04-impuestos/nacional/bienes-personales.md` (TBD) |
| IIBB, ingresos brutos | `04-impuestos/provincial/iibb-{caba,pba}.md` (TBD) |
| sellos, impuesto de sellos | `04-impuestos/provincial/sellos.md` (TBD) |
| ABL, TSG, alumbrado barrido | `04-impuestos/municipal/abl.md` (TBD) |
| LCT, ley contrato de trabajo | `03-laboral/lct-marco-general.md` (TBD) |
| UOCRA, CCT 76/75, convenio construcción | `03-laboral/uocra-cct.md` (TBD) |
| ART, riesgos del trabajo, accidentes | `03-laboral/art-srt.md` (TBD) |
| rubros de obra | `rubros-obra.md` (legacy) → migrar a `05-construccion/rubros-obra.md` |
| rendimientos, productividad obra | `rendimientos.md` (legacy) |
| materiales, precios materiales | `materiales-precios.csv` |
| TIR, VAN, payback, flujo descontado | `06-financiero/indicadores-evaluacion.md` (TBD) |
| financiamiento, créditos, UVA, fideicomiso financiero | `06-financiero/fuentes-financiamiento.md` (TBD) |
| inflación, IPC, IPIM, ICC | `08-macro-argentina/inflacion-indices.md` (TBD) |
| dólar, FX, MEP, CCL, oficial | `08-macro-argentina/tipos-de-cambio.md` (TBD) |
| BCRA, tasa de política, REM | `08-macro-argentina/politica-monetaria.md` (TBD) |
| pricing, tasación, valor m2, precio | `07-comercial/pricing.md` (TBD) |
| pre-venta, pozo, fideicomiso al costo comercial | `07-comercial/preventa-pozo.md` (TBD) |
| LEED, certificación verde | `09-triple-impacto/leed-edge-iram.md` (TBD) |
| modelos de negocio, joint venture, permuta | `10-estrategia/modelos-de-negocio.md` (TBD) |

## Por jurisdicción

| Jurisdicción | Carpeta principal |
|---|---|
| Nacional | `02-normativa/` (CCyCN, leyes generales), `04-impuestos/nacional/`, `03-laboral/` |
| CABA | `02-normativa/codigo-urbanistico-caba.md`, `04-impuestos/provincial/iibb-caba.md`, `04-impuestos/municipal/abl.md` |
| PBA | `02-normativa/ley-8912-pba.md`, `04-impuestos/provincial/iibb-pba.md`, `04-impuestos/provincial/sellos-pba.md` |
| Otras (Cba/Mza/SF) | crear `04-impuestos/provincial/{provincia}/` cuando aplique |

## Estado de la base (Phase 1)

- ✅ Estructura de carpetas
- ✅ README maestro
- ✅ `_meta/fuentes-oficiales.md`
- ✅ `_meta/glosario.md`
- ✅ `_meta/indice-rapido.md` (este archivo)
- 🟡 `00-fundamentos/*` (en proceso)
- ⬜ Resto: ver roadmap en README.md
