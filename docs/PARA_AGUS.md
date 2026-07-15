# 📌 Para Agus — pendientes en tu dominio (chat / Capa 2 / voz)

> Esta nota la dejó Mati + Claude. Son cosas del **chat** (tu territorio) que
> nosotros no tocamos para no pisarte. Cuando puedas, dale bola. Si algo no está
> claro, hablalo con Mati.

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
- **SSRF de retrieval**: fix pendiente de subir a origin (ver con Mati/Claude).
- **`document_service` / `financial_artifact`**: envolver el render de PDF/DOCX/
  XLSX en `await asyncio.to_thread(...)` → hoy corre síncrono y **congela todos
  los streams SSE** mientras genera un entregable.
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
