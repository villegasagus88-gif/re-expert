---
title: "Plataformas de gestión integral del developer (PMS / CMS / ERP construcción)"
topic: "tecnologia"
subtopic: "plataformas"
jurisdiction: "Global / AR"
last_verified: "2026-05-12"
sources:
  - "Documentación pública de proveedores (Procore, Buildots, Autodesk, BIM 360, SAP)"
  - "Reportes de adopción Forrester / Gartner"
keywords: [procore, buildots, plangrid, autodesk construction cloud, bim 360, sap construction, oracle primavera, fieldwire, microsoft project, gestion integral, pms, cms, erp, integracion, single source of truth]
audience: ["cto", "developer", "project manager", "constructora", "controller"]
confidence: "media-alta"
---

# Plataformas de gestión integral

## TL;DR
- El stack del developer está fragmentado: CRM por un lado, ERP por otro, gestor de obra por otro, calidad en otro, BIM en otro. La fricción cuesta tiempo y errores.
- **Plataformas integrales** prometen un "single source of truth" por todo el ciclo: pre-construcción, obra, calidad, recepción, postventa.
- Los líderes globales: **Procore, Autodesk Construction Cloud, Oracle Aconex, SAP**.
- En AR los grandes developers van migrando; los medianos siguen con soluciones más livianas (Fieldwire, PlanGrid, planillas + Drive + WhatsApp).

---

## 1. Capas de software del developer

### 1.1 Pre-construcción y diseño
- BIM authoring: Revit, ArchiCAD.
- Coordinación: Navisworks, Solibri, BIM Track.
- Estimación: bibliotecas de precios + APU.
- Cómputo: takeoff manual o automático.

### 1.2 Comercial / preventa
- CRM: Salesforce, HubSpot, Tokko, Pipedrive.
- Marketing automation: Mailchimp, ActiveCampaign, RD Station.
- Plataformas portales: integración con Zonaprop, Argenprop.

### 1.3 Gestión de obra
- Plataforma de obra: Procore, Buildots, ACC, Fieldwire, PlanGrid.
- Cronograma: Primavera P6, Microsoft Project, Asana, Smartsheet.
- Compras: módulo del ERP o software dedicado.
- RFI / cambios: módulo dentro de la plataforma de obra.

### 1.4 Finanzas y backoffice
- ERP: SAP, Oracle, Microsoft Dynamics, ContaBilidad / Tango / Bejerman (AR).
- Tesorería: dentro del ERP.
- Contratos: módulo CLM (Contract Lifecycle Management) o estándar del ERP.

### 1.5 Postventa
- CRM con módulo postventa o ticketing dedicado (Zendesk, Freshdesk).
- Plataforma con app de cliente final.

### 1.6 Operación
- BMS / BAS.
- CMMS (Computerized Maintenance Management System): MaintainX, IBM Maximo, UpKeep.
- Plataforma de gemelo digital (en avanzados).

---

## 2. Plataformas integrales líderes

### 2.1 Procore
- Foco: gestión de obra end-to-end.
- Módulos: project management, financials, quality & safety, design coordination.
- Fortaleza: madurez en construcción, integración nativa con BIM.
- Mercado: dominante en US, creciente en LATAM.
- Pricing: percentual sobre volumen de obra gestionado.

### 2.2 Autodesk Construction Cloud (ACC)
- Integra: BIM 360, PlanGrid, BuildingConnected.
- Foco: continuidad desde el diseño BIM hasta obra.
- Fortaleza: ecosistema Autodesk (Revit, Navisworks).
- Mercado: amplio (incluye Argentina con representantes).
- Pricing: suscripción por usuario + módulos.

### 2.3 Oracle Aconex
- Foco: colaboración documental + workflow en grandes proyectos.
- Fortaleza: complejos megaproyectos, infraestructura.
- Mercado: APAC + grandes proyectos globales.

### 2.4 Bentley iTwin / SYNCHRO
- Foco: ingeniería + 4D + digital twin.
- Fortaleza: infraestructura, industrial.

### 2.5 Fieldwire / PlanGrid (parte de ACC)
- Foco: la obra día a día. Más liviano que Procore.
- Fortaleza: adopción rápida en jefes de obra.

### 2.6 SAP Construction / RPM
- Foco: ERP corporativo con módulo construcción.
- Fortaleza: empresas grandes ya con SAP.

### 2.7 Soluciones locales AR
- **PMU / Sicop / Klipper**: gestión de obra con módulos administrativos.
- **Bejerman / Tango**: ERPs locales con módulos para construcción.
- Stack típico mid-size AR: ERP local + Procore o BIM 360 + CRM + Excel.

---

## 3. Categorías especializadas

### 3.1 Visión computacional de obra
- **Buildots**: análisis de fotos / video con IA → avance por elemento.
- **Doxel**: similar, foco en cronograma.
- **OpenSpace** (más liviano): 360° + tracking de progreso visual.

### 3.2 Calidad y seguridad
- **Safesite, Fieldwire (módulo Safety)**: checklists, observaciones, NC.
- **iAuditor (SafetyCulture)**: checklists multipurpose.

