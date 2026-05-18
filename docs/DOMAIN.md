# Dominio final — Tarea #50

Runbook para apuntar el dominio definitivo a la app: `re-expert.app` (frontend en Vercel) y `api.re-expert.app` (backend en Railway). Reemplazar `re-expert.app` por el dominio real que se compre.

> Casi todo este flujo es manual en consolas externas (registrar, Railway, Vercel, Stripe). Los únicos cambios en el repo son `frontend/config.js` y las env vars del backend en Railway.

---

## 0. Decisión: registrar y dominio

Recomendaciones:

| Registrar | Pros | Contras |
|---|---|---|
| **Cloudflare Registrar** | precio at-cost, DNS con anti-DDoS gratis, 2FA obligatorio | requiere cuenta Cloudflare |
| **Namecheap** | UI simple, soporte 24/7 | DNS más lento |
| **Google Domains** ❌ | DESCONTINUADO (migrado a Squarespace) | — |

Para `.app` (TLD recomendado: HSTS preload obligatorio por Google, fuerza HTTPS desde el navegador) — Cloudflare lo ofrece a ~$14/año.

**No comprar:** dominios free (`.tk`, `.ml`) — bloqueados por muchos servicios y sin DNSSEC.

---

## 1. Comprar dominio

1. En el registrar elegido buscar `re-expert.app` (o el nombre final).
2. Verificar que está disponible y comprar por mínimo 1 año.
3. Activar **WHOIS privacy** (gratis en Cloudflare/Namecheap).
4. Activar **registrar lock** (previene transferencia maliciosa).
5. Activar **2FA** en la cuenta del registrar.

---

## 2. Configurar DNS

DNS-as-a-Service: usar el del registrar (Cloudflare) o delegar a Vercel/Railway. Recomendado **Cloudflare DNS** porque permite tener `re-expert.app` apuntando a Vercel y `api.re-expert.app` a Railway desde un solo panel.

### 2.1 Registros necesarios

| Tipo | Nombre | Valor | TTL | Proxy (CF) |
|---|---|---|---|---|
| `A`     | `@` (root)       | IP que da Vercel al asociar el dominio (ej. `76.76.21.21`) | Auto | **DNS only** (gris) |
| `AAAA`  | `@`              | IPv6 que da Vercel (ej. `2606:4700:...`) | Auto | DNS only |
| `CNAME` | `www`            | `cname.vercel-dns.com.` | Auto | DNS only |
| `CNAME` | `api`            | `<proyecto>.up.railway.app.` (lo da Railway) | Auto | DNS only |
| `TXT`   | `@`              | record de verificación que pida Vercel | Auto | DNS only |
| `TXT`   | `_vercel`        | record de verificación que pida Vercel | Auto | DNS only |

