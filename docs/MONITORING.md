# Monitoring básico — RE Expert

Stack: **Sentry** (errores backend + frontend) + **UptimeRobot** (uptime y
alerta "app caída"). Todo en plan free, sin agregar costos al MVP.

## 1. Sentry — alta de proyectos

1. Crear cuenta gratis en https://sentry.io (Developer plan: 5k errores +
   10k transactions/mes, 1 usuario, retención 30 días — alcanza para MVP).
2. Crear **dos proyectos** dentro de la misma organización:
   - `re-expert-backend` — Platform: **Python → FastAPI**
   - `re-expert-frontend` — Platform: **JavaScript → Browser**
3. Copiar el DSN de cada proyecto desde *Settings → Projects → <project> →
   Client Keys (DSN)*.

> **Nota:** los DSN no son secretos absolutos (van embebidos en el bundle
> del frontend), pero es buena práctica no commitearlos. En backend el DSN
> vive solo en env vars; en frontend se inyecta en `config.js` en build/deploy.

## 2. Backend — configuración

Variables en `backend/.env` (o env vars de Railway):

```env
SENTRY_DSN=https://xxxxx@oXXX.ingest.sentry.io/YYY
SENTRY_ENVIRONMENT=production    # o staging / dev
SENTRY_TRACES_SAMPLE_RATE=0.0    # subir a 0.1 si querés performance traces
```

Cuando `SENTRY_DSN` está vacío Sentry no se inicializa (caso por defecto en
tests y dev local). El SDK ya viene en `requirements.txt`
(`sentry-sdk[fastapi]==2.18.0`) e instala las integraciones de FastAPI,
Starlette y asyncio en `main.py`.

Configuración relevante (en `main.py`):
- `send_default_pii=False` — no se envían IPs ni headers de auth.
- `max_request_body_size="never"` — los bodies pueden contener prompts del
  usuario, no se mandan a Sentry.
- `release=settings.VERSION` — permite asociar errores a una versión y ver
  regresiones por release.

### Verificar que captura

Endpoint temporal de smoke test (no commitear):

```python
@app.get("/__sentry_test")
async def _sentry_test():
    raise RuntimeError("sentry smoke test")
```

Pegar el endpoint, ver el error en *Issues* de Sentry, y borrarlo.

## 3. Frontend — configuración

En `frontend/config.js` setear:

```js
window.RE_CONFIG = {
  // ...
  SENTRY_DSN: 'https://xxxxx@oXXX.ingest.sentry.io/ZZZ',
  SENTRY_ENVIRONMENT: 'production',
  SENTRY_TRACES_SAMPLE_RATE: 0.0,
  VERSION: '0.1.0'   // bumpear con cada deploy
};
```

`frontend/sentry.js` se carga en los 6 HTML (`index`, `login`, `register`,
`account`, `pricing`, `success`). Hace 2 chequeos antes de bootear:
1. Si `SENTRY_DSN` está vacío → no carga el SDK.
2. Si el host es `localhost` o `127.0.0.1` → no carga el SDK (no
   contaminamos la cuota con errores de dev).

El SDK se trae del CDN oficial (`browser.sentry-cdn.com`, versión 7.119.0).
Si el CDN está inalcanzable falla en silencio: la app sigue funcionando sin
monitoring.

### Verificar que captura

Desde la consola del browser en producción:

```js
Sentry.captureException(new Error('frontend smoke test'));
```

## 4. Alertas por email — errores 500

En cada proyecto de Sentry: *Alerts → Create Alert → Issue Alert*.

Configuración recomendada (mismo template para backend y frontend):

| Trigger | Filtro | Action |
|---|---|---|
| `A new issue is created` | `event.level equals error or fatal` | Send a notification to `Email` → tu mail |
| `An issue changes state from resolved to unresolved` | — | Email |
| `The issue is seen by more than 10 users in 1 hour` | — | Email |

Para errores 500 específicos, agregar un filtro adicional:
- `event.tag http.status_code` → `equals 500` (o `>=500`).

> Si usás Slack/Discord en el futuro, Sentry tiene integración nativa free.

## 5. UptimeRobot — alerta "app caída"

1. Crear cuenta gratis en https://uptimerobot.com (50 monitores, intervalo
   mínimo 5 min, alertas por email ilimitadas).
2. Crear monitores tipo **HTTP(s)**:

| Nombre | URL | Tipo | Intervalo |
|---|---|---|---|
| RE Expert API | `https://api.<dominio>/health` | HTTP(s) | 5 min |
| RE Expert Frontend | `https://<dominio>/` | HTTP(s) | 5 min |

3. *Alert Contacts* → agregar tu email. Default: avisa al 1er fallo y al
   recuperarse. Para evitar ruido en flaps cortos, configurar en cada
   monitor *Advanced → Alert when down for X minutes* = 5 min.

4. (Opcional) Crear una **Status Page** pública gratuita, útil para
   transparencia con usuarios.

## 6. Dashboard de errores

Sentry ya provee uno por proyecto out-of-the-box (*Issues → Dashboard*).
Para una vista combinada backend+frontend:

1. *Dashboards → Create Dashboard*.
2. Widgets sugeridos:
   - **Errors over time** (línea, 24h, group by `project`)
   - **Top issues** (tabla, top 10 por *events*)
   - **Issues by environment** (barras)
   - **Apdex / failure rate** (si activás performance subiendo
     `SENTRY_TRACES_SAMPLE_RATE` > 0).

## 7. Checklist final

- [x] Cuenta Sentry free, 2 proyectos creados (backend + frontend)
- [x] Sentry SDK backend (`sentry-sdk[fastapi]==2.18.0`, init env-gated en `main.py`)
- [x] Sentry SDK frontend (`frontend/sentry.js` cargado en los 6 HTML, gated por DSN + no-localhost)
- [x] Alertas email para errores 500 (Sentry Issue Alerts con filtro de status code)
- [x] UptimeRobot — 2 monitores (`/health` backend, `/` frontend) con alerta a 5 min
- [x] Dashboard combinado en Sentry

## 8. Costo y límites

| Servicio | Plan | Cuota | Si se excede |
|---|---|---|---|
| Sentry | Developer (free) | 5k errores + 10k transactions/mes, retención 30d | Eventos descartados (no rompe la app) |
| UptimeRobot | Free | 50 monitores, intervalo 5 min, alertas email ilimitadas | N/A |

Cuando crezca el tráfico:
- Sentry Team plan ~26 USD/mes (50k errores, retención 90d, miembros ilimitados).
- UptimeRobot Pro ~7 USD/mes (intervalo 1 min + SMS alerts).
