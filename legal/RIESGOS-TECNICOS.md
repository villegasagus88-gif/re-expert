# Riesgos detectados en el código — exposición legal y de seguridad

> **Qué es este documento.** Durante la redacción del paquete legal se auditó el código
> fuente de RE Expert. Estos son los hallazgos donde **el código genera exposición legal
> real** — cosas que ningún documento arregla, porque un contrato no cambia lo que el
> software hace.
>
> **No son tareas legales: son tareas técnicas nuestras.** Están ordenadas por gravedad
> y con la evidencia para poder atacarlas.
>
> **Ninguno fue modificado en esta sesión** (se reportan, no se arreglan).
>
> Auditoría sobre el commit `3ce696a` de la branch `refactor/sol-hardening`.

---

## 🔴 Bloqueantes antes de publicar los documentos

### R1 — No hay política de privacidad ni términos publicados, y la app ya transfiere datos a EE.UU.
**Estado:** ✅ **Este paquete lo resuelve** (queda pendiente publicarlo en la app).
La app muestra "Política y privacidad" y "Términos de servicio" en el menú, pero
renderizan "Próximamente" (`frontend/app.html:2113-2115`, `acctRenderPane`).
**Exposición:** art. 6 Ley 25.326 (deber de información) + art. 12 (transferencia
internacional). Sin política publicada, la transferencia a Anthropic/Supabase/Railway
no tiene base informada.
**Falta:** cablear los documentos a esas dos secciones y a un link público en el footer.

### R12 — No existe Botón de Arrepentimiento
**Evidencia:** `grep -rni 'arrepentimiento'` → cero resultados operativos.
**Exposición:** la **Resolución 424/2020** de la Secretaría de Comercio Interior lo
exige de forma **visible en la página de inicio** y que inicie la revocación sin ningún
otro trámite. Es sancionable por sí solo, con independencia de lo que digan los T&C.
**Es el único ítem de esta lista que es obligación legal directa e incumplida hoy.**
**Tarea:** botón en la home + endpoint de revocación + aviso al titular.

### R8 — La app promete borrar "todos tus datos" y el código conserva el email
**Evidencia:** promesa en `frontend/app.html:2866`; realidad en
`backend/models/bug_report.py:49-59` — `ondelete="SET NULL"` con `reporter_email`
preservado a propósito. Además, los documentos generados en el bucket `reports/` nunca
se borran (`services/document_service.py:6-8`).
**Exposición:** art. 16 Ley 25.326 (supresión). Es una declaración **escrita y
verificable** que el propio sistema desmiente — el peor tipo de prueba.
**Hay que elegir una:** (a) que la purga limpie `reporter_email` y los objetos del
bucket, o (b) cambiar el copy de la app para declarar las excepciones. La Política de
Privacidad quedó redactada declarando las excepciones (opción b), pero **el copy de la
app sigue diciendo "todos"**.

---

## 🟠 Alto — vulnerabilidades explotables

### R3 — Informes financieros servidos sin autenticación
**Evidencia:** `backend/main.py:356-364` monta `/static/reports` con `StaticFiles` **sin
`Depends(get_current_user)` ni gate de plan**. El nombre del archivo es
`{scope}-{fecha}-{uuid4().hex[:8]}.{ext}` (`document_service.py:415`) = **32 bits de
entropía con prefijo predecible**.
**Qué contienen:** presupuesto, costo real, pagos y proveedores de la obra del usuario.
**Exposición:** arts. 9 y 10 Ley 25.326. Fuga por enumeración o por reenvío del link.
Imposible sostener "medidas técnicas adecuadas" en una pericia.
**Agrava:** el `share_message` empuja al usuario a mandar ese link por WhatsApp.

### R9 — Sentry puede exfiltrar contraseñas en texto plano el día que se active
**Evidencia:** `backend/main.py:61-77` setea `send_default_pii=False` y
`max_request_body_size="never"` pero **no setea `include_local_variables=False`**, cuyo
default es `True` en `sentry-sdk 2.18.0`.
**Frame vulnerable:** `auth_service.py:116` → `async def login_user(email, password)`.
Cualquier excepción ahí adentro (timeout de DB, error de bcrypt) manda **email y
contraseña en claro** a un tercero.
**Hoy es inerte** (`SENTRY_DSN` vacío), pero la documentación del proyecto empuja a
activarlo. **Arreglo de una línea.**

### R5 — El secreto TOTP del 2FA se guarda sin cifrar
**Evidencia:** `backend/models/user.py:54` — `twofa_secret` es `String` plano; se asigna
sin transformar en `account_security_service.py`. Los códigos de recuperación **sí**
están hasheados; la semilla no.
**Exposición:** con un dump de `profiles` se generan códigos 2FA válidos → el segundo
factor deja de existir frente a una filtración. Ofrecer "verificación en dos pasos"
mientras la semilla está en claro no resiste una pericia.

