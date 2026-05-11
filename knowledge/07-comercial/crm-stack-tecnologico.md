---
title: "CRM y stack tecnológico comercial inmobiliario"
topic: "comercial"
subtopic: "crm-stack"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [crm, tokko, hubspot, salesforce, zoho, pipedrive, whatsapp business, api, automatizacion, lead management, ventas inmobiliarias]
audience: ["broker", "developer", "comercial", "chat"]
confidence: "alta"
---

# CRM y stack tecnológico

## TL;DR
- Sin **CRM** un equipo comercial inmobiliario pierde 30-50% de leads.
- En AR el ecosistema mainstream: **Tokko Broker** (vertical RE) + **HubSpot** (general, escalable) + **WhatsApp Business API** (canal #1) + integraciones con portales (ZonaProp, ML, Argenprop).
- Stack mínimo viable: CRM + WhatsApp + portales + analítica.

## 1. Funciones de un CRM inmobiliario

### 1.1 Gestión de leads
- Captura desde portales, formularios web, redes, WhatsApp.
- Asignación automática (round robin, geografía, producto).
- Segmentación.

### 1.2 Pipeline / embudo
- Etapas: nuevo → contactado → calificado → visita → oferta → cerrado.
- Conversión por etapa.
- Tiempo en cada etapa.

### 1.3 Inventario de propiedades
- Stock unificado de unidades en venta / alquiler.
- Fichas con fotos, planos, video, brochure.
- Disponibilidad en tiempo real (vendido, reservado, disponible).

### 1.4 Publicación multi-portal
- Carga única → se replica a ZonaProp, ML, Argenprop, Properati.
- Sincronización de disponibilidad.

### 1.5 Comunicaciones
- Plantillas de WhatsApp, email, SMS.
- Tracking de aperturas, respuestas.

### 1.6 Reporting
- KPIs comerciales (CPL, CTR, conversión, ROI por canal).
- Dashboards.

## 2. CRMs específicos para RE en AR

### 2.1 Tokko Broker
- Líder en AR para inmobiliarias.
- Multi-portal nativo.
- App móvil.
- Pricing por usuario.
- Integraciones: WhatsApp, portales, formularios web.

### 2.2 Properati Tools
- Suite del portal Properati (OLX).
- Gestión + analítica.

### 2.3 Naranja Suite / ZonaProp Office
- Soluciones de ZonaProp para inmobiliarias asociadas.

### 2.4 Otros locales
- Bisman, Mediahaus, Bidonia, Soluciones Inmobiliarias.

## 3. CRMs generales aplicados a RE

### 3.1 HubSpot
- Robusto, marketing + ventas + servicio.
- Plan free → paid escalable.
- Excelente automation + analytics.
- Necesita customización para RE vertical.

### 3.2 Salesforce
- Enterprise.
- Salesforce Real Estate Cloud disponible.
- Costoso pero potente.

### 3.3 Pipedrive
- Simple, foco ventas.
- Buen ROI para equipos chicos.

### 3.4 Zoho CRM
- Buen costo-beneficio.
- Suite completa (mail, marketing, etc.).

### 3.5 Monday.com
- Más bien gestión de proyectos pero también ventas.

## 4. WhatsApp como canal central

### 4.1 WhatsApp Business (app)
- Gratis.
- Limitada para escalar (1 número, 1 dispositivo principal).
- Catálogo de productos.

### 4.2 WhatsApp Business API (Meta)
- Múltiples agentes en el mismo número.
- Integración con CRM.
- Plantillas aprobadas para outbound.
- BSP (Business Solution Providers): Twilio, 360dialog, Sirena, Cliengo, Wati, Whaticket.

### 4.3 Buenas prácticas
- Respuesta < 5 minutos (vital para conversión RE).
- Plantillas para flujos repetitivos.
- Bot inicial (calificación) + agente humano para cerrar.
- Cumplir Política de Privacidad de WhatsApp.

## 5. Integración con portales

### 5.1 Portales relevantes (AR)
- ZonaProp (Navent).
- Argenprop.
- ML Inmuebles (MercadoLibre).
- Properati (OLX).

### 5.2 APIs / feeds
- XML / API feeds para sincronización automática.
- CRM publica + recibe leads.

### 5.3 Métricas por portal
- CPL (costo por lead).
- Calidad de lead (conversión a visita y cierre).
- ROI por inversión.

## 6. Marketing automation

### 6.1 Email marketing
- Mailchimp, HubSpot, ActiveCampaign, Sendinblue.
- Secuencias drip para nurturing.

### 6.2 SMS / WhatsApp masivo
- Cuidar opt-in y plantillas aprobadas.

### 6.3 Retargeting
- Meta Ads, Google Ads remarketing.
- Pixel + custom audiences.

### 6.4 Chatbots
- Calificación inicial 24/7.
- Captura datos básicos antes de pasar a humano.
- Manychat, Cliengo, Drift, propio con API.

## 7. Analítica y BI

### 7.1 Stack típico
- Google Analytics 4.
- Meta Business Suite.
- Looker Studio (ex Data Studio) o Power BI / Tableau para dashboards.
- Hotjar / Microsoft Clarity para UX.

### 7.2 KPIs clave
- **CPL** por canal.
- **CTR** en anuncios.
- **Conversión lead → visita**: meta 15-25%.
- **Conversión visita → reserva**: meta 10-20%.
- **CAC** (Costo de Adquisición de Cliente).
- **LTV** (en BTR / property management).
- **Tiempo de respuesta** primer contacto.

### 7.3 Atribución
- Multi-touch (un comprador suele tener 5-15 interacciones antes de comprar).
- UTM tracking en todos los links.

## 8. Otros componentes del stack

### 8.1 Tour virtual / video
- Matterport (3D).
- Drone + edición.
- Video walk-through para WhatsApp.

### 8.2 E-firma
- DocuSign, Signaturit, ZapSign, FirmaCom.
- Para boletos, reservas, OK comerciales.
- Validez legal AR (Ley 25.506 + Decreto 182/19).

### 8.3 Cobranzas
- MercadoPago, Modo, links de pago.
- Para reservas / señas.

### 8.4 Documentación
- Drive, Notion, Dropbox.
- Plantillas, brochure, fichas legales.

## 9. Stack mínimo viable (developer mediano AR)

| Componente | Herramienta sugerida | Costo aprox / mes |
|---|---|---|
| CRM | Tokko / HubSpot | USD 50-300 |
| WhatsApp API | BSP (Wati, Sirena) | USD 30-150 |
| Portales | ZonaProp + ML + Argenprop | USD 200-1.000 |
| Email automation | HubSpot / Mailchimp | USD 0-100 |
| BI | Looker Studio (free) | 0 |
| E-firma | ZapSign / DocuSign | USD 10-50 |

> 🔴 Costos orientativos; varían con escala y plan.

## 10. Errores comunes

- Implementar CRM y no usarlo (data sucia).
- Múltiples CRMs sin integrar (Tokko + Excel + Drive).
- WhatsApp sin BSP en operación >2 agentes (no escala).
- No medir CPL / ROI por canal.
- Respuesta lenta a leads (pierde 50% antes de hablar con agente).
- No capacitar al equipo en el stack.

## 11. Reglas operativas para el chat

- **Estable:** funciones, categorías, mejores prácticas.
- **🔴 Volátil:** precios de software, features específicas → web de cada vendor.
- **Sensible:** elección del stack depende de escala, presupuesto, equipo. No hay one-size-fits-all.
- Si el usuario pregunta "¿qué CRM uso?": equipo chico vertical RE → Tokko; equipo escalable multi-vertical → HubSpot.

## Ver también
- `./marketing-digital.md`
- `./embudo-comercial.md`
- `./preventa.md`
- `../01-mercado-argentino/portales-y-canales.md`
- `../15-tecnologia-proptech/` (pendiente)
