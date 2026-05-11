---
title: "Automatización de procesos en Real Estate (RPA, workflows, integraciones)"
topic: "proptech"
subtopic: "automatizacion"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [automatizacion, rpa, zapier, make, n8n, workflows, integracion, api, webhook, no code, low code]
audience: ["developer", "broker", "PM", "chat"]
confidence: "alta"
---

# Automatización de procesos

## TL;DR
- Automatizar = reducir trabajo manual repetitivo + bajar errores + acelerar procesos.
- Stack típico AR: **Zapier / Make (Integromat) / n8n** para integrar CRM, portales, email, WhatsApp, sheets, ERP.
- ROI alto en procesos altos-volumen / baja-complejidad: lead capture, notificaciones, reportes, sincronización stock.

## 1. Qué se puede automatizar

### 1.1 Comercial
- Captura de lead desde formulario web → CRM + notificación a vendedor.
- Sincronización stock entre CRM y portales (ZonaProp, ML, Argenprop).
- Envío automático de brochures + ficha al lead.
- Recordatorios de visitas.
- Drip emails a leads dormidos.
- Tagging de leads por origen y comportamiento.

### 1.2 Operativo
- Generación de boletos / reservas con datos del CRM (mail merge).
- Cargos automáticos en MercadoPago para señas.
- Confirmación de seña + email + slack/WhatsApp al equipo.
- Notas de venta a contabilidad.

### 1.3 Reporting
- Reportes diarios/semanales de KPIs en Slack/email.
- Dashboard auto-actualizado en Looker Studio / Data Studio.
- Alertas de SLA (lead sin contestar > X horas).

### 1.4 Posventa
- Encuesta NPS post-entrega.
- Workflows de gestión de reclamos.
- Recordatorios de mantenimiento.

### 1.5 Construcción
- Notificación de avance + foto al cliente.
- Coordinación de subcontratistas via WhatsApp/Slack.

## 2. Herramientas

### 2.1 No-code automation
- **Zapier**: el más popular global; conectores extensos.
- **Make** (ex Integromat): visual + más flexible que Zapier.
- **n8n**: open source, self-hosted o cloud.
- **Pipedream**: developer-friendly.

### 2.2 Workflow / process management
- **Notion + Notion AI**.
- **Monday.com**, **Asana**, **ClickUp** con automations.
- **Airtable** con automations + scripts.

### 2.3 RPA (Robotic Process Automation)
- **UiPath**, **Automation Anywhere**, **Power Automate** (Microsoft).
- Para automatizar interacción con software legacy sin API.

### 2.4 Integración a medida
- Webhooks + API + scripts (Python, Node).
- Backend custom.
- Más caro pero más control y escalable.

## 3. Arquitectura típica

### 3.1 Capa CRM (centro)
- Tokko, HubSpot, etc.
- Fuente de la verdad para leads y propiedades.

### 3.2 Canales (entrada)
- Web (formularios).
- Portales (XML feed, APIs).
- WhatsApp (BSP API).
- Email (parser + reenvío).
- Llamada (con call tracking).

### 3.3 Canales (salida)
- Email marketing (Mailchimp, ActiveCampaign).
- WhatsApp Business.
- SMS.
- Notificaciones internas (Slack, Teams).

### 3.4 BI / reporting
- Google Sheets / Airtable como datastore.
- Looker Studio / Power BI para dashboards.

### 3.5 Operativo / back-office
- ERP (Tango, Bejerman, SAP, Holistor).
- Facturación electrónica (AFIP API).
- Pagos (MercadoPago, Modo).

## 4. Ejemplos de workflows (Make/Zapier)

### 4.1 Lead capture clásico
```
[Formulario web]
   → CRM (crea contacto)
   → Slack (notifica vendedor)
   → Email automático al lead (gracias + brochure)
   → Agendar follow-up tarea en 24h
```

### 4.2 Seña confirmada
```
[Pago MercadoPago aprobado]
   → CRM (marca propiedad como reservada)
   → Portales (saca publicación)
   → Email al cliente con instrucciones
   → Slack interno (felicita al vendedor)
   → Sheet contabilidad (registra)
```

### 4.3 SLA monitoring
```
[Cron diario]
   → Filtra leads sin contactar >24h
   → Slack alert + email supervisor
   → Re-asignación automática si sigue sin contestar
```

## 5. Integraciones AR específicas

### 5.1 AFIP
- Webservices para facturación electrónica.
- WS-FE, WS-PAD.
- Útil para developers + brokers facturando comisiones.

### 5.2 ARBA / AGIP / ARCA
- APIs limitadas. Verificación manual de partidas en muchos casos.

### 5.3 RPI
- En general no hay API pública. Algunos servicios privados consultan.

### 5.4 Mercado Pago / Modo
- APIs robustas. Integración estándar.

### 5.5 WhatsApp Business
- Via BSP (Twilio, Wati, 360dialog).
- API formal Meta.

## 6. Beneficios cuantificables

### 6.1 Tiempo ahorrado
- Lead-to-contact: de 30min a < 2min.
- Reportes: de horas a segundos.

### 6.2 Errores reducidos
- Copy-paste manual → 0 con sync automática.

### 6.3 Conversión
- Speed-to-lead: 5x mayor conversión si <5 min de respuesta.

### 6.4 Escala
- Equipo igual maneja 3-5x volumen con buen stack.

## 7. Buenas prácticas

### 7.1 Mapeo previo
- Antes de automatizar, **mapear el proceso manual** (BPMN simple).
- Identificar puntos de dolor + alta frecuencia.

### 7.2 Empezar simple
- 1 workflow funcional > 10 sin terminar.
- Iterar.

### 7.3 Logging y monitoreo
- Todo workflow debe loguear ejecución.
- Alertas si falla.

### 7.4 Seguridad
- Permisos mínimos por integración.
- API keys en vault / secret manager.
- Webhook con verificación.

### 7.5 Documentación
- Diagrama del flujo.
- Owner por workflow.
- Procedimiento de troubleshooting.

## 8. Errores comunes

- Automatizar un proceso roto (no lo arregla, lo acelera).
- No documentar → cuando falla nadie sabe arreglarlo.
- Sobrecargar Zapier (mejor migrar a Make/n8n para flujos complejos).
- Olvidar Ley 25.326 al automatizar contacto con leads.
- No tener handoff a humano cuando el cliente lo pide.

## 9. Reglas operativas para el chat

- **Estable:** principios, conceptos, herramientas.
- **🔴 Volátil:** precios de plataformas, features específicas.
- **Sensible:** automatización transversal a todo el negocio. Empezar con pilotos antes de transformar todo.
- Si el usuario pregunta "¿qué automatizo primero?": lead capture + speed-to-lead + reportes básicos.

## Ver también
- `./ia-en-real-estate.md`
- `./datos-y-fuentes.md`
- `../07-comercial/crm-stack-tecnologico.md`
- `../14-costos-presupuesto/control-presupuestario.md`