### R4 — Credenciales de hasta 5 cuentas en `localStorage`, con CSP permisivo
**Evidencia:** `frontend/authService.js` guarda `{refresh, access}` por cuenta;
`netlify.toml:99` tiene `script-src 'self' 'unsafe-inline'`; no hay endpoint de logout
server-side.
**Exposición:** un solo XSS entrega credenciales de larga duración (7 días, **90 si es
admin**) de hasta 5 cuentas, sin forma de revocarlas salvo cambiar la contraseña.
Obligaría a notificar el incidente.
**Nota:** es una consecuencia asumida del diseño multicuenta; la mitigación realista es
sacar `'unsafe-inline'` del CSP y agregar revocación server-side.

### R7 — Un LLM decide solo qué datos personales se persisten
**Evidencia:** `api/routes/chat.py:232-330` — `_persist_memory_item()` guarda con
`source="auto-silent"`, sin confirmación. El prompt ordena *"GUARDÁ EN SILENCIO (llamá
remember sin pedir permiso)"* (`anthropic_service.py:470-472`). La única barrera contra
guardar un CBU o una tarjeta es **texto en el prompt** — no hay regex ni validación.
**Exposición:** arts. 4 (finalidad determinada) y 5-6 (consentimiento) Ley 25.326. El
alcance de la recolección lo fija un modelo probabilístico.
**Mitigación sugerida:** filtro server-side (CBU/CUIT/tarjeta) en `_persist_memory_item`
+ un interruptor para desactivar la memoria automática.

### R6 — Datos de terceros que nunca consintieron
**Evidencia:** `models/contact.py:34-40` (nombre, teléfono, email), `plan_projects.client_name`,
`payments.proveedor`, `PlanAlert.responsible`. Todo viaja al LLM vía `agent_tools`.
**Exposición:** somos corresponsables del tratamiento de personas que jamás tuvieron
contacto con nosotros, y el usuario **no puede consentir por otro**.
**Estado:** ✅ **mitigado contractualmente** en la cláusula 9.3 de los T&C y el punto 4.3
de la Política. Queda como riesgo residual porque el traslado contractual no elimina la
corresponsabilidad frente a la autoridad.

---

## 🟡 Medio

### R2 — Transferencia internacional sin instrumento documentado
No hay ningún DPA ni cláusula contractual tipo firmada con Supabase, Railway, Netlify,
Anthropic, OpenAI ni Resend en el repositorio.
**Estado:** la Política se apoya en el **consentimiento informado** (art. 12 inc. 2
Ley 25.326), que es una base válida. Aun así, corresponde adherir a los DPA que estos
proveedores ya ofrecen — es gratis y cierra el punto.

### R11 — No existe forma de ejercer derechos ARCO
`grep 'exportar mis datos|portabilidad|25.326|habeas'` → **0 resultados**. Los únicos
exports son parciales (memoria de un workspace, bajar un plano).
**Exposición:** art. 14 Ley 25.326 da **10 días corridos** para responder un pedido de
acceso; habilita habeas data y sanción de la AAIP.
**Dato útil:** el mapa de FK `CASCADE` es exactamente la lista de lo que debería incluir
un `GET /api/account/export`.

### R10 — No hay evidencia de backups automáticos ni de restore probado
`docs/BACKUPS.md:29` dice textualmente que en el plan **Free no hay backups
automáticos**, y la configuración figura como pendiente. Cero cron, cero script de dump.
**Exposición:** cualquier cláusula de "resguardamos tu información" sería no
acreditable. **Por eso la Política no menciona copias de seguridad** — y no debe
mencionarlas hasta que existan y se pruebe una restauración.

### R14 — Google Fonts transmite la IP del visitante antes de cualquier consentimiento
Se carga en los 9 HTML, incluidos `login.html` y `register.html`.
**Exposición:** en la UE esta práctica fue sancionada bajo RGPD. Dado que hay expansión
internacional prevista, conviene **alojar las tipografías localmente** — es un cambio
técnico menor que elimina la transferencia.

### R15 — Nominatim recibe coordenadas GPS exactas, sin redondeo
`backend/api/routes/corralones.py:84-98` envía lat/lon sin truncar, y el User-Agent
expone `contacto@re-expert.app`.
**Mitigación trivial:** redondear a 2-3 decimales (~1 km) alcanza de sobra para
resolver el nombre de la zona.

---

---

## 🔵 Detectados al contrastar los documentos contra el código

Estos surgieron de una segunda pasada que verificó afirmación por afirmación. **Los
documentos ya fueron corregidos** para decir la verdad; lo que sigue es la tarea técnica
que quedaría si se quisiera que el producto haga lo que sería mejor prometer.

### R16 — La cancelación de suscripción corta el acceso en el acto
`services/mercadopago_service.py:503` pone `plan = "inactive"` en la misma request → el
paywall se activa inmediatamente, aunque el período esté pagado.
**Exposición:** cobrarle a un consumidor un período completo y cortarle el acceso antes
de que termine es exactamente el tipo de desequilibrio que el art. 37 Ley 24.240
sanciona. **Los T&C ahora lo declaran con honestidad, pero la salida correcta es
implementar baja diferida al fin del período abonado.**

