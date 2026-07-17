# 📌 Para Agus — pendientes en tu dominio (chat / Capa 2 / voz)

> Esta nota la dejó Mati + Claude. Son cosas del **chat** (tu territorio) que
> nosotros no tocamos para no pisarte. Cuando puedas, dale bola. Si algo no está
> claro, hablalo con Mati.

## 0. 🚀 Cómo ponerte al día (hacé esto primero)

1. **`git fetch` + pull de `main`.** Backend ya está en prod (Railway auto-deploy
   desde main, `/health` = 200). **El FRONTEND de main NO está publicado**: el
   deploy a Netlify lo hacés vos (ver sección 6 — hay cambios nuevos para subir).
2. **3 fixes de TU dominio ya MERGEADOS a main** (decisión de Mati para dejar
   main listo para prod — revisalos post-merge, todo con tests verdes):
   - **SSRF de retrieval**: `follow_redirects=False` + revalida cada hop contra
     la whitelist (`retrieval_service.py`, helper `_get_whitelisted`).
   - **`to_thread` en entregables**: los renders PDF/XLSX de `financial_artifact`
     ya no bloquean el event loop (SSE).
   - **`classify_query`**: 2 misclasificaciones por keywords de intención
     ("cuanto sale/cuesta/vale" → costos; se sacó "como funciona" de
     fundamentos). test_context_router 27/27.
   Si algo no te cierra, revertí ese commit puntual y lo charlamos. La branch
   `fix/agus-retrieval-artifacts` queda como referencia del diff.
3. **Branch `perf/prompt-cache-split-agus`** (sigue pendiente de tu review/merge).
4. **Decisiones que dependen de vos**: WhatsApp/Telegram (sección 5) y config en
   dashboards (sección 4). Después de decidir, publicá el frontend a Netlify.

## 1. 🐛 Bug de render del chat (se ve feo en la respuesta)

En respuestas que usan tools (p.ej. tasación con búsqueda web), el texto sale
mal formado. Ejemplo real:

> …recomendaciones de precio**.Perfecto**, tengo datos frescos. Ahora voy a hacer
> la tasación…**.## Valuación** de tu casa — San Rafael, Mendoza

Dos problemas:
- **Oraciones pegadas** entre iteraciones del loop tool-use: el texto que el
  modelo emite ANTES de un tool_use y el que emite DESPUÉS se concatenan sin
  separador (`precio.Perfecto`). Falta un `\n\n` (o al menos un espacio) al unir
  los tramos de texto de distintas vueltas del loop.
- **Markdown crudo**: el `## Valuación` aparece literal en vez de renderizarse
  como título. Pasa porque el `##` queda pegado al final del tramo anterior sin
  el salto de línea que marked necesita para tratarlo como heading.

**Dónde mirar**: el armado del texto en el loop tool-use del chat —
`services/anthropic_service.py` (stream_chat / cómo se acumulan los tramos de
texto entre iteraciones) y/o cómo el front concatena los `delta`. El fix
probable: insertar `\n\n` entre el texto de una iteración y el de la siguiente
(y garantizar salto antes de un bloque que arranca con `#`, `-`, etc.).

## 2. 🔊 Lectura de voz — que diga el mensaje completo y bien

Relacionado con lo de arriba: cuando se toca "Escuchar", la voz lee el texto del
mensaje. Si el texto viene pegado/mal formado, la lectura también sale rara.
Revisá que la voz **lea el mensaje completo y bien formado** (sin el markdown
crudo ni las oraciones pegadas). Si el fix del punto 1 limpia el texto, esto se
arregla solo; si no, ver el stripping de markdown antes del TTS.

> ⚠️ Mati: confirmá si "que termine de decir la voz" era esto (lectura completa/
> limpia) o algo distinto — lo dejé con mi mejor interpretación.

## 3. Otros pendientes tuyos que veníamos charlando (no urgentes)

- **`perf/prompt-cache-split-agus`** (branch en origin, para review): split del
  system prompt del chat en bloques de cache → baja fuerte el TTFT del 1er
  mensaje de cada conversación. Revisá y mergeá.
- ✅ **SSRF de retrieval** — HECHO en branch `fix/agus-retrieval-artifacts`
  (`follow_redirects=False` + revalida cada hop contra la whitelist). Revisá y mergeá.
