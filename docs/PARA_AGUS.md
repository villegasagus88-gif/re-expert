# 📌 Para Agus — estado y pendientes

> **Estado al 31-jul-2026**, verificado contra el código y contra producción
> (no contra lo que decía la versión anterior de esta nota).
> La dejamos Mati + Claude. Si algo no te cierra, hablalo con Mati.

**Si leíste la versión anterior, dos cosas cambiaron y ya no tenés que hacer nada
por ellas**: el deploy de Railway se destrabó y el frontend ya está publicado.
El detalle está en la sección 8. Todo lo demás de esta nota sí sigue abierto.

---

## 0. Dónde estamos parados (30 segundos)

| | Estado |
|---|---|
| `origin/main` | `32553c7` |
| Railway (backend) | ✅ sirviendo `32553c7` — al día con main |
| Netlify (frontend) | ✅ sirviendo `32553c7` — al día con main |
| Migraciones | 0036, 0037 y 0038 aplicadas en prod |

Hacé `git pull` de `main` y listo. Backend **y** frontend están live y al día.

> **Pregunta para vos, corta pero importante**: el `app.css` publicado es
> byte-idéntico al commit. El `app.html` difiere en **una sola línea**
> (`pricing.html` reescrito a `/pricing`), y esa variante no existe en ningún
> commit del repo → es el post-procesado de **Pretty URLs** de Netlify, no un
> cambio de contenido. La evidencia fuerte es otra: el header CSP en vivo ya trae
> los hosts de Mercado Pago que agregamos en `netlify.toml` en `32553c7`, así que
> el `netlify.toml` de la **raíz** se está aplicando. Eso apunta a que Netlify
> buildea **desde git**, no por Drop (ya actualizamos `CLAUDE.md`, que decía lo
> contrario).
>
> Confirmanos cuál de las dos es. Se ve acá: **Netlify → proyecto `re-expert` → Site configuration → Build &
> deploy → Continuous deployment**. Si el repo aparece linkeado, buildea desde
> git; si no aparece, sigue siendo Drop.
>
> Importa por algo concreto: **si alguna vez publicás arrastrando sólo la carpeta
> `frontend/`, el `netlify.toml` de la raíz no viaja** y te quedás sin ninguna
> cabecera de seguridad (el CSP completo, X-Frame-Options, Referrer-Policy y
> Permissions-Policy salen sólo de ese archivo: no hay `_headers`, y el único
> `<meta>` de CSP en las páginas es `upgrade-insecure-requests`, que no restringe
> nada) y sin los rewrites de `/api/*`, `/static/*` y `/health`. El sitio sigue
> andando, pero desprotegido. **Si publicás a mano, arrastrá la RAÍZ del repo, no
> `frontend/`.**

---

## 1. 🔑 Config en Railway — es lo que bloquea features enteras

> ⚠️ **Antes de arrancar, una cuestión de orden.** Prender Mercado Pago es lo que
> más desbloquea, pero **no lo prendas antes** de que estén: (a) los documentos
> legales publicados y linkeados, (b) el checkbox de aceptación en el registro y
> (c) el Botón de Arrepentimiento en la home. Hoy faltan los tres (sección 2).
> Sin cobros eso es un incumplimiento formal; **con cobros es un incumplimiento
> con consumidores que pagaron**, que es otra categoría. (a), (b) y (c) son
> código nuestro: pedínoslos y salen rápido. Sumale que la cancelación todavía
> corta el acceso en el acto aunque el período esté pagado (R16 en
> `legal/RIESGOS-TECNICOS.md`) — también conviene resolverlo antes del primer
> cobro real.

### 1.1 Mercado Pago — hoy la sección Facturación está apagada

Verificado en prod: `GET /api/billing/mp/config` → `{"enabled":false,"public_key":""}`.
Sin esto, **nadie puede pagar**: no hay cobro, ni tarjetas guardadas, ni suscripción.

**Ojo: estos 4 valores todavía no existen, hay que generarlos.** No es "copiar y
pegar de algún lado". En https://www.mercadopago.com.ar/developers → tu aplicación:

