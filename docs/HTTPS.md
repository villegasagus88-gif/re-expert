# HTTPS obligatorio — Tarea #46

Forzar HTTPS en producción para todo el tráfico (API y frontend).

## Capas activadas

| Capa                | Mecanismo                                      | Archivo                       |
|---------------------|------------------------------------------------|-------------------------------|
| Backend (Railway)   | `HTTPSRedirectMiddleware` + `Strict-Transport-Security` header | `backend/main.py`             |
| Backend (uvicorn)   | `--proxy-headers --forwarded-allow-ips='*'`    | `backend/Dockerfile`          |
| Frontend (Vercel)   | TLS auto + `upgrade-insecure-requests` meta    | `frontend/*.html`             |
| Hosting             | Certificados emitidos automáticamente          | Railway + Vercel              |

## Backend — FastAPI

### Redirect HTTP → HTTPS

`HTTPSRedirectMiddleware` de Starlette se monta solo cuando `settings.DEBUG=False`:

```python
if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(_HSTSMiddleware)
```

En desarrollo local (`DEBUG=True` en `.env`), el middleware se omite para que el dev server siga funcionando en HTTP.

### Reverse proxy (Railway)

Railway termina TLS en el edge y reenvía la conexión al contenedor por HTTP plano,
agregando `X-Forwarded-Proto: https`. Sin `--proxy-headers`, Starlette vería todas las requests como HTTP y entraría en un loop infinito de redirects.

El `Dockerfile` invoca uvicorn con:

```
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} \
       --proxy-headers --forwarded-allow-ips='*'
```

### HSTS

`_HSTSMiddleware` agrega en cada response:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

- `max-age=31536000` → 1 año.
- `includeSubDomains` → cubre todos los subdominios.
- `preload` está deshabilitado intencionalmente; activarlo solo cuando se haya verificado que **todos** los subdominios sirven HTTPS (es difícil de revertir).

## Frontend — meta tag

Cada `*.html` incluye:

```html
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
```

Esto fuerza a que el navegador convierta automáticamente cualquier `http://...` embebido (imágenes, scripts, fetch, links) a `https://...`. Defensa en profundidad por si algún recurso queda con esquema explícito por error.

## Cookies

El backend no setea cookies — la auth es **JWT en `Authorization: Bearer ...`**, persistido en `localStorage` del frontend. Por eso no hay flag `Secure` que configurar.

Si en el futuro se introducen cookies (por ejemplo para CSRF en formularios), agregar:

```python
response.set_cookie(
    key="...",
    value="...",
    httponly=True,
    secure=True,           # solo HTTPS
    samesite="strict",     # bloqueo CSRF
)
```

## Tests

`backend/tests/test_https.py` cubre:

- HTTP plano se redirige a HTTPS en prod.
- HTTPS pasa sin redirect cuando llega `X-Forwarded-Proto: https`.
- Header `Strict-Transport-Security` presente con `max-age` ≥ 1 año e `includeSubDomains`.
- En `DEBUG=True` (dev/test) el redirect se desactiva (no rompe local).

Los tests fuerzan `settings.DEBUG=False` y recargan `main` para evaluar el bloque condicional, restaurando el estado al terminar.

## Verificación post-deploy

Tras desplegar:

```bash
# 1. HTTP del backend debería redirigir
curl -sI http://api.tu-dominio.app/health
# Esperado: HTTP/1.1 307 Temporary Redirect, Location: https://...

# 2. HTTPS responde 200 con HSTS
curl -sI https://api.tu-dominio.app/health
# Esperado: HTTP/2 200, strict-transport-security: max-age=31536000; includeSubDomains

# 3. Vercel ya redirige HTTP→HTTPS por defecto
curl -sI http://re-expert.app
# Esperado: HTTP/1.1 308 Permanent Redirect, Location: https://...
```

## Checklist

- [x] SSL en hosting (Railway + Vercel auto)
- [x] Vercel HTTPS verificado (308 automático)
- [x] Middleware redirect HTTP → HTTPS en backend
- [x] Cookies con flag Secure (N/A: auth via JWT header)
- [x] HSTS header con max-age ≥ 1 año
- [x] `upgrade-insecure-requests` en frontend
- [x] uvicorn con `--proxy-headers` para que respete `X-Forwarded-Proto`
- [x] Test de redirect HTTP → HTTPS
- [x] Test de header HSTS
