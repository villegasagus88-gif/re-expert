---
title: "Mercado inmobiliario argentino — overview"
topic: "mercado"
subtopic: "overview"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "CEDU (Cámara Empresaria de Desarrolladores Urbanos)"
  - "AEV (Asociación Empresarios de la Vivienda)"
  - "CIA (Cámara Inmobiliaria Argentina)"
  - "INDEC — Construcción ISAC, ICC"
  - "BCRA — REM, créditos hipotecarios"
keywords: [mercado argentino, real estate ar, panorama inmobiliario, segmentos, players, benchmarks, portales]
audience: ["desarrollador", "inversor", "chat"]
confidence: "alta"
---

# 01 — Mercado Argentino

## TL;DR
- Mercado fragmentado por jurisdicción: AMBA concentra >60% del stock y de la oferta nueva.
- Segmentos: **residencial**, **oficinas**, **retail**, **logística/industrial**, **hotelería**, **alquiler temporario**, **usos especiales**.
- Moneda funcional: **USD** para precio de venta y suelo; **ARS** para construcción y servicios.
- Volatilidad estructural: precios y rendimientos cambian rápido — derivar a fuentes en vivo.

## Archivos del módulo

| Archivo | Contenido |
|---|---|
| `panorama.md` | Tamaño del mercado, ciclo actual, AMBA vs interior |
| `segmentos-y-productos.md` | Residencial, oficinas, retail, logística, hotelería, alquiler temporario, usos especiales |
| `players-y-actores.md` | Developers, fondos, brokers, constructoras, cámaras |
| `benchmarks.md` | Rangos históricos, cap rate, brecha pozo-terminado, vacancia (con regla volátil) |
| `portales-y-canales.md` | ZonaProp, Argenprop, ML Inmuebles, Properati, Idealista, embudo |

## 🔴 Datos volátiles vs 🟢 estables

Aplican las reglas de `_meta/politica-datos.md`.

**🔴 Volátil — el chat NO da el número:**
- Valor m² USD por barrio / zona (consultar ZonaProp Data, Reporte Inmobiliario, Properati Index).
- Rentabilidad bruta y neta por zona.
- Volumen mensual de escrituración (Colegio de Escribanos CABA + PBA).
- Cap rate de referencia (Colliers, Cushman, JLL, CBRE).
- Vacancia de oficinas / logística.
- Listados activos y absorción del mes.
- Tarifas y CPL de portales.

**🟡 Semivolátil (rango histórico documentado, marcar como tal):**
- Rango cap rate por segmento.
- Brecha pozo-terminado.
- Ratios estructurales de costos.

**🟢 Estable — respuesta directa:**
- Caracterización de segmentos y productos.
- Estructura del ecosistema (players, cámaras).
- Drivers del ciclo argentino.
- Embudo comercial típico y KPIs estructurales.
- Cómo se construyen las métricas (cap rate, absorción, vacancia, comparables).

**Para datos del día → derivar a:** Colegio de Escribanos CABA y PBA, Reporte Inmobiliario, ZonaProp / Properati Data, Colliers / Cushman & Wakefield / JLL / CBRE, BCRA, INDEC.

## Reglas operativas

- **Cierres reales > listados.** Los listados son orientativos, no precio de cierre.
- Indexar todo precio en **USD** (preferentemente MEP) y aclarar fecha.
- Marcar `last_verified` mensual; los datos envejecen rápido.