### 3.3 Mantenimiento (CMMS)
- **MaintainX, UpKeep, Limble**: gestión de mantenimiento preventivo + tickets.
- **IBM Maximo, SAP PM**: corporativo grande.

### 3.4 Energy + sustainability
- **Measurabl**: ESG reporting + benchmark.
- **Honeywell Forge**: control + analytics.

---

## 4. Stack mínimo viable por tamaño

### 4.1 Developer chico (1-3 proyectos / año)
- ERP / contabilidad local.
- CRM simple (HubSpot free, Tokko).
- Carpeta compartida (Drive / OneDrive).
- WhatsApp Business para obra.
- Excel + Microsoft Project.

### 4.2 Mediano (4-10 proyectos / año)
- ERP local con módulo de obra.
- CRM dedicado.
- Plataforma de obra (Fieldwire / BIM 360 / Procore básico).
- BIM en proyecto y obra.

### 4.3 Grande (10+ proyectos / año)
- ERP corporativo (SAP, Oracle, MS Dynamics).
- Procore o ACC completo.
- BIM Level 2 + digital twin pilots.
- BI + analytics.
- Postventa con CRM dedicado.

---

## 5. Integración: el desafío real

### 5.1 Problema
- 10+ herramientas no hablan entre sí.
- Doble carga, inconsistencias, decisiones con datos viejos.

### 5.2 Soluciones
- **APIs nativas** entre plataformas (Procore + Salesforce, BIM 360 + Procore).
- **Middleware** (Zapier, Make, n8n, Workato) para integraciones simples.
- **iPaaS** (MuleSoft, Boomi) para integraciones empresariales.
- **Data warehouse** centralizado para reportes cross-sistema.

### 5.3 Data layer
- Modelo común mínimo: proyecto, unidad funcional, contrato, factura, certificado, persona.
- Data warehouse (Snowflake, BigQuery) consolida.
- Una sola fuente para reportes ejecutivos.

---

## 6. Decisiones críticas al elegir plataforma

### 6.1 ¿Best-of-breed o suite integrada?
- **Suite**: menos integración, menos features punteros.
- **Best-of-breed**: mejor en cada pieza, más fricción.
- Híbrido es lo más común.

### 6.2 ¿Local o cloud?
- Cloud es estándar 2024+.
- Local solo para empresas con compliance especial o redes no confiables.

### 6.3 ¿AR o global?
- Plataformas locales: precios en pesos, soporte local, módulos fiscales AR.
- Plataformas globales: features punteros, pero precio USD + brecha cambiaria + módulos fiscales propios.

### 6.4 ¿Adopción interna?
- Plataforma sin adopción es plata tirada.
- Plan de implementación + champion interno + capacitación obligatoria.

---

## 7. Costo total de propiedad (TCO)

### 7.1 Visible
- Licencia / suscripción.

### 7.2 Invisible (suele ser 2-5x la licencia)
- Implementación / consultoría.
- Capacitación.
- Integración con otras herramientas.
- Mantenimiento + updates.
- Soporte interno (1-2 admins en empresa grande).

### 7.3 Costos de no usar
- Errores de cómputo: 1-5% del costo de obra.
- Doble carga: horas-equipo perdidas.
- Decisiones tardías por datos viejos.
- Reclamos por mala documentación.

---

## 8. Tendencias 2025-2026

### 8.1 AI nativa en plataforma
- Procore Copilot, ACC AI Assistant.
- Análisis automático de RFIs, prelectura de contratos, sugerencia de prioridades.

### 8.2 Mobile-first
- Toda la operación se hace desde mobile.
- Offline-first en obras con mala conectividad.

### 8.3 Open APIs + estándares
- IFC para BIM.
- ISO 19650 como guía de proceso.
- WBS / cost code estandarizados.

### 8.4 Connected sites
- Sensores + cámaras + drones integrados a la plataforma.
- Plataforma se vuelve "operating system" del sitio.

---

## 9. Errores comunes

- Comprar plataforma y no entrenar al equipo.
- Implementar muchas herramientas a la vez → adopción cero.
- Subestimar la integración (50%+ del proyecto).
- Querer reemplazar Excel sin entender por qué la gente lo usa.
- No medir KPIs antes y después → no se sabe si funcionó.
- Empezar por features avanzados antes de los básicos (digital twin sin BIM en obra es absurdo).

---

## 10. Reglas operativas para el chat

- **Estable y respondible:** taxonomía de plataformas, casos de uso por categoría, stack mínimo por tamaño, decisiones al elegir, errores comunes.
- **🔴 Volátil:** precios específicos de licencias, capacidades exactas de cada plataforma (cambian trimestre a trimestre), partnerships locales.

---

**Ver también:**
- `./ai-workflows-developers.md`
- `./bim-gemelo-digital-operacion.md`
- `./reality-capture.md`
- `./automatizacion-procesos.md`
- `../05-construccion/gestion-diaria-obra.md`
- `../14-costos-presupuesto/control-presupuestario.md`
