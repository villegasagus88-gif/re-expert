---
title: "Arquitectura e ingeniería — overview"
topic: "arquitectura-ingenieria"
subtopic: "overview"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CIRSOC — Centro de Investigación de los Reglamentos Nacionales de Seguridad para las Obras Civiles"
  - "INPRES — Instituto Nacional de Prevención Sísmica"
  - "Ley 22.250 — Estatuto del trabajador de la construcción"
  - "Códigos de Edificación CABA y provinciales"
keywords: [arquitectura, ingenieria, programa, anteproyecto, proyecto, direccion obra, cirsoc, inpres, instalaciones, suelos, bim]
audience: ["developer", "arquitecto", "ingeniero", "chat"]
confidence: "alta"
---

# 13 — Arquitectura e ingeniería

## TL;DR
- Disciplina técnica que convierte el programa del developer en proyecto construible y eficiente.
- Bloques: **programa arquitectónico**, **eficiencia de planta**, **normas estructurales (CIRSOC)**, **instalaciones**, **sismicidad (INPRES)**, **estudio de suelos**, **BIM/tecnología**.
- Errores en estas etapas son los más caros del proyecto: arquitectura mala = 5-15% menos rentabilidad estructural.
- Profesional firmante: arquitecto matriculado (proyecto + dirección) + ingenieros especialistas (estructura, electromecánica, sanitaria, gas).

## Archivos del módulo

| Archivo | Contenido |
|---|---|
| `programa-arquitectonico.md` | Programa, anteproyecto, proyecto, dirección, etapas |
| `eficiencia-planta.md` | m² vendible/construido, factor K, layout, planta |
| `cirsoc.md` | Reglamentos CIRSOC para estructuras y construcción |
| `instalaciones.md` | Electromecánica, sanitaria, gas, agua, telecomunicaciones |
| `sismicidad-inpres.md` | INPRES-CIRSOC 103, zonas sísmicas, diseño antisísmico |
| `estudio-suelos.md` | Geotecnia, fundaciones, ensayos, normas |
| `bim-tecnologia.md` | BIM, IFC, coordinación, gemelos digitales |

## Routing del chat

| Pregunta | Archivo |
|---|---|
| "¿Cómo se arma un proyecto?" / "¿Etapas de diseño?" | `programa-arquitectonico.md` |
| "¿Cuántos m² vendibles tengo?" / "¿Factor K?" | `eficiencia-planta.md` |
| "¿Qué norma de estructura aplica?" | `cirsoc.md` |
| "¿Qué instalaciones tengo que prever?" | `instalaciones.md` |
| "¿La zona es sísmica?" / "¿Diseño antisísmico?" | `sismicidad-inpres.md` |
| "¿Hace falta estudio de suelos?" | `estudio-suelos.md` |
| "¿Conviene BIM?" | `bim-tecnologia.md` |

## Reglas para el chat

- **Estable:** normas técnicas, procedimientos, etapas, criterios de diseño.
- **🔴 Volátil:** valores específicos de cargas, factores zonales del INPRES, alícuotas de honorarios → consultar normas vigentes y aranceles de colegios.
- **Sensible:** todo proyecto serio requiere profesional matriculado (arquitecto/ingeniero).

## Ver también
- `../02-normativa/codigo-edificacion-caba.md`
- `../05-construccion/`
- `../14-costos-presupuesto/`
