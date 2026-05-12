---
title: "Datos alternativos para market intelligence inmobiliaria"
topic: "tecnologia"
subtopic: "alt-data"
jurisdiction: "Global / AR"
last_verified: "2026-05-12"
sources:
  - "Práctica observada en REIT / asset managers globales"
  - "Documentación pública de proveedores (Placer, Reonomy, SafeGraph, Sentinel Hub)"
keywords: [datos alternativos, alt data, satelite, sentinel, copernicus, mobility, footfall, geolocalizacion, anonymized data, scraping, portales, zonaprop, argenprop, dwell time, big data, market intelligence, mi, hot zones]
audience: ["developer", "analista", "investor", "cmo", "data"]
confidence: "media-alta"
---

# Datos alternativos para Market Intelligence

## TL;DR
- "Alt data" = todo dato útil **fuera** del Multiple Listing Service / portales tradicionales: satélite, mobility, scraping, redes sociales, energía, contactos comerciales.
- Permite **anticipar** dinámicas de mercado antes de que se reflejen en precios.
- Casos típicos: detectar zonas calientes, validar comportamiento esperado de un proyecto, evaluar competencia, estimar absorción.
- En AR el dato MLS oficial es opaco → alt data tiene más valor relativo que en US/EU.

---

## 1. Categorías de alt data

### 1.1 Satelitales
- Imagen satelital (óptica, radar).
- Cambio temporal (qué se construye, qué se demuele).
- Espectrales (calidad del aire, vegetación, suelo).

### 1.2 Mobility / footfall
- Geolocalización agregada (datos anonimizados de celulares + apps).
- Patrones de visita a barrios / shopping / oficinas.
- Tiempo de permanencia (dwell time).
- Origen / destino agregados.

### 1.3 Scraping y web
- Listings de portales (Zonaprop, Argenprop, Mercado Libre, Properati).
- Reviews (Google Maps, Tripadvisor, Foursquare).
- Redes sociales (Instagram, TikTok, Twitter/X) — tendencias y menciones.
- Web de competidores (precios, lanzamientos).

### 1.4 Datos públicos estructurados
- Catastro municipal.
- Estadísticas oficiales (INDEC, GCBA estadísticas, censo).
- Padrones de obra (permisos municipales).
- Resoluciones CNV, BCRA.
- Registro de la propiedad inmueble (parcial).

### 1.5 Consumo y servicios
- Datos agregados de electricidad / gas / agua por área.
- Tráfico de banda ancha (cable / fibra) por zona.

### 1.6 Negocio y comercio
- Apertura / cierre de locales comerciales.
- Tickets promedio por zona (datos de procesadoras de pago).
- Densidad de tipos de negocio (cafetería, retail, servicios).

---

## 2. Casos de uso

### 2.1 Detección de zonas calientes
- Footfall creciente + apertura de comercios premium + cambio satelital (obras) = barrio en transición.
- Anticipación de 6-18 meses respecto a precios.

### 2.2 Validación de proyecto
- Antes de comprar terreno: medir footfall de hora, día, semana.
- Validar mix de usos esperado.

### 2.3 Pricing competitivo
- Scraping diario de portales.
- Tracking de precios por proyecto similar.
- Detección de cambios de listings (baja de precio = ajuste de mercado).

### 2.4 Absorción y velocidad de venta
- Cuántas unidades hay en venta por barrio + cuántas se descartan por mes.
- Tiempo medio en mercado.
- Cuántos lanzamientos similares en pipeline.

### 2.5 Market sizing
- Densidad de hogares + ingreso + tipo de vivienda → estimar mercado objetivo.

### 2.6 Detección de gentrificación / deterioro
- Cambio en mix comercial + tipo de tráfico + reformas.

### 2.7 Validación de oficinas
- Footfall durante horarios laborales.
- Conectividad / banda ancha.
- Presencia de tipos de empresas (LinkedIn agregado).

---

## 3. Fuentes específicas (referenciales)

### 3.1 Satelital
- **Copernicus / Sentinel** — gratuito, resolución 10-20 m.
- **Planet Labs** — comercial, resolución diaria.
- **Maxar** — comercial, altísima resolución (puntual).
- **Sentinel Hub** — API simplificada para acceso.

### 3.2 Mobility (global)
- SafeGraph, Veraset, Outlogic, Placer, Cuebiq.
- En AR: datos menos accesibles, algunos proveedores telco con productos B2B.

### 3.3 Listings AR
- Zonaprop, Argenprop, Properati, Mercado Libre, Remax.
- Properati Data (propiedad de OLX) para datos agregados.
- Estimaciones propias con scraping (cuidado con TOS).

### 3.4 Catastro / públicos
- GCBA Buenos Aires Data.
- ARBA PBA.
- Datos AFIP / RPI (acceso parcial).
- Mapas IGN.

### 3.5 Comercial
- Google Places / Maps API (apertura y cierre, reviews).
- Foursquare.

---

## 4. Workflow típico de un proyecto de alt data