### R17 — La ruta de cancelación no existe en la app
`app.html:2228-2237`: sólo `error`, `almacenamiento` y `cuenta` renderizan UI real;
**`facturacion` cae al placeholder "Próximamente"**. El botón de cancelar vive en
`account.html`, página huérfana a la que sólo se llega por un fallback de `pricing.html`.
**Problema:** tanto los T&C como la app mandan al usuario a "Configuración →
Facturación" para cancelar, y para poder darse de baja hay que cancelar primero. **Hoy
ese camino no existe.**

### R18 — Sin punto de aceptación de los documentos
No hay enlaces legales en el footer, ni checkbox de aceptación en el registro, y las
secciones "Términos" y "Privacidad" muestran "Próximamente". **Un contrato que declara
que el usuario acepta al registrarse, sin un punto de aceptación registrable, no tiene
respaldo probatorio.**

### R19 — El logout no limpia la memoria de voz del navegador
`authService.js` borra ACCESS/REFRESH/USER/FLAG pero **no `re_voice_memory`**, que
contiene datos que el usuario pidió recordar. Queda en el equipo después de cerrar
sesión — problema en computadoras compartidas.
**Arreglo:** una línea (`localStorage.removeItem('re_voice_memory')`) en `logout()` y en
la baja.

### R20 — No hay procedimiento de reembolso
Cero llamadas a la API de refunds en todo el backend.
`mercadopago_service.py:296-330` ya deja anotado *"requiere reembolso manual"* para pagos
duplicados. El derecho de revocación es una obligación legal que existe igual: **hay que
definir quién ejecuta el reembolso, en qué panel y en cuántos días hábiles.**

### R21 — Los registros contables se borran con la cuenta
`payment.py:22` y `course_purchase.py:34` son `ondelete="CASCADE"`. Si el Titular
necesita conservar respaldo fiscal por 10 años (art. 328 CCyC), hay que implementarlo en
una tabla desvinculada de la cuenta. **La Política no declara esa retención justamente
porque hoy no ocurre.**

### R22 — El dominio `re-expert.app` puede no estar operativo
`docs/DOMAIN.md` es un runbook para **comprar** el dominio; el sitio productivo es
`re-expert.netlify.app`. La casilla `contacto@re-expert.app` aparece sólo como texto en
un User-Agent, y `RESEND_API_KEY` no está configurada.
**Exposición:** un canal de contacto que rebota vacía de contenido el Botón de
Arrepentimiento y el ejercicio de derechos ARCO. **Antes de publicar hay que confirmar
que el dominio es nuestro y que esa casilla recibe y se lee.**

---

## Resumen de tareas técnicas

| # | Tarea | Prioridad | Esfuerzo |
|---|---|---|---|
| R12 | Botón de Arrepentimiento (obligación legal incumplida) | 🔴 Bloqueante | Medio |
| R1 | Publicar los documentos en la app + footer | 🔴 Bloqueante | Bajo |
| R8 | Resolver la contradicción del "todos tus datos" | 🔴 Bloqueante | Bajo |
| R3 | Autenticar `/static/reports` | 🟠 Alto | Bajo |
| R9 | `include_local_variables=False` en Sentry | 🟠 Alto | **Una línea** |
| R5 | Cifrar el secreto TOTP en reposo | 🟠 Alto | Medio |
| R7 | Filtro server-side de datos financieros en la memoria automática | 🟠 Alto | Medio |
| R4 | Sacar `'unsafe-inline'` del CSP + logout server-side | 🟠 Alto | Medio |
| R11 | `GET /api/account/export` | 🟡 Medio | Medio |
| R10 | Backups automáticos + prueba de restore | 🟡 Medio | Config |
| R2 | Adherir a los DPA de los proveedores | 🟡 Medio | Trámite |
| R14 | Alojar las tipografías localmente | 🟡 Medio | Bajo |
| R15 | Redondear coordenadas antes de geocodificar | 🟡 Medio | **Una línea** |
| R17 | Sección Facturación operativa (hoy "Próximamente") | 🔴 Bloqueante | Medio |
| R18 | Enlaces legales + checkbox de aceptación en el registro | 🔴 Bloqueante | Bajo |
| R22 | Confirmar dominio y casilla de contacto operativa | 🔴 Bloqueante | Trámite |
| R16 | Baja diferida al fin del período abonado | 🟠 Alto | Medio |
| R20 | Procedimiento de reembolso definido | 🟠 Alto | Proceso |
| R19 | Limpiar `re_voice_memory` en el logout | 🟡 Medio | **Una línea** |
| R21 | Respaldo contable desvinculado de la cuenta | 🟡 Medio | Medio |
