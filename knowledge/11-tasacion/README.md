---
title: "Tasación y valuación inmobiliaria — overview"
topic: "tasacion"
subtopic: "overview"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Resolución CPAU 4/2015 — Normas de tasación"
  - "Ley 22.802 — Tribunal de Tasaciones de la Nación"
  - "Normas IVS (International Valuation Standards)"
  - "CCyCN — arts. 1133, 1273"
keywords: [tasacion, valuacion, metodos valuacion, comparativo, costo, capitalizacion, residual, ttn, tribunal tasaciones, idoneidad, ttu, cpau]
audience: ["desarrollador", "tasador", "inversor", "abogado", "chat"]
confidence: "alta"
---

# 11 — Tasación y valuación

## TL;DR
- La tasación es el acto profesional que determina el **valor económico** de un inmueble en una fecha dada y con un fin específico.
- Tres métodos clásicos: **comparativo** (mercado), **costo** (reposición), **capitalización** (renta).
- Para suelo de desarrollo: **método residual** (valor del suelo derivado del proyecto).
- En AR la tasación la firma un profesional habilitado (arquitecto/ingeniero matriculado, corredor inmobiliario, ingeniero agrónomo según el caso).
- **Tasación ≠ valuación fiscal**: la fiscal es para impuestos; la de mercado es para operación.

## Archivos del módulo

| Archivo | Contenido |
|---|---|
| `metodos-valuacion.md` | Comparativo, costo, capitalización — cuándo usar cada uno |
| `metodo-residual-suelo.md` | Valor de suelo derivado del proyecto (clave para developer) |
| `tribunal-tasaciones-nacion.md` | TTN — rol, dictámenes, expropiaciones |
| `tasacion-vs-valuacion-fiscal.md` | Diferencia entre valor de mercado y valuación fiscal |
| `normas-profesionales.md` | Quién puede tasar, idoneidad, CPAU/TTU, responsabilidad |

## Routing del chat

| Pregunta | Archivo |
|---|---|
| "¿Cómo se tasa un departamento?" | `metodos-valuacion.md` |
| "¿Cuánto vale mi terreno para un desarrollo?" | `metodo-residual-suelo.md` |
| "¿Quién puede firmar una tasación?" | `normas-profesionales.md` |
| "Me están expropiando, ¿cómo se calcula la indemnización?" | `tribunal-tasaciones-nacion.md` |
| "¿Por qué AGIP me cobra un valor distinto al de mercado?" | `tasacion-vs-valuacion-fiscal.md` |

## Reglas para el chat

- **Estable y respondible:** métodos, lógica, cuándo aplicar cada uno, qué firma cada profesional.
- **🔴 Volátil — NO dar:** valor m² puntual, valor del terreno X. Derivar a tasador.
- **Sensible:** tasación formal solo profesional matriculado.

## Ver también
- `../01-mercado-argentino/benchmarks.md`
- `../12-suelo-y-dominio/`
- `../06-financiero/`
