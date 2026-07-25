# Módulo de Geolocalización (plataforma)

> Capacidad transversal nueva (2026-07-25). **Todavía no está integrada a
> ninguna feature** — este doc explica qué hay construido y cómo enchufarlo
> cuando decidamos dónde usarlo. Cero cambios sobre lo que ya funcionaba:
> archivos nuevos + 2 líneas aditivas (mount del router y registro del modelo).

## Qué resuelve

Ubicación real del usuario, con consentimiento explícito, para cualquier
feature futura: materiales/proveedores cerca de la obra, rutas de visita de
SOL, oportunidades por zona, contexto de ubicación en el chat, etc.

## Arquitectura

```
frontend/location.js          ← módulo standalone (window.RELocation)
        │  Geolocation API del browser (permiso nativo) + throttle
        ▼
POST /api/location/fix        ← backend/api/routes/location.py
        ▼
services/location_service.py  ← validación, consent gate, precisión, geohash, retención
        ▼
user_locations (+ user_location_settings)   ← migración 0034
```

## Modelo de privacidad (no negociable)

| Regla | Implementación |
|---|---|
| Consent-first | Sin `consent='granted'` el backend rechaza fixes con 403. Default: `unset` (fail-safe). |
| Precisión elegible | `exact` (lo que dé el device) o `coarse`: el server redondea a ~1.1 km **antes** de persistir — la coordenada exacta nunca toca el disco, y los metadatos finos (accuracy/altura/rumbo/velocidad) se descartan. |
| Retención acotada | Máx 500 fixes por usuario y 90 días (poda en cada insert). Env: `LOCATION_MAX_FIXES_PER_USER`, `LOCATION_RETENTION_DAYS`. |
| Purga self-service | `DELETE /api/location/me` borra todo el historial. |
| Cascade | Borrar la cuenta borra settings + fixes (FK `ON DELETE CASCADE`). |
| Sin fugas a logs | Coordenadas nunca se loguean; el `__repr__` del modelo no las incluye. |
| Cache local efímero | El frontend cachea el último fix en `sessionStorage` (muere con la pestaña), nunca `localStorage`. |

## Endpoints (todos auth + plan gate, scoped al usuario)

| Método | Ruta | Qué hace | Rate limit |
|---|---|---|---|
| GET | `/api/location/consent` | Estado actual (`unset/granted/denied` + precisión) | — |
| PUT | `/api/location/consent` | Otorgar/negar + elegir precisión | 30/min |
| POST | `/api/location/fix` | Reportar un fix (403 sin consent) | 12/min |
| GET | `/api/location/me` | Última ubicación conocida | — |
| GET | `/api/location/history` | Historial paginado (`limit`≤200, `before`) | — |
| DELETE | `/api/location/me` | Purga total | 5/h |

## Frontend — `window.RELocation`

Incluir en la página **después de `authService.js`**:
```html
<script src="location.js"></script>
```

```js
// Flujo típico de opt-in (la UI la definimos en la fase de integración):
await RELocation.setConsent('granted', 'exact');   // 1) consentimiento app-level
const { stored } = await RELocation.captureOnce(); // 2) permiso del browser + fix

// Tracking continuo (throttle: ≥30 s Y ≥25 m entre reportes):
RELocation.startWatch({ onFix: (fix, stored) => { /* ... */ } });
RELocation.stopWatch();

// Lectura barata (cache de sesión 5 min → backend):
const latest = await RELocation.getLatest();
```

## Geohash — por qué y cómo usarlo después

Cada fix guarda un geohash (9 chars exact ≈ 4.8 m; 5 chars coarse ≈ 4.9 km).
Consultas de proximidad **sin PostGIS**:

```sql
-- "usuarios/fixes cerca de la celda del Obelisco"
SELECT * FROM user_locations WHERE geohash LIKE '69y7p%';
```

Si algún día necesitamos radios exactos o joins espaciales pesados → activar
PostGIS en Supabase y agregar una columna `geography` en una migración nueva;
el geohash sigue sirviendo como índice grueso.

## Extensiones previstas (NO implementadas, a decidir en la integración)

- **IP fallback** (`source='ip'`): ubicación gruesa server-side sin permiso del
  browser. El schema ya reserva el source; falta elegir proveedor.
- **Reverse geocoding** ("Palermo, CABA" en vez de coords): pluggable en el
  service; requiere Nominatim (gratis, rate-limited) o Google (key).
- **Tool de SOL** (`get_user_location`): exponer la última ubicación al agente
  — pasa por la misma `_redact_for_model` que el resto si hace falta.

## Tests

```bash
cd backend && python -m pytest tests/test_location.py --import-mode=importlib -q
```
27 tests: auth en los 6 endpoints + unit de geohash (valores de referencia),
validación de coordenadas, coarsen, consent gate, clamp de timestamps y
haversine.
