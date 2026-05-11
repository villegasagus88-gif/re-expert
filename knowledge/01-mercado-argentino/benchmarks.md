---
title: "Benchmarks de mercado AR — referencia y rangos"
topic: "mercado"
subtopic: "benchmarks"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "Reporte Inmobiliario"
  - "ZonaProp Data, Properati Index"
  - "Colliers, Cushman & Wakefield, JLL, CBRE — reportes trimestrales"
  - "INDEC — EPH, ICC"
keywords: [benchmarks, cap rate, rendimiento, valor m2, vacancia, brecha pozo terminado, valor suelo, ratios desarrollo]
audience: ["desarrollador", "inversor", "chat"]
confidence: "media"
priority: "alta"
---

# Benchmarks de mercado AR

## TL;DR
- Los **valores absolutos** (USD/m², cap rate, vacancia) son **🔴 volátiles** — el chat NUNCA da número del día.
- Los **rangos históricos y ratios estructurales** sí son estables y respondibles.
- Esta página es la guía de **cómo interpretar** y **dónde mirar**, no la tabla de valores actuales.

## 1. Cómo usar esta página (regla para el chat)

| Pregunta | Cómo responder |
|---|---|
| "¿Cuánto vale el m² en X?" | NO dar número. Derivar a ZonaProp / Reporte Inmobiliario / Properati. Sí dar **rango histórico** si está documentado. |
| "¿Cuál es la vacancia de oficinas A?" | NO dar número. Derivar a Colliers/Cushman/JLL/CBRE (reportes trimestrales). |
| "¿Qué rinde un depto. en Palermo?" | Explicar fórmula + rango histórico + factores. Derivar a fuente para valor del día. |
| "¿Cuánto cuesta construir el m² en AR?" | Derivar a ICC INDEC + listas de proveedor. Sí dar estructura del costo. |

## 2. Estructura de un valor m² (componentes estables)

```
Precio venta m² = Costo suelo (por m² vendible)
                + Costo construcción m² (hard cost)
                + Honorarios profesionales (8-15%)
                + Costos indirectos + gerenciamiento (3-7%)
                + Impuestos (variable por estructura fiscal)
                + Comercialización (3-5%)
                + Imprevistos (5-10%)
                + Utilidad del developer (12-25% sobre venta total típico)
```

> Esta estructura es estable. Los valores absolutos no.

## 3. Cap rate — rangos de referencia (orden de magnitud histórico)

> No son valores del día. Sirven para "¿está en línea o fuera de rango?".

| Segmento | Cap rate USD bruto típico (rango histórico) |
|---|---|
| Residencial CABA (renta tradicional) | 2-4% |
| Residencial CABA (alquiler temporario) | 5-9% |
| Oficinas A CABA | 7-10% |
| Logística clase A AMBA | 9-12% |
| Retail shopping (alquiler vinculado a ventas) | variable (no comparable lineal) |
| Industrial | 8-12% |

> 🔴 Estos rangos son referencias históricas, no valores corrientes. Para hoy: reportes Colliers / Cushman / JLL / CBRE.

## 4. Brecha pozo vs terminado (residencial)

- Patrón histórico: el **pozo** se vende con un **descuento del 25-40%** sobre el terminado.
- La brecha se cierra a medida que avanza la obra.
- Cuando la brecha cae por debajo del 15%, el incentivo a comprar en pozo se diluye.
- 🔴 Brecha actual: derivar a Reporte Inmobiliario / ZonaProp Data.

## 5. Vacancia (referencia)

| Segmento | Vacancia "sana" |
|---|---|
| Oficinas A CABA | < 10% |
| Oficinas B/C | históricamente mayor; post-pandemia muy alta |
| Logística AMBA | < 5% (mercado tensionado) |
| Residencial alquiler tradicional | n/a (mercado fragmentado) |

## 6. Ratios estructurales del desarrollo

### 6.1 Suelo / venta total
- Regla práctica para que un proyecto cierre: **valor del suelo ≤ 15-25%** del ingreso bruto por venta.
- Si supera 30%, el proyecto suele forzarse vía permuta o premio urbanístico.

### 6.2 Costo de construcción / venta total
- Hard cost típico: 40-55% del ingreso bruto.
- Indirectos + honorarios: 12-20%.
- Comercialización + impuestos: 8-12%.
- Utilidad objetivo: 15-25%.

### 6.3 m² vendible / m² construido
- Edificio eficiente residencial AMBA: 75-85%.
- Por debajo de 70% el proyecto pierde rentabilidad rápido.

## 7. Plazos típicos (referencia, no garantía)

| Etapa | Plazo típico |
|---|---|
| Anteproyecto y aprobación municipal | 6-18 meses (CABA) |
| Obra (edificio 10.000-20.000 m²) | 24-36 meses |
| Pre-venta para arrancar obra | 30-50% pre-vendido |
| Comercialización completa post-obra | 6-24 meses (según ciclo) |

## 8. Indicadores macro a mirar (relacionados)

- **ICC INDEC** — costo construcción en ARS (mensual).
- **CAC** — Cámara Argentina de la Construcción, índices propios.
- **UVA** — Unidad de Valor Adquisitivo (BCRA).
- **MEP / CCL** — dólar financiero (ámbito, Rava).
- **EMBI+ AR** — riesgo país (JP Morgan).
- **REM** — Relevamiento de Expectativas (BCRA).

Ver `../08-macro-argentina/*` para detalle.

## 9. Fuentes vivas a las que derivar

| Tipo de dato | Fuente |
|---|---|
| Valor m² residencial por zona | ZonaProp Data, Reporte Inmobiliario, Properati Index |
| Cap rate / vacancia oficinas | Colliers, Cushman & Wakefield, JLL, CBRE (reportes trimestrales) |
| ICC, ISAC | INDEC |
| Tasas y crédito | BCRA |
| Cambiario | BCRA / ámbito / Rava |
| Construcción CAC | Cámara Argentina de la Construcción |

## 10. Reglas operativas para el chat

1. NUNCA dar valor m² ni cap rate puntual sin fuente del día.
2. Sí dar rango histórico + factores que mueven el valor.
3. Si el usuario pide un cálculo concreto, pedir el valor m² (que él consulte hoy) y armar el cálculo encima.
4. Marcar siempre **fecha del rango** que se cita.

## Ver también
- `./panorama.md`
- `./segmentos-y-productos.md`
- `../_meta/politica-datos.md`
- `../_meta/fuentes-oficiales.md`