### 4.1 Definir la pregunta
- ¿Qué decisión vamos a tomar con este dato?
- Sin pregunta concreta, el data lake se llena de basura inútil.

### 4.2 Identificar dataset
- ¿Qué dato responde la pregunta?
- ¿Qué granularidad necesito (manzana, radio censal, barrio)?
- ¿Qué frecuencia (diaria, semanal, mensual)?

### 4.3 Procurar fuente
- Pública (mejor) vs API comercial (medio) vs scraping (último recurso, riesgo legal).

### 4.4 Ingest y limpieza
- ETL hacia data warehouse.
- Validación (nulos, outliers, duplicados).
- 50-70% del esfuerzo total.

### 4.5 Modelado / análisis
- Estadística descriptiva primero.
- Modelo si la pregunta lo requiere.
- Visualización para storytelling.

### 4.6 Decisión / acción
- Conclusión accionable.
- Implementación.
- Medición de resultado.

---

## 5. Análisis específicos comunes

### 5.1 Hot zone score
- Combinación de:
  - Crecimiento de precios listing (últimos 12 meses).
  - Footfall creciente.
  - Aperturas comerciales premium.
  - Permisos municipales de obra.
  - Calidad de tráfico (gente joven profesional, p.ej.).
- Score 0-100 por barrio o radio censal.

### 5.2 Análisis competitivo
- Por cada proyecto activo dentro del polígono:
  - Precio /m².
  - Tipologías.
  - Velocidad de venta (estimada por cambios de listings).
  - Tiempo de obra.
- Visualización: heatmap + lista.

### 5.3 Demanda potencial
- Densidad de hogares por radio + ingreso estimado + situación habitacional (alquiler vs propio).
- Crucificar con stock disponible → indicador de gap.

### 5.4 Path of progress
- Identificar barrios adyacentes a hot zones que aún no subieron de precio.
- Apostar a la propagación.

---

## 6. Integración con el resto del stack

### 6.1 Conectar con CRM y comercial
- Score del barrio + perfil del lead → mejor matching.
- Personalización de mensaje.

### 6.2 Conectar con inversión
- Alimentar comité de inversión con dashboard estandarizado por proyecto.

### 6.3 Conectar con marketing
- Targeting geográfico fino.
- Mensajes adaptados al barrio.

---

## 7. Visualización y dashboard

### 7.1 Stack típico
- **GIS**: QGIS (open) / ArcGIS (comercial) / Kepler.gl / Mapbox.
- **BI**: Metabase, Looker Studio, PowerBI, Tableau.
- **Dashboards programáticos**: Streamlit, Dash, Observable.

### 7.2 Vistas críticas
- Mapa con capas filtrables (precio, footfall, obras).
- Time series (evolución de cada indicador).
- Comparativa entre zonas / proyectos.
- Alertas (cambio significativo en última semana).

---

## 8. Marco legal y ético

### 8.1 PDP — Ley 25.326 (AR)
- Datos personales protegidos. Datos anonimizados agregados generalmente OK.
- Footfall por radio censal con > X usuarios = anonimizado suficiente.
- Datos a nivel individual = consentimiento explícito.

### 8.2 Términos de servicio
- Scraping de portales: muchos lo prohíben en TOS.
- Risk management: o se contrata el dato (Properati Data), o se asume riesgo.

### 8.3 Datos de competencia
- Inteligencia competitiva legal: precios públicos, listings, comunicados.
- Inteligencia ilegal: ingeniería social, acceso no autorizado, copyright.

---

## 9. Costos referenciales

| Item | Costo aproximado |
|---|---|
| API satelital Sentinel | Gratis (con límites) |
| API satelital Planet | USD 5k-50k/año |
| Mobility data (US) | USD 20k-200k/año |
| Mobility data (AR, donde disponible) | USD 10k-80k/año |
| Scraping infrastructure | USD 200-2000/mes |
| Properati Data | USD por consulta o suscripción |
| Equipo data (1 senior + 1 analyst) | Salarios |
| Plataforma BI | USD 50-500/mes según herramienta |

---

## 10. Errores comunes

- Coleccionar dato sin saber la pregunta → data lake muerto.
- Confiar en una sola fuente → sesgo.
- No validar el dato (footfall sin ground truth).
- Sobre-extrapolación (pasar de tendencia agregada a decisión individual).
- Ignorar marco legal (PDP, TOS) → riesgo reputacional o legal.
- No invertir en limpieza → modelos mal alimentados.

---

## 11. Reglas operativas para el chat

- **Estable y respondible:** taxonomía de datos, casos de uso, workflow, stack, consideraciones legales.
- **🔴 Volátil:** precios de proveedores, disponibilidad de datasets puntuales (cambia), regulación PDP específica (puede actualizarse).

---

**Ver también:**
- `./ai-workflows-developers.md`
- `./datos-y-fuentes.md`
- `./panorama-proptech-ar.md`
- `../01-mercado-argentino/segmentos-y-zonas.md`
- `../07-comercial/tasacion-previa-lanzamiento.md`
- `../11-tasacion/metodo-comparativo.md`