1. **Credenciales de producción** → Access Token + Public Key.
2. **Crear el plan de suscripción** (`preapproval_plan`, $69.900/mes ARS, trial de
   7 días) → eso te devuelve el `plan_id`.
3. **Registrar el webhook** `https://re-expert-production.up.railway.app/api/billing/mp/webhook`
   con los topics `payment` y `subscription_preapproval` → eso te da la clave de firma.

> El paso a paso completo está en **`docs/ACTIVAR_PAGOS.md`** — esa es tu guía,
> usala. Se puede hacer todo primero con credenciales de TEST.

| Variable | Qué pasa sin ella |
|---|---|
| `MP_ACCESS_TOKEN` | `mp_enabled()` = false. Todo el módulo es inerte. |
| `MP_PLAN_ID` | Idem: `mp_enabled()` chequea las dos juntas. |
| `MP_WEBHOOK_SECRET` | **Fail-closed en prod**: el webhook rechaza todo con 503, así que MP no puede avisarnos de ningún cobro. |
| `MP_PUBLIC_KEY` | ⚠️ **Ya NO es opcional.** El formulario de tarjeta tokeniza en el navegador con el SDK de MP y necesita la public key. Sin ella la sección abre pero al agregar una tarjeta dice "los pagos todavía no están habilitados". |

> Ese último punto es una trampa nueva: `docs/ACTIVAR_PAGOS.md:40` decía
> "Opcional (no se usa en el flujo redirect)" y el comentario de `settings.py:59`
> decía "opcional". Era cierto para el checkout viejo por redirect y dejó de
> serlo cuando entraron las tarjetas guardadas. Los dos van corregidos en el
> mismo commit que esta nota.

### 1.2 `RESEND_API_KEY` — pasó a ser obligación contractual

Antes la usaba sólo "recuperar contraseña". Hoy la consumen seis flujos, y **dos
de ellos son promesas escritas en los Términos**:

- **Aviso previo a cada cobro**, 3 días antes y con el importe
  (`scheduler_service.py` → `_avisar_proximos_cobros`). La constante
  `DIAS_AVISO_COBRO = 3` está atada a la **cláusula 5.1.1**: si no sale el mail,
  incumplimos algo firmado, no perdemos una comodidad.
- **Aviso de cobro rechazado** (`billing_issues.py`), que es lo que le da sentido
  a los 5 días de gracia: sin mail, el usuario se entera cuando ya perdió acceso.
- Cambio de email verificado, alta del 2FA por email, y recuperar contraseña.
- **2FA por email en el LOGIN.** Hoy nadie puede tener ese método activo (para
  activarlo hay que recibir un código por mail y el backend corta con 503 si no
  sale), así que **no hay cuentas trabadas**. El riesgo aparece después: una vez
  seteada la key y con gente enrolada, si la rotás, la borrás o el dominio pierde
  la verificación en Resend, esos usuarios no pueden entrar y sólo les queda un
  código de recuperación. **Regla: una vez que la prendés, esa key y ese dominio
  no se tocan sin avisar.**

**Son DOS pasos, no uno** — setear la key sola no manda ni un mail:

1. **Verificar el dominio** en https://resend.com/domains. Resend te da registros
   DNS (SPF, DKIM, return-path) que hay que cargar donde tengas el dominio. Hasta
   que no diga *Verified*, todo envío vuelve con 403 y no sale nada.
2. Recién ahí, crear la API key en https://resend.com/api-keys y cargarla en
   Railway como `RESEND_API_KEY`.

> El remitente está fijo en `RESEND_FROM = "RE Expert <hola@re-expert.app>"`
> (`config/settings.py:182`). **Si el dominio final no va a ser `re-expert.app`,
> avisanos**: hay que cambiar esa env var también. Y ojo que esto se cruza con
> "Dominio y casilla de contacto" de la sección 2 — si el dominio todavía no es
> nuestro, este paso no se puede hacer.
>
> No pudimos verificar desde afuera si la key ya está cargada (ningún endpoint la
> expone; `/api/auth/forgot-password` responde igual en los dos casos, por
> anti-enumeración). Chequealo en Railway → Variables y avisanos.

El día que enciendas Mercado Pago, esta key tiene que estar sí o sí.

