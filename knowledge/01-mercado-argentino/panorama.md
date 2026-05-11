---
title: "Panorama del mercado inmobiliario argentino"
topic: "mercado"
subtopic: "panorama"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "INDEC — ISAC (Indicador Sintético de la Actividad de la Construcción)"
  - "INDEC — ICC (Índice del Costo de la Construcción)"
  - "Reporte Inmobiliario, Properati, ZonaProp Data"
  - "BCRA — Informe Monetario (créditos hipotecarios)"
keywords: [panorama, mercado argentino, amba, interior, ciclo inmobiliario, isac, icc, oferta, demanda]
audience: ["desarrollador", "inversor", "chat"]
confidence: "alta"
---

# Panorama del mercado inmobiliario argentino

## TL;DR
- AMBA (CABA + GBA) concentra el grueso del stock y de la oferta nueva. Córdoba, Rosario, Mendoza, Neuquén siguen.
- Ciclo del mercado AR está fuertemente acoplado a: **estabilidad cambiaria**, **crédito hipotecario** y **brecha cambiaria**.
- En ausencia de crédito (situación dominante post-2018), el mercado se mueve con **ahorro propio en USD**, lo que define producto, precio y plazos.
- 🔴 Volátil: cantidad de escrituras/mes, m² lanzados, valor m² por zona — derivar a fuente.

## 1. Tamaño y distribución

### 1.1 Stock por jurisdicción (aprox., órdenes de magnitud)
- CABA: ~1,6M unidades habitacionales.
- PBA: ~5,5M (AMBA pesa fuerte).
- Córdoba, Santa Fe, Mendoza, Tucumán, Salta, Neuquén → grandes mercados secundarios.
- Restantes provincias: mercados locales con dinámica propia.

### 1.2 Producción anual
- Permisos de construcción y ISAC marcan ritmo de oferta nueva.
- Promedio histórico de m² permisados depende fuertemente del ciclo macro.

## 2. Variables que definen el ciclo

| Variable | Cuándo impulsa | Cuándo frena |
|---|---|---|
| Crédito hipotecario (UVA o tradicional) | Tasas reales bajas + estabilidad | Tasas altas / volatilidad |
| Brecha cambiaria (oficial vs MEP/CCL) | Brecha alta → desarmar plazo fijo a ladrillo | Brecha baja → otras alternativas |
| Estabilidad de precios | Inflación baja permite planificar | Inflación alta dispara reajustes y aborta proyectos |
| Demanda externa de ahorro | Si AR es "barata" en USD → entran compradores | Si está cara → se frena |
| Confianza / política | Reglas claras → inversión | Cambios bruscos → freno |

## 3. Etapas del ciclo argentino (patrón histórico)

1. **Salida de crisis / dólar barato** → suelo y obra abaratan en USD → arranca pozo.
2. **Recomposición** → demanda mejora, valor m² sube, brecha pozo-terminado se abre.
3. **Pico** → escasez de suelo bien ubicado, costos en USD vuelven al promedio histórico.
4. **Enfriamiento** → tipo de cambio se atrasa, costos en USD se vuelven caros, freno de lanzamientos.
5. **Crisis** → suspensión de proyectos, ajuste, vuelta a fase 1.

## 4. AMBA vs interior

### CABA
- Producto: departamento, mix dominado por 1-2 ambientes.
- Demanda: inversor minorista para renta + comprador final clase media-alta.
- Drivers: cercanía a transporte, premios urbanísticos del Código (Ley 6099).

### GBA Norte (Vicente López, San Isidro, Pilar)
- Producto: barrio cerrado, country, edificios premium en corredor Panamericana.
- Demanda: familia clase media-alta, mudanza por calidad de vida.

### GBA Oeste / Sur
- Producto: vivienda de clase media, multifamily, lotes.
- Demanda: comprador final, planes estatales (Procrear).

### Córdoba / Rosario / Mendoza / Neuquén
- Cada una con dinámica propia (ver `../04-impuestos/provincial/`).
- Córdoba: mercado profundo, fideicomiso al costo muy desarrollado.
- Neuquén / Vaca Muerta: distorsiones por boom petrolero.

## 5. Drivers de demanda 2024-2026 (estructurales)

- **Vivienda como reserva de valor** (no rinde, pero conserva en USD).
- **Renta temporaria** (Airbnb, plataformas) — alteró rendimiento en CABA, Bariloche, Mendoza.
- **Logística / e-commerce** — auge post-pandemia, vacancia bajísima en parques.
- **Oficinas** — vacancia alta en clase B y C; clase A premium se mantiene.
- **Retail** — shoppings consolidados; street comercial sufre.

## 6. Riesgos y restricciones del mercado AR

- **Sin crédito hipotecario masivo** → operaciones contado o pozo con financiación del developer.
- **Tipo de cambio múltiple** → complejidad para ingresar / salir capital.
- **Carga impositiva alta y dispersa** → ver `../04-impuestos/_overview*` y provincial.
- **Burocracia urbanística** → plazos largos para aprobaciones (CABA, PBA).
- **Inflación** → reajuste de contratos de obra es crítico (ver `../05-construccion/certificacion-obra.md`).

## 7. Reglas operativas para el chat

- **Estable y respondible:** estructura del mercado, drivers, etapas del ciclo, diferencias regionales.
- **🔴 Volátil — derivar a fuente:** valor m² actual, cantidad de escrituras del mes, tasas hipotecarias vigentes, lanzamientos del trimestre.
- Si la pregunta es de magnitud actual, redirigir a:
  - INDEC (ISAC, ICC, EPH)
  - BCRA (créditos hipotecarios, REM)
  - Reportes privados: Reporte Inmobiliario, Properati, ZonaProp Data, Colliers, Cushman, JLL, CBRE.

## Ver también
- `./segmentos-y-productos.md`
- `./benchmarks.md`
- `../08-macro-argentina/ciclos-mercado.md`
