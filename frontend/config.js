// Configuración pública del frontend.
//
// Arquitectura de prod:
//   - Frontend en Netlify (re-expert.netlify.app o dominio custom).
//   - Backend en Railway (re-expert-production.up.railway.app).
//   - Netlify hace reverse-proxy de /api/* → backend (ver netlify.toml).
//   - Por eso API_BASE='' en prod = same-origin = el browser nunca habla
//     directo con railway.app → sin CORS, sin mixed-content issues.
//
// Para local dev hay dos modos:
//   - docker-compose con nginx (puerto :5173, también same-origin).
//   - backend FastAPI suelto en :8000 (puerto :3000/:5500/etc del front).
//
// El bloque de detección al final aplica la heurística correcta.

window.RE_CONFIG = {
  SUPABASE_URL: 'https://uaiiqjouxlcvleiimokz.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_lPyD13RGcJG4bjJIew9z6g_cYQ9n269',
  // Default same-origin. Override automático abajo para dev local sin proxy.
  API_BASE: '',
  // Sentry — dejar vacío para deshabilitar. sentry.js además ignora localhost.
  SENTRY_DSN: '',
  SENTRY_ENVIRONMENT: 'production',
  SENTRY_TRACES_SAMPLE_RATE: 0.0,
  VERSION: '0.1.0'
};

// Detección automática del API_BASE:
//   - Cualquier dominio público (Netlify, Cloudflare Tunnel, dominio custom):
//       same-origin → API_BASE='' (el reverse proxy se encarga).
//   - localhost:5173 (docker-compose nginx con proxy a /api/):
//       same-origin → API_BASE=''.
//   - localhost en otro puerto (dev frontend suelto, sin proxy):
//       backend separado en :8000 → API_BASE='http://localhost:8000'.
(function () {
  var loc = (typeof window !== 'undefined' && window.location) || {};
  var h = (loc.hostname || '').toLowerCase();
  var port = loc.port || (loc.protocol === 'https:' ? '443' : '80');
  var isLocalhost = (h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0');

  if (!isLocalhost) {
    window.RE_CONFIG.API_BASE = 'https://re-expert-production.up.railway.app';
    return;
  }

  // En local: si el puerto es 5173 (compose nginx) usamos same-origin,
  // en cualquier otro puerto asumimos backend en :8000.
  window.RE_CONFIG.API_BASE = (port === '5173') ? '' : 'http://localhost:8000';
})();