### 1.3 Telegram — gratis, y son 4 pasos, no 3

Lo dijimos como "sólo faltan 3 env vars" y faltaba un cuarto paso:

1. `TELEGRAM_BOT_TOKEN` — habilita el envío saliente.
2. `TELEGRAM_BOT_USERNAME` — sin él no se puede vincular a nadie
   (`/api/channels/telegram/connect` → 503).
3. `TELEGRAM_WEBHOOK_SECRET` — **obligatoria en prod, fail-closed**: sin ella el
   webhook entero devuelve 503.
4. **Registrar el webhook a mano contra la API de Telegram.** No lo hace ningún
   código nuestro (`TELEGRAM_WEBHOOK_BASE_URL` está declarada y sin usar):

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" -d "url=https://re-expert-production.up.railway.app/api/channels/telegram/webhook" -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

Con eso queda andando **SOL → vos** (avisos salientes + vinculación). El chat
**bidireccional** por Telegram sigue apagado hasta prender `TELEGRAM_AGENT_ENABLED=true`.

### 1.4 `OPENAI_API_KEY` — apaga más cosas de las que decíamos

No es sólo el timbre de la voz:

- El TTS cae a la voz del navegador (esto ya lo sabías).
- **El dictado por Whisper** (`/api/voice/transcribe`) queda en 503 y cae a
  `SpeechRecognition`, que sólo existe en Chrome y Edge: **en Firefox y Safari no
  hay dictado**.

### 1.5 `SENTRY_DSN` — ojo, no es lo que dice la nota vieja

Son **dos Sentry distintos** y la nota los mezclaba:

- `SENTRY_DSN` en Railway = errores del **backend** (Python/FastAPI).
- Los errores **JS** salen de `frontend/config.js` (hoy `''`, verificado en prod):
  se activan editando el archivo y republicando, **no desde ningún dashboard**.

Dato tranquilizador: el SDK de Sentry adjunta por default las variables locales
de cada frame — una excepción dentro de `login_user(email, password)` le habría
mandado una contraseña en claro a un tercero. Ya está cerrado con
`include_local_variables=False` (`main.py:72`). Ahora sí se puede activar sin ese
riesgo. Si lo activás, sumá el host de Sentry a `connect-src` en `netlify.toml`.

### 1.6 App Sleeping = OFF — ya está, por código

No hay nada que setear: `backend/railway.json` declara `"sleepApplication": false`
(el mismo bloque de donde sale el `preDeployCommand: alembic upgrade head` que
corre las migraciones en cada deploy).

Lo dejamos acá sólo para que sepas por qué importa: el scheduler corre **en
background dentro del mismo proceso** (avisos de cobro, recordatorios, digest
diario, purga de cuentas). Si alguna vez alguien fuerza el sleep desde la UI de
Railway, esos jobs dejan de correr **sin ningún error visible**.

### 1.7 `ADMIN_EMAILS` — probablemente vos no seas admin

El allowlist de fundadores hardcodeado (`core/auth.py:115`) tiene **sólo el mail
de Mati**. Todo lo demás sale de `ADMIN_EMAILS` (lista separada por comas, env de
Railway). Si tu mail no está ahí:

