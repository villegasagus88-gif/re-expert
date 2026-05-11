---
title: "Datos, fuentes y BI para Real Estate"
topic: "proptech"
subtopic: "datos"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
sources:
  - "INDEC, BCRA, AFIP, ARBA, AGIP — fuentes oficiales"
  - "Properati Tools, Reporte Inmobiliario, Mercado Libre Real Estate Index"
keywords: [datos, fuentes, indec, bcra, scraping, api, properati, bi, business intelligence, indicadores, mercado, dataset]
audience: ["developer", "analista", "PM", "chat"]
confidence: "alta"
---

# Datos y fuentes

## TL;DR
- Datos de calidad = ventaja competitiva. En AR son escasos pero crecientes.
- Fuentes clave: **oficiales (INDEC, BCRA, AFIP, AGIP, ARBA)**, **privadas (Reporte Inmobiliario, Properati, Mercado Libre, Navent)**, **propias (CRM, ventas históricas)**.
- BI bien armado: dashboards en tiempo real → decisiones más rápidas.

## 1. Fuentes oficiales (gratuitas)

### 1.1 INDEC
- ICC, IPC, EPH (Encuesta Permanente de Hogares).
- Estadísticas demográficas (censo 2022).
- Permisos de construcción municipales agregados.
- API + descargas CSV.

### 1.2 BCRA
- Cotización FX (oficial, MEP, CCL).
- Tasas de interés (BADLAR, PASE, Leliq).
- UVA diaria.
- Préstamos hipotecarios (estadísticas).

### 1.3 AFIP
- Padrón fiscal.
- Constancias inscripción.
- API para fac electrónica.

### 1.4 AGIP (CABA)
- Padrón ABL.
- Catastro digital.
- Valuación fiscal.

### 1.5 ARBA (PBA)
- Padrón inmobiliario.
- Catastro online.

### 1.6 RPI / RGNR
- Consultas con costo (escritura, certificado dominio).
- Sin API pública open.

### 1.7 Datos abiertos
- Portal `datos.gob.ar`.
- Catastros municipales abiertos (CABA tiene buen catalog).
- IDERA (Infraestructura de Datos Espaciales).

## 2. Fuentes privadas

### 2.1 Portales / marketplaces
- ZonaProp (estadísticas trimestrales gratuitas + reportes pagos).
- Argenprop / Reporte Inmobiliario.
- Mercado Libre Real Estate Index.
- Properati Tools.

### 2.2 Brokers globales
- Colliers, Cushman & Wakefield, JLL, CBRE — reportes sectoriales (oficinas, logística, retail, residencial).
- Mayoría públicos.

### 2.3 Cámaras
- CEDU, AEV, CIA, CAC, COCAMBA, CUCICBA — informes sectoriales.

### 2.4 Bases pagas
- Tasacasa, Mavtech (AVM/comparables).
- LinkedIn Sales Navigator (B2B).

## 3. Scraping

### 3.1 Por qué se hace
- Construir bases de comparables.
- Monitorear competencia.
- Detectar oportunidades.

### 3.2 Cómo
- Python (Scrapy, Playwright, Selenium).
- Servicios cloud (Bright Data, Apify).

### 3.3 Limitaciones legales
- Términos de uso de cada portal.
- Ley 25.326 (datos personales si hay PII).
- Robots.txt.
- Buena práctica: rate limit + no afectar servicio.

### 3.4 Ética
- Scraping para uso interno / análisis: zona gris habitual.
- Redistribuir / comercializar: riesgo legal.

## 4. APIs disponibles

### 4.1 Públicas
- BCRA: Estadísticas Cambiarias API.
- INDEC: Datos vía CSV/Excel mayormente.
- AFIP: WSAA + WSFE para fac.
- Datos.gob.ar: API REST.

### 4.2 Privadas
- ZonaProp Office (asociados).
- Properati Tools.
- MercadoLibre API (productos, pero limitado para RE).

### 4.3 Servicios geo
- Google Maps Platform.
- Mapbox.
- OpenStreetMap.

## 5. Indicadores clave del sector

### 5.1 Macro
- ICC, IPC, UVA, FX MEP, BADLAR.

### 5.2 Sectoriales
- Precio/m² por barrio + segmento.
- Cap rate medio por producto.
- Vacancia oficinas/retail.
- Stock vs absorción.
- Permisos de obra.
- Escrituras mensuales (CABA + PBA).

### 5.3 Operativos (KPI propio)
- CPL, CAC, conversión por canal.
- Tiempo medio en pipeline.
- NPS posventa.
- Margen por proyecto.

## 6. Stack BI

### 6.1 Datastore
- **Google Sheets / Airtable**: para equipos chicos.
- **PostgreSQL / BigQuery / Snowflake**: para escala.
- **Notion + Databases**: para colaboración.

### 6.2 ETL / pipelines
- Make/Zapier para flujos simples.
- Fivetran / Airbyte para enterprise.
- Custom Python para específicos.

### 6.3 Visualización
- **Looker Studio (Data Studio)**: free, robusto.
- **Power BI**: ecosistema Microsoft.
- **Tableau**: enterprise.
- **Metabase**: open source.

### 6.4 IA / ML
- Notebooks (Colab, Jupyter).
- AutoML (BigQuery ML, Vertex AI, Azure ML).
- Modelos custom (scikit-learn, PyTorch).

## 7. Dashboards típicos para developer

### 7.1 Comercial
- Leads por canal por mes.
- Conversión por etapa.
- Pipeline valorizado.
- Cierre estimado mensual.

### 7.2 Obra
- Avance físico vs financiero por proyecto.
- EVM (CPI, SPI).
- Forecast cierre.

### 7.3 Financiero
- Cashflow real vs proyectado.
- Cobranza pendiente.
- Posición FX.

### 7.4 Operativo
- Stock disponible por proyecto.
- Tiempo medio respuesta lead.
- NPS posventa.

## 8. Buenas prácticas

### 8.1 Una fuente de verdad
- Datos siempre desde CRM/ERP, no Excel paralelo.

### 8.2 Versioning + auditoría
- Cambios trackeados.
- Reportes históricos no se modifican (snapshot).

### 8.3 Definiciones explícitas
- "Lead", "venta", "metros vendidos" tienen una definición única documentada.

### 8.4 Calidad de datos
- Validaciones en input.
- Cleaning periódico.
- Owner de cada tabla.

### 8.5 Acceso por rol
- No todos ven todo.
- Cumplir Ley 25.326.

## 9. Errores comunes

- Reportes mensuales hechos a mano cada mes.
- Excels paralelos con números distintos.
- Métricas sin definición clara.
- Mezclar moneda (ARS, USD, UVA) sin aclarar.
- No invertir en BI hasta que es tarde.

## 10. Reglas operativas para el chat

- **Estable:** mapa de fuentes, stack BI, indicadores clave.
- **🔴 Volátil:** valores específicos de indicadores → fuente oficial.
- **Sensible:** scraping y manejo de datos personales requieren cumplir marco legal.
- Si el usuario pregunta "¿de dónde saco data del mercado?": INDEC + BCRA + portales + reportes brokers globales + base propia.

## Ver también
- `./automatizacion-procesos.md`
- `./ia-en-real-estate.md`
- `../_meta/fuentes-oficiales.md`
- `../01-mercado-argentino/benchmarks.md`
- `../08-macro-argentina/`
