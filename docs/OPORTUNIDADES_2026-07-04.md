# Oportunidades de mejora — 2026-07-04

> Salidas de una exploración multi-agente en 4 frentes (producto/monetización,
> performance, operación/confianza, experiencia/diferencial). NO son bugs (eso
> se barrió y arregló el 07-03): son palancas para retener y vender a USD 70/mes.
> Cada una está anclada en código real (file:line en el detalle de la auditoría).

## TIER 1 — Máximo impacto, ya casi construido (solo falta conectar)

1. **SOL por Telegram de verdad** (1-2 días) — El webhook + pairing + el agente
   con 25+ tools YA existen; hoy un mensaje libre al bot recibe un eco fijo
   ("entrá a la app web"). Conectar `handle_webhook_update` → `run_agent` convierte
   el bot en "cargale un pago a SOL desde la obra por Telegram" — diferencial
   enorme para el usuario de campo. (telegram_service.py:216 dice "Fase 2").
2. **Promesa rota de automatizaciones** (2-3 días) — SOL ofrece y GUARDA
   `automation_prefs` (resumen diario, alertas de desvío) pero ningún código las
   lee jamás. El scheduler existe; falta el job que las ejecute.
3. **Emails de ciclo de vida** (1-2 días) — Resend ya está implementado y probado
   (reset de password). Falta: welcome, "tu trial vence mañana" (LA palanca de
   conversión con trial de 7 días y corte seco), recibo de pago. El canal email
   del dispatcher es un stub declarado.
4. **Reporte semanal de obra automático** (1-2 días) — `generate_report()` (PDF),
   `send_document` por Telegram y el scheduler ya existen por separado. Un job
   lunes 8am con avance + desvíos CPI/SPI = retención pura.
5. **Encender Sentry + UptimeRobot** (2-3 hs, mayormente Agus) — todo el wiring
   está; falta DSN en Railway/config.js y 2 monitores. Hoy los errores de prod se
   detectan "cuando un cliente se queja".

## TIER 2 — Alto impacto, esfuerzo corto

6. **Auditoría del webhook MP** (1 día) — Stripe tiene tabla de eventos; MP (el
   que va a cobrar de verdad) solo loguea a stdout. Persistir eventos + alerta en
   fallos = no perder nunca un pago acreditado sin acceso otorgado.
7. **generate_report ciego al multi-proyecto** (medio día) — con 2+ proyectos el
   reporte revienta (`scalar_one_or_none` sobre N proyectos) y mezcla pagos de
   todos. Deuda del multi-proyecto recién lanzado. ← *el más urgente del tier*
8. **Backup automatizado + prueba de restore** (1 día) — el plan está escrito
   (BACKUPS.md), nada corre. GitHub Action con pg_dump cifrado; no depende de Agus.
9. **Páginas legales** (1-2 días) — no existen Términos, Privacidad ni botón de
   arrepentimiento (Res. 424/2020, obligatorio en AR). Exposición legal directa
   cobrando $69.900/mes.
10. **PDFs con la marca del profesional** (1.5 días) — todos los entregables dicen
    "— RE Expert" hardcodeado. Logo + nombre de estudio del usuario transforma el
    PDF en un entregable por el que él cobra honorarios.
11. **Link compartible read-only del proyecto** (2-4 días) — todo es single-user;
    un `share_token` + vista pública del panel le deja mostrar el avance al
    inversor/cliente. La feature de retención B2B más barata.
12. **Optimizar imágenes de la landing** (1-2 hs) — 886 KB de JPG sin lazy-load
    en la página que vende; el hero solo pesa 427 KB. WebP + lazy = -70% de LCP.
13. **GZip en el backend + cache de catálogos** (2-4 hs) — FastAPI no comprime
    nada (84 KB de JSON de Academia por visita → serían ~13 KB) y `no-store`
    global impide cachear catálogos estáticos.
14. **N+1 en el sidebar de chats** (medio día) — 22 queries por carga (una por
    conversación para el preview) en el endpoint más caliente de la app.

## TIER 3 — Valioso, para planificar

15. **Proyecto demo de un click** (2-3 días) — el panel/pagos/scanner arrancan
    vacíos; el momento aha es invisible en el trial. "Cargar proyecto de ejemplo".
16. **Calculadora pública de oportunidad** (1-2 días) — `compute_deterministic` es
    código puro sin costo por request: lead magnet perfecto en la landing.
17. **Plan anual con descuento** (0.5-1 día + decisión de precio) — adelanta cash
    flow y anula churn 12 meses; MP soporta un segundo preapproval plan.
18. **Import de MercadoLibre en el scanner** (1 día) — la API pública de MLA
    esquiva el 403 de Zonaprop y salva el momento wow de "pegá el link".
19. **Noticias Destacadas/Opinión congeladas (04-04)** (1-3 días) — auto-ocultar
    si viejo, o generarlas con el pipeline IA que ya existe.
20. **`/api/bootstrap`** (1 día) — colapsar los 5-6 round-trips seriales del
    arranque (~1s de spinner diario desde AR a us-west).
21. **PWA instalable** (4-8 hs) — manifest + SW de shell; el usuario está en obra
    con el teléfono.
22. **Foto de comprobante en cada pago** (1-2 días) — input capture + storage ya
    resuelto; la evidencia papel hoy muere en el rollo de fotos.
23. **Cache del feed "Últimas"** (2-3 hs) — hoy baja TODOS los .md del bucket en
    cada request (31 llamadas HTTP); el patrón TTL ya existe en news_live.
24. **smoke_prod automatizado + monitorear /health/db** (3-4 hs) — la herramienta
    existe, nadie la corre; /health devuelve 200 con la DB caída.
25. **Accesibilidad mínima** (1 día) — cero :focus-visible, modales sin
    role=dialog ni Escape.
26. **Persistir digests/traducciones IA** (3-5 hs) — cada deploy tira el cache en
    memoria y re-paga los mismos LLM calls.
27. **Sacar marked/DOMPurify del critical path** (1-2 hs) — 2 scripts síncronos de
    jsdelivr bloquean el head; si el CDN falla, app en blanco.
28. **Partir el JS de app.html en módulos** (2-3 días) — 284 KB inline sin cache
    del browser; con archivos hasheados el 90% queda cacheado.

## Ya pendientes de ANTES (no repetidos acá)
CSV de materiales congelado + admin de carga · "sin tarjeta" vs tarjeta-upfront ·
sandbox MP · fulfillment de cursos · rotación de secrets · reskin pricing/account ·
confirm() nativos → ver `PENDIENTES_NEGOCIO_2026-07-03.md` y `NOTA_AGUS_SEGURIDAD_2026-07-01.md`.

> Detalle completo con evidencia file:line: output de la auditoría del 07-04
> (workflow `oportunidades-mejora`).