- no ves la **bandeja de reportes de error** (la feature nueva de "Informar un
  error"), y
- el gate de plan te trata como usuario común (`core/plan_gate.py`), o sea que
  vas a chocar contra el paywall como cualquiera.

Sumate a `ADMIN_EMAILS` cuando entres al dashboard.

### ⚠️ 1.8 No rotes `JWT_SECRET` sin leer esto

`JWT_SECRET` dejó de ser sólo la firma de los tokens. Si `CONFIRM_SIGNING_SECRET`
no está definida, es además el secreto maestro de:

- **el cifrado en reposo del secreto TOTP del 2FA** (`core/secret_box.py`), y
- **la firma de los links de entregables** (`core/signed_files.py`).

O sea: **si la rotás, los usuarios con 2FA por app quedan afuera** (su secreto no
se puede descifrar) y todos los links de informes ya emitidos se invalidan. Si
alguna vez hace falta rotarla, seteá primero `CONFIRM_SIGNING_SECRET` con el
valor actual de `JWT_SECRET` para desacoplarlas, y recién después rotá.

### Lo que hace fallar el arranque (fail-fast en el deploy)

En producción (`DEBUG=false`) el backend **no arranca** si falta: `DATABASE_URL`,
`JWT_SECRET` (≥32 chars, ≥8 caracteres distintos, y que no sea un placeholder
conocido), `FRONTEND_URL`, y al menos una de `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`.
Si el deploy actual está en 200, esas ya están bien.

---

## 2. ⚖️ Legal — lo que no se destraba con código

Se escribió un paquete legal completo en `legal/` (términos, privacidad, cookies)
fundado en una auditoría del código real, más `legal/RIESGOS-TECNICOS.md` con 24
riesgos (8 ya corregidos en código: R3, R5, R7, R8, R9, R11, R15, R19). Lo que
queda abierto de acá **es decisión o trámite tuyo/de Mati**, y conviene mirarlo
antes de seguir sumando features:

- **🔴 Botón de Arrepentimiento — obligación incumplida HOY.** La Resolución
  424/2020 lo exige visible en la home y que inicie la revocación sin ningún otro
  trámite. `grep -rni 'arrepentimiento' frontend/` da cero. Es sancionable por sí
  solo.
- **Los documentos no están publicados.**
  `https://re-expert.netlify.app/legal/politica-de-privacidad.md` da 404 y en la
  app las secciones legales siguen diciendo "Próximamente". Falta cablearlos +
  checkbox de aceptación en el registro.
- **Dominio y casilla de contacto.** Los tres documentos apuntan a
  `contacto@re-expert.app` (**17 menciones**: 7 en Términos, 9 en Privacidad, 1
  en Cookies). Necesitamos que confirmes que el dominio es nuestro y que esa
  casilla recibe y se lee: si rebota, el Botón de Arrepentimiento y los pedidos
  de datos quedan vacíos de contenido. Es además el mismo dominio del que depende
  Resend (sección 1.2).
- **DPAs de los proveedores** (Anthropic, Supabase, Railway): trámite de
  adhesión, va desde tus cuentas.
- **Backups — hay un `[CONFIRMAR CON TITULAR]` esperándote.** En el plan Free de
  Supabase no hay backups automáticos y no hay ningún cron ni script de dump. La
  sección de seguridad de la Política **no los promete** (hay una nota expresa de
  no afirmarlos hasta probar un restore), **pero el cuadro 8.4 sí los lista** como
  excepción a la baja, con el plazo sin resolver
  (`legal/politica-de-privacidad.md:433`). Ese placeholder hay que cerrarlo antes
  de publicar: o subimos el plan y probamos un restore, o sacamos la fila.
- **Procedimiento de reembolso**: no existe definido. Decisión de negocio.

---

## 3. 📲 WhatsApp / Telegram de SOL — decisión de negocio

> 👉 Leé `docs/WHATSAPP_API_COSTOS_Y_PLAN.md` completo. Resumen:

- **Por qué SOL no escribe por WhatsApp**: el canal `whatsapp` en
  `notification_dispatcher.py` sigue siendo un stub (`whatsapp_not_implemented_yet`),
  igual que `email` y `push`. No es un bug del plan del usuario: no está codeado.
- **Nuestro lado ya está**: SOL no ofrece ni promete WhatsApp/email/push (los
  sacamos del enum de sus tools) y su prompt dice la verdad ("por ahora no puedo
  escribirte por WhatsApp, te ofrezco Telegram") en vez de inventar que es "por
  tu plan".
- **Lo rápido y gratis = Telegram**: ver sección 1.3.
- **WhatsApp saliente tiene costo por mensaje** (Cloud API oficial) y escala con
  la base de usuarios → **hay que decidir el modelo con Mati antes de codear**
  (pricearlo en Pro o poner tope). El detalle está en el doc.

---

## 4. 🐛 Bugs abiertos en tu dominio

### 4.1 Render del chat — SIGUE VIVO, nadie lo tocó

Síntoma real:

> …recomendaciones de precio**.Perfecto**, tengo datos frescos… **.## Valuación**
> de tu casa — San Rafael, Mendoza

**Causa confirmada**: en `services/anthropic_service.py:818-831`, el loop
`for _ in range(MAX_TOOL_ITERATIONS)` reabre el stream en cada vuelta y hace
`yield {"type":"delta","text":text}` **sin intercalar ningún separador de texto**
entre una vuelta y la siguiente. (Sí emite `tool_use` y `tool_result` en el
medio — de hecho SOL se apoya en esos eventos para mitigarlo, ver más abajo —
pero ningún `\n\n` en el flujo de texto.) El texto de antes y el de después del
`tool_use` se pegan.

Tres precisiones que la nota vieja no tenía:

1. **Un espacio NO alcanza.** Lo probamos con el `marked` vendorizado del repo:
   `'precio. ## Valuación'` sigue renderizando literal. Con `\n` ya toma el
   heading; `\n\n` es lo seguro. El markdown crudo es consecuencia directa de
   esto, no hay un segundo bug en el front.
2. **El síntoma es del Chat Experto, no de SOL.** SOL ya lo mitiga en el front:
   cierra el bubble antes del primer `tool_use` y abre uno nuevo para el texto
   posterior (`app.html:8690-8700` y `:8726-8731`). El Chat Experto mete todos
   los tramos en el mismo bubble (`app.html:3877-3880`).
3. **Conviene arreglarlo en el backend.** El texto pegado también se **persiste**
   (`full_response` en `api/routes/chat.py:611` es lo que se guarda como mensaje
   del asistente), así que un fix sólo en el front deja el historial igual de
   roto. Un fix en el loop cubre Chat Experto + historial de una.

### 4.2 Lectura de voz — estaba MAL DIAGNOSTICADO

> ⚠️ **Leé esto antes de tocar nada, porque cambia a qué código ir.** El bug que
> describimos abajo vive en la ruta de voz **premium** (`vcSpeakApi`), y esa ruta
> sólo se activa con `OPENAI_API_KEY` — que según la sección 1.4 hoy **no está
> seteada**. Con la voz del navegador corre `vcSpeak` (`app.html:3966`), cuyo
> regex tiene el `[.!?]` **opcional** y por lo tanto no descarta líneas.
> Entonces: si lo que escuchaste fue con la voz del navegador, el bug es OTRO y
> necesitamos el mensaje exacto; si fue con la premium (o sea, la key ya está en
> Railway y 1.4 quedó vieja), el de abajo es el tuyo y está confirmado.

La nota vieja decía "si el fix del punto 1 limpia el texto, esto se arregla solo;
si no, ver el stripping de markdown antes del TTS". **Las dos cosas son falsas**:

- El stripping de markdown **ya existía** cuando se escribió esa nota
  (`vcStripMd` entró el 09-jul, la nota es del 14-jul). No hay nada que agregar
  ahí.
- El pegado tampoco se escucha: `vcSpeak` parte por oraciones, así que
  `precio.Perfecto` sale como "precio." + "Perfecto".

**El bug real, reproducible**, está en `vcTtsChunks` (`app.html:4012`): el regex
`/[^.!?\n]+[.!?]+["»)]?|[^.!?\n]+$/g` **no tiene la flag `m`**, así que la
segunda alternativa sólo matchea al final del string. Resultado: toda línea sin
puntuación final se **descarta y nunca se sintetiza**. Verificado en node:

```
'Titulo\nCuerpo con punto.'.match(regex)  →  ["Cuerpo con punto."]
```

El "Titulo" se pierde. Ahí está el "no lee el mensaje completo".

> Un dato más, por si es lo que te molestaba: con la voz premium
> (`OPENAI_API_KEY`), lo que se lee **no es el mensaje** sino un guion reescrito
> por Claude (`/api/voice/speak-script`, `max_tokens=900`). O sea que por diseño
> condensa. Si lo que querías era que lea el mensaje textual, eso es un cambio de
> producto, no un bug.

---

## 5. 🔧 Pendientes técnicos tuyos

- **`perf/prompt-cache-split-agus`** — aclaración por el nombre: es una
  optimización **nuestra** (commit `41891da`, 13-jul, de Mati) que quedó en branch
  esperando **tu review**, no código tuyo a medias. Sigue sin mergear. Buena
  noticia: **mergea limpio** — lo verificamos con `merge-tree` (cero conflictos) y
  ningún commit de `main` tocó `anthropic_service.py` desde entonces. No se
  pudrió: revisala y, si te cierra, mergeala.
- **`document_service`** — siguen 100% síncronos y llamados sin wrapper desde la
  corrutina `async def generate_report`: `_render_pdf` (`:111`, reportlab),
  `_render_docx` (`:252`, python-docx) y `_save_local` (`:377`, `write_bytes`).
  Mismo patrón que ya arreglamos en `financial_artifact`. Evaluá `to_thread`.
  (Detalle fino: en `financial_artifact` el `to_thread` cubre **sólo el render**;
  `_store` sigue llamando a `_save_local` sincrónico.)
- **Streaming del chat** — sigue reparseando todo el acumulado en cada delta:
  `app.html:3878` hace `full+=ev.text; updateStreaming(full)` y `updateStreaming`
  corre `marked.parse` + `DOMPurify.sanitize` sobre el texto completo. Es O(n²) y
  tironea en respuestas largas. Coalescer con `requestAnimationFrame`.

> Los dos que la nota vieja marcaba "✅ HECHO en branch, revisá y mergeá" —**SSRF
> de retrieval** y **`to_thread` en entregables**— ya no están en branch: entraron
> a `main` en `5e45407` y están en producción. La branch
> `fix/agus-retrieval-artifacts` es ancestro de `main`, sirve sólo como referencia
> del diff. Igual que el fix de `classify_query` (`test_context_router`: 27/27,
> corrido hoy).

---

## 6. 🤝 Cosas que entraron a `main` y te tocan el dominio

Te avisamos porque son archivos tuyos o suposiciones tuyas:

- **`chat.py` — la memoria de SOL ahora tiene un filtro server-side.**
  `_persist_memory_item()` guardaba con `source="auto-silent"` sin confirmación, y
  la única barrera contra guardar un CBU o una tarjeta era una frase del prompt.
  Ahora `core/pii_guard.py` corre **antes del INSERT** (`chat.py:249-265`) y
  bloquea CBU/CVU, alias bancario, tarjetas validadas con Luhn, CVV y
  contraseñas; devuelve `{"error": ..., "saved": false}`. **Qué mirar**: que SOL
  maneje bien ese `saved:false` y no insista ni diga que guardó. Probado con 7
  casos que debe bloquear y 10 que no (montos, superficies, expedientes, CUIT,
  coordenadas, teléfonos), cero falsos positivos. Si ves algo legítimo que se
  cae, avisá y ajustamos el regex — no lo saques.
- **Entregables: los links ahora vencen a las 48 h.** `/static/reports` estaba
  montado con `StaticFiles`: cualquiera que adivinara el nombre se bajaba el
  informe financiero de otro. Ahora es un handler con firma HMAC + vencimiento
  (`core/signed_files.py`). **Impacto en tu flujo**: si SOL guarda un link y lo
  manda después (Telegram, recordatorio, conversación vieja), a las 48 h da 404.
  Hay que re-firmar al mandar, no reusar la URL guardada.
- **`corralones.py` — te tocamos una línea.** `reverse_geocode()` mandaba las
  coordenadas GPS exactas a Nominatim. Como la llamada usa `zoom=13` y sólo
  resuelve ciudad/partido, la precisión no aportaba nada y sí exponía el
  domicilio. Se redondea a 3 decimales (~110 m) antes de salir (`:93`). Los
  corralones que devuelve deberían ser los mismos; si ves diferencias, avisá.
- **La memoria de voz se limpia al cerrar sesión.** `re_voice_memory` sobrevivía
  al logout y quedaba vivo en computadoras compartidas. Ahora se borra en los
  tres caminos de salida de `authService.js`. Si tu flujo de voz asumía que esos
  datos persisten entre sesiones, ya no vale.
- **Multi-cuenta (hasta 5, estilo ChatGPT).** Dos cambios de comportamiento que
  te pueden confundir debuggeando: `logout()` ya no siempre lleva al login —
  cierra la cuenta actual y salta a la siguiente guardada, recargando la página;
  y `login.html?add=1` no rebota a la app aunque haya sesión válida.
- **`vcRTMirror`**: hoy usa `scrollBottom(!vcState.mini||vcAtChatBottom())` —
  fuerza el scroll salvo en modo mini con el usuario leyendo arriba. (La nota
  vieja decía `scrollBottom(true)`; ya estaba desactualizada.)

---

## 7. 📦 Features nuevas en `main` (informativo)

Todas están live en Railway + Netlify. No necesitan nada de vos salvo lo de la
sección 1.

- **Informar un error** — reportes con número de ticket + bandeja admin.
- **Configuración → Almacenamiento** — todos tus archivos con buscador, renombrar,
  descargar y borrar.
- **Configuración → Cuenta** — nombre, email verificado por código, teléfono,
  contraseña, 2FA (app authenticator o email) y baja con 30 días de gracia.
- **Configuración → Facturación** — hasta 2 tarjetas (principal y respaldo),
  cambiar cuál cobra, y recuperación cuando un cobro se rechaza. El número de
  tarjeta nunca llega al backend (lo tokeniza el SDK de MP en el navegador).
- **`GET /api/account/export`** — derechos del titular (art. 14 de la 25.326 da
  10 días). Devuelve las **29 colecciones** que cuelgan de la cuenta (eran 27
  hasta que Facturación sumó `tarjetas_guardadas` y `cobros_rechazados`). Va
  **sin gate de plan** a propósito, y no incluye credenciales ni los bytes de los
  planos.
  Si sumás tablas colgadas del usuario, acordate de sumarlas: la Política promete
  "todos tus datos".
- **Ciclo de cobro**: los 5 días de gracia ahora son reales (antes MP pausaba y
  el webhook cortaba el acceso igual). Migración **0038**, puramente aditiva.

**Tests nuevos** para tu regresión (corrélos por archivo, como siempre):
`tests/test_hardening_legal.py` y `tests/test_billing_cards.py`.

> Para que no pierdas tiempo: `test_all` y `test_project_full` están en rojo,
> **pero venían así**. Lo verificamos con un worktree limpio: fallan idénticos
> commit a commit. No los rompimos.

---

## 8. 🗄️ Resuelto — para que no lo persigas

Esto ocupaba la mitad de la nota anterior. Ya está, no hagas nada:

> **Ignorá `docs/PARA_AGUSTIN.md`.** Es de junio, tiene un nombre casi igual a
> este y está al lado en la misma carpeta, pero su punto 0 arranca con "NETLIFY —
> el frontend NO se está publicando 🔴 URGENTE", que es exactamente lo que ya
> está resuelto. Le pusimos un cartel de obsoleto arriba; esta nota lo reemplaza.

- **El backend no se desplegaba en Railway** (bloqueado desde el 25-jul en
  `4704d42`). **Resuelto**: prod sirve `32553c7`, los 15 commits posteriores
  entraron y las migraciones corrieron. `POST /api/bugs` y
  `GET /api/storage/files` responden 401 (existen y piden sesión), ya no 404.
  Si algún día volvés a ver `/health` desfasado de `main`, mirá
  **Settings → Source** en Railway.
- **El frontend esperando publicación en Netlify.** **Resuelto**: ya está
  publicado, y publicado el HEAD actual. Todo lo que la nota listaba como
  pendiente de subir —`connect_telegram`, el selector de dólar Blue/Oficial, el
  bloqueo de `<img>` en `parseSolMd`, el SRI de pdf.js y Sentry, el rail de
  acceso rápido, el auto-scroll inteligente— ya lo están viendo los usuarios.

> Dos detalles menores que corregimos de paso: la migración 0037 tiene **11**
> `ADD COLUMN`, no 10 (la nota decía las dos cosas en distintos párrafos); y el
> SRI de pdf.js se setea vía `s.integrity` sobre un script inyectado
> dinámicamente, no en una etiqueta `<script>` estática — y el
> `pdf.worker.min.js` se carga por `workerSrc` **sin** integrity, eso sí sigue
> abierto.