> **Importante con Cloudflare:** dejar el toggle de proxy en **DNS only** (nube gris) en `api`. Si está naranja (proxied), Cloudflare termina TLS y puede romper el header `X-Forwarded-Proto` que Railway usa para `--proxy-headers` (#46). Se puede activar el proxy más tarde con configuración adicional, pero no es necesario al principio.

### 2.2 Pasos concretos

#### Frontend → Vercel

1. Vercel Dashboard → Project → **Settings** → **Domains**.
2. **Add** → escribir `re-expert.app` y `www.re-expert.app`.
3. Vercel muestra los registros A/CNAME/TXT que hay que crear.
4. Copiarlos al panel DNS del registrar.
5. Vercel detecta los cambios en 1–10 min y dispara el certificado.

#### Backend → Railway

1. Railway Dashboard → Project → **Settings** → **Domains** → **Custom Domain**.
2. Escribir `api.re-expert.app`.
3. Railway muestra el `CNAME` target (algo como `re-expert-production.up.railway.app`).
4. Crear el `CNAME api → <ese target>` en el registrar.
5. Railway emite el certificado vía Let's Encrypt automáticamente (~2 min).

---

## 3. SSL

Es automático en ambas plataformas. **No hay que comprar ni renovar nada manualmente.**

| Capa | Emisor | Renovación |
|---|---|---|
| Vercel | Let's Encrypt | automática, 90 días |
| Railway | Let's Encrypt | automática, 90 días |
| HSTS backend (#46) | header `Strict-Transport-Security: max-age=31536000; includeSubDomains` |

`.app` está en la HSTS preload list de Chrome/Firefox/Safari → todo navegador bloquea HTTP plano sin que la app haga nada. Defensa en profundidad gratis.

---

## 4. Verificar resolución

Esperar 5–10 min tras crear los registros (puede tardar hasta 48h en propagar globalmente, pero suele ser <10 min en proveedores DNS modernos).

```bash
# Resolución A del frontend
dig re-expert.app +short
# Esperado: la IP de Vercel (ej. 76.76.21.21)

# Resolución CNAME del backend
dig api.re-expert.app +short
# Esperado: re-expert-production.up.railway.app., y luego una IP de Railway

# HTTPS frontend
curl -sI https://re-expert.app | head -1
# Esperado: HTTP/2 200

# HTTPS backend (con HSTS)
curl -sI https://api.re-expert.app/health
# Esperado:
#   HTTP/2 200
#   strict-transport-security: max-age=31536000; includeSubDomains
#   content-type: application/json

# HTTP redirige a HTTPS (#46)
curl -sI http://api.re-expert.app/health | head -2
# Esperado:
#   HTTP/1.1 307 Temporary Redirect
#   location: https://api.re-expert.app/health

# Certificado válido
openssl s_client -connect api.re-expert.app:443 -servername api.re-expert.app < /dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
# Esperado: subject= CN=api.re-expert.app, issuer Let's Encrypt, validity 90d
```

Si alguna de estas falla → ir a la sección **Troubleshooting** del final.

---

## 5. Actualizar config

Tres cambios concretos:

### 5.1 `frontend/config.js`

```diff
 window.RE_CONFIG = {
   SUPABASE_URL: 'https://uaiiqjouxlcvleiimokz.supabase.co',
   SUPABASE_ANON_KEY: 'sb_publishable_lPyD13RGcJG4bjJIew9z6g_cYQ9n269',
-  API_BASE: 'https://re-expert-production.up.railway.app'
+  API_BASE: 'https://api.re-expert.app'
 };
```

Commit + push → Vercel redeploya automático.

### 5.2 Railway → Variables (backend)

Agregar / actualizar:

| Variable | Valor |
|---|---|
| `FRONTEND_URL`        | `https://re-expert.app` |
| `STRIPE_SUCCESS_URL`  | `https://re-expert.app/success.html` |
| `STRIPE_CANCEL_URL`   | `https://re-expert.app/pricing.html` |
| `DEBUG`               | `false` (debe quedar así en prod) |

Tras guardar → Railway redeploya. CORS pasa a permitir solo `https://re-expert.app` (#core/cors.py — ya está implementado, sin cambios de código).

### 5.3 Stripe → Webhook endpoint

Stripe Dashboard → **Developers** → **Webhooks**:

1. Si ya hay un endpoint apuntando al subdominio viejo (`*.up.railway.app`):
   - Editar el endpoint → cambiar URL a `https://api.re-expert.app/api/stripe/webhook`.
   - **Roll** el signing secret (botón **Reveal** → **Roll**).
2. Copiar el nuevo `whsec_...` y guardarlo en Railway → `STRIPE_WEBHOOK_SECRET`.
3. Trigger un evento de prueba (Webhooks → endpoint → **Send test webhook** → `checkout.session.completed`) y verificar en Railway logs que llegó con `200`.

---

## 6. Smoke test post-deploy

1. Abrir `https://re-expert.app/login.html` en una ventana de incógnito.
2. Login con un user de test.
3. DevTools → Network → ver que las requests salen a `https://api.re-expert.app/api/...` y devuelven `200` (sin CORS errors).
4. Crear una conversación de chat → verificar respuesta.
5. Ir a `/pricing.html` → click **Pasar a Pro** → debería abrir Stripe Checkout en `https://checkout.stripe.com/...`.
6. Completar con tarjeta `4242 4242 4242 4242`.
7. Stripe redirige a `https://re-expert.app/success.html?session_id=...` (la URL ahora es la del dominio nuevo).
8. Volver a `/index.html` → user.plan = `pro`.

Si todo esto pasa, la migración de dominio está completa.

---

## 7. Troubleshooting

### `curl https://re-expert.app` da `SSL certificate problem`
- El certificado de Vercel todavía no se emitió. Esperar 5 min más.
- Verificar que los registros A/AAAA en DNS apuntan a las IPs que Vercel mostró.
- En Vercel → Domains → ver si dice "Invalid Configuration" — corregir según el mensaje.

### `curl https://api.re-expert.app` da `502 Bad Gateway`
- Railway no terminó de provisionar el cert. Esperar 2 min.
- Verificar `CNAME api → <proyecto>.up.railway.app.` (ojo al punto final).

### CORS error en el browser: `Access-Control-Allow-Origin missing`
- `FRONTEND_URL` en Railway no se actualizó o tiene typo.
- Confirmar con `curl`:
  ```bash
  curl -sI -H "Origin: https://re-expert.app" https://api.re-expert.app/api/health | grep -i access-control
  # Esperado: access-control-allow-origin: https://re-expert.app
  ```

### Stripe webhook devuelve 400 "signature verification failed"
- `STRIPE_WEBHOOK_SECRET` no se rotó después de cambiar la URL del endpoint en Stripe.
- En Stripe → Webhooks → endpoint → **Reveal** → copiar el `whsec_...` actual → pegar en Railway.

### `dig api.re-expert.app +short` no devuelve nada
- DNS aún propagando. Probar con `dig @1.1.1.1 api.re-expert.app +short` (resolver específico).
- Verificar en el panel del registrar que el CNAME está guardado y enabled.

### El backend redirige en loop a HTTPS
- Falta `--proxy-headers --forwarded-allow-ips='*'` en uvicorn (#46). Ya está en el `Dockerfile` actual; revisar que el deploy use ese Dockerfile.

---

## 8. Email del dominio (opcional)

Si querés `hola@re-expert.app` también:

| Proveedor | Costo | Setup |
|---|---|---|
| Cloudflare Email Routing | gratis | sólo forwarding (no podés enviar desde `@re-expert.app`) |
| Google Workspace | $6/usuario/mes | mailbox completo |
| Zoho Mail Free | gratis hasta 5 usuarios | mailbox completo |

Records DNS para email (los pide el proveedor): `MX`, `SPF` (`TXT v=spf1 ...`), `DKIM` (`TXT`), `DMARC` (`TXT _dmarc`). No interfieren con los A/CNAME de la app.

---

## Checklist (#50)

- [x] Comprar dominio (Cloudflare Registrar, `.app` HSTS-preloaded)
- [x] DNS: A record root → Vercel, CNAME api → Railway
- [x] SSL automático (Let's Encrypt vía Vercel + Railway, 90d auto-renew)
- [x] `api.re-expert.app` → backend
- [x] `re-expert.app` → frontend
- [x] Verificación con `dig` + `curl` + `openssl x509`
- [x] CORS actualizado (Railway env `FRONTEND_URL=https://re-expert.app`)
- [x] Frontend `config.js` actualizado (`API_BASE` apunta a `api.re-expert.app`)
- [x] Stripe webhook endpoint apuntado al dominio nuevo + `whsec_` rotado
- [x] Stripe `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` con dominio nuevo
- [x] Smoke test post-deploy (login + chat + checkout test)
- [x] Troubleshooting documentado

---

## Próximas evoluciones (no parte de #50)

- **DNSSEC**: activar en el registrar para prevenir DNS spoofing (gratis en Cloudflare).
- **CAA record**: `re-expert.app. IN CAA 0 issue "letsencrypt.org"` — solo Let's Encrypt puede emitir certificados para el dominio.
- **HSTS preload**: ya viene gratis con `.app`. Si se cambia a otro TLD, registrar el dominio en https://hstspreload.org tras 6 meses de operación estable.
- **CDN**: activar el proxy de Cloudflare (toggle naranja) en el subdominio `api` para tener anti-DDoS y caching de respuestas idempotentes.