- ✅ **`financial_artifact`** — HECHO en la misma branch: los renders PDF/XLSX van
  por `asyncio.to_thread` (ya no congelan los SSE). **Pendiente que dejamos para
  vos**: `document_service._render_pdf/_render_docx` y `_save_local/write_bytes`
  tienen el mismo patrón síncrono — evaluá `to_thread` también ahí.
- **Streaming del chat**: coalescer el render con `requestAnimationFrame` (hoy
  reparsea el markdown en cada token = O(n²), tironea en respuestas largas).

## 4. Config en dashboards (cuando puedas)

- **`OPENAI_API_KEY`** en Railway → sin ella la voz nueva (argentina/cálida) cae
  al TTS del navegador y no se escucha el cambio.
- Confirmar **Railway → App Sleeping = OFF**.

## 5. 📲 WhatsApp / Telegram de SOL — DECISIÓN DE NEGOCIO (leer antes de decidir)

> 👉 **Leé `docs/WHATSAPP_API_COSTOS_Y_PLAN.md` completo.** Ahí está el detalle de
> costos (Cloud API vs WAHA vs Telegram), riesgos y qué implementar. Resumen:

- **Por qué SOL no escribe por WhatsApp hoy**: el canal `whatsapp` en
  `notification_dispatcher.py` es un **stub** (`whatsapp_not_implemented_yet`).
  No es un bug del plan del usuario: literalmente no está codeado el envío.
- **Lo que ya arreglamos nosotros** (nuestro lado, ya en `main`): SOL ya no
  ofrece ni promete WhatsApp/email/push (los sacamos del enum de sus tools) y su
  prompt ahora dice la verdad ("por ahora no puedo escribirte por WhatsApp,
  ofrecé Telegram/app") en vez de inventar que es "por tu plan".
- **Lo más rápido y GRATIS = Telegram**: ya está 100% implementado en código.
  Solo falta setear en Railway `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` y
  `TELEGRAM_WEBHOOK_SECRET` (crear el bot con @BotFather). Con eso "SOL te
  escribe" funciona ya, sin costo.
- **WhatsApp saliente = tiene costo por mensaje** (Cloud API oficial). No es
  gratis y escala con la base de usuarios → **hay que decidir el modelo con Mati
  antes de codear** (pricearlo en Pro o poner tope). El detalle está en el doc.

## 6. 🌐 Frontend en `main` pendiente de PUBLICAR en Netlify

> El backend ya está live (Railway auto-deploy). El **frontend NO** — estos
> cambios están en `main` pero recién los ven los usuarios cuando **vos publiques
> a Netlify** (Netlify Drop / tu flujo). Publicá `frontend/` cuando estés listo:

- **`app.html`** — varias cosas nuevas: tool `connect_telegram` de SOL (chip +
  botón "Abrir Telegram"), `parseSolMd` bloquea `<img>` (anti-exfil), `project_id`
  en el ingest de pagos, **selector de dólar Blue/Oficial en la calculadora
  hipotecaria** (antes cotización fija 1460), y SRI (`integrity`) en el `<script>`
  de pdf.js.
- **`sentry.js`** — SRI (`integrity`) en el bundle de Sentry.
- **Rail de acceso rápido + auto-scroll inteligente** (app.html + app.css): al
  colapsar el sidebar queda una columna de iconos para navegar (desktop); y el
  chat/SOL ahora dejan de auto-bajar cuando el usuario scrollea arriba durante el
  streaming (patrón ChatGPT), re-enganchando al volver al fondo. Heads-up: tu
  `vcRTMirror` (voz en vivo) ahora usa `scrollBottom(true)` — fix de integración
  para que el espejo de la sesión de voz siga bajando siempre (tu flujo no pasa
  por sendMessage y no resetea el flag nuevo).
- Todo verificado local (JS OK, probado en browser). Al publicar, chequeá que la
  sección Créditos traiga la cotización (necesita el endpoint nuevo
  `GET /api/creditos/dolar`, que ya está en el backend live).

## 7. ⚙️ Config nueva a setear en Railway (backend, dashboards)

Hay validators de arranque nuevos: en producción (`DEBUG=false`) el backend
**NO arranca** si falta algo crítico (fail-fast en el deploy). Confirmá que en
Railway estén seteadas: `JWT_SECRET` (fuerte, ≥32 chars), `FRONTEND_URL`, y al
menos una de `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`. (Si el deploy actual está en
200, ya están bien.) Opcionales que suman: `TELEGRAM_BOT_TOKEN` (SOL por Telegram,
gratis), `SENTRY_DSN` (monitoreo de errores JS — hoy vacío).
