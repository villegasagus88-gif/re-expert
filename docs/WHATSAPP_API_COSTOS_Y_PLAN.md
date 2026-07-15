# WhatsApp para SOL — costos, opciones y qué implementar

> Decisión de negocio + técnica para Agus. Contexto: SOL hoy NO puede escribirle
> al usuario por WhatsApp (el canal es un stub). Esto explica por qué, cuánto
> cuesta cada camino, y qué habría que implementar. **Antes de codear, decidir el
> modelo con Mati** — hay un costo por mensaje que impacta el pricing.

## Estado actual (verificado en código)

- `services/notification_dispatcher.py` → `dispatch()`: el canal `whatsapp`
  devuelve `{"ok": False, "detail": "whatsapp_not_implemented_yet"}` (stub). Ídem
  `email` y `push`. Solo `in_app` y `telegram` están implementados de verdad.
- Ya arreglamos (nuestro lado): las tools `send_message_now` y `schedule_reminder`
  ya NO ofrecen whatsapp/email/push en su enum, y el prompt de SOL dice la verdad
  ("por ahora no puedo escribirte por WhatsApp") en vez de inventar "tu plan".
- `wa.me` (SOL → un CONTACTO del usuario) **sí funciona** y es gratis: es un link
  que el usuario toca y manda desde SU teléfono. Eso NO es "WhatsApp API".

## Los dos usos (piden cosas distintas)

1. **SOL le escribe al USUARIO** (recordatorios/avisos). Necesita un número
   central de RE Expert + una API. **Acá está el costo.**
2. **SOL le escribe a un CONTACTO del usuario** (mandar a un cliente). Sale del
   número del propio usuario vía `wa.me` (link, un tap). **Gratis, ya está.**

Este doc es sobre el uso 1 (el que hoy no anda).

## Opciones para el uso 1, con costos

### A) WhatsApp Cloud API (oficial de Meta) — RECOMENDADA para producción
- **Cómo**: cuenta de Meta Business + un número dedicado a la API (ese número
  deja de servir como WhatsApp normal). El usuario final no baja nada.
- **Costo**: modelo por MENSAJE (desde julio 2025). Los mensajes que INICIA el
  negocio (avisos proactivos, "vencé un pago") son plantillas de categoría
  *utility/marketing* y se pagan por unidad; la tarifa varía por país (Argentina
  tiene la suya). Los mensajes dentro de una ventana de 24h abierta por el
  usuario (el usuario escribió primero) suelen ser gratis o mucho más baratos.
  → **Verificar la tarifa vigente para AR antes de decidir** (cambia seguido).
- **Tier gratis**: ~1.000 conversaciones/mes para arrancar sin pagar.
- **Pro**: estable, sin ban, oficial. **Contra**: trámite de alta + costo que
  escala con el uso → hay que pricearlo en el plan Pro o poner un tope mensual.

### B) WAHA / Evolution API (self-hosted) — solo para MVP/validar
- **Cómo**: Docker con un número vinculado por QR (como WhatsApp Web). Gratis.
- **Contra CRÍTICO**: es NO oficial (automatiza WhatsApp Web) → **riesgo de ban
  del número** por parte de Meta, sobre todo con volumen o algo que parezca spam.
  Además la sesión se cae y hay que re-escanear. **No apto para producción
  premium** (si banean el número, muere el canal).
- Sirve para: prototipar rápido y gratis, sabiendo que es puente, no destino.

### C) Twilio / BSP (proveedor tercero) — atajo pago
- API oficial "envuelta" por un tercero (Twilio, 360dialog, etc.). Más fácil de
  integrar que Cloud API directa, pero suma el markup del proveedor arriba del
  costo por mensaje de Meta.

## Alternativa que ya tenés GRATIS: Telegram

Para "SOL le avisa al usuario", **Telegram ya está 100% implementado en código**
(dispatch + pairing + deep link + webhook) y es **gratis e ilimitado**. Lo único
que falta para que ande en prod: setear en Railway `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_BOT_USERNAME` y `TELEGRAM_WEBHOOK_SECRET` (crear el bot con @BotFather).
→ **La forma más barata y rápida de dar "SOL te escribe" es prender Telegram, no
implementar WhatsApp.**

## Qué implementar si se elige WhatsApp (uso 1)

1. Elegir proveedor (A recomendado para prod; B solo MVP).
2. En `notification_dispatcher.py::dispatch`, reemplazar el stub del canal
   `whatsapp` por la llamada real al proveedor (mismo patrón que el bloque
   `telegram`: buscar el `UserChannel` verificado, mandar, devolver `{ok,...}`).
3. Env vars nuevas (token/API key del proveedor, número, plantillas aprobadas si
   es Cloud API). Documentarlas en `.env.example`.
4. Flujo de opt-in del usuario (WhatsApp exige consentimiento) + pairing del
   número, análogo al de Telegram (`UserChannel` channel='whatsapp').
5. Volver a habilitar `whatsapp` en los enums de `send_message_now` y
   `schedule_reminder` (hoy los sacamos para que SOL no fallara).
6. Tope de mensajes/mes o gate por plan, para que el costo por mensaje no se
   dispare con la base de usuarios.

## Recomendación (para charlar con Mati)

- **Ahora**: prender **Telegram** (gratis, ya codeado) para cubrir "SOL te
  escribe". Cero costo, cero riesgo.
- **WhatsApp**: dejarlo como **feature premium** más adelante, con **Cloud API
  oficial** y el costo por mensaje priceado en el plan Pro (o con tope). WAHA
  solo si se quiere validar la demanda rápido, sabiendo el riesgo de ban.
- **Nunca** poner WhatsApp saliente como default gratis para toda la base:
  el costo por mensaje × millones de usuarios lo absorbe la empresa.
