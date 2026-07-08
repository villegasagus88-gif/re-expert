// Configuración pública del frontend.
//
// Arquitectura de prod:
//   - Frontend en Netlify (re-expert.netlify.app o dominio custom).
//   - Backend en Railway (re-expert-production.up.railway.app).
//   - El browser habla DIRECTO con Railway (no via Netlify proxy).
//
// ¿Por qué directo y no via Netlify reverse-proxy?
//   - Los rewrites de Netlify a hosts externos tienen un timeout duro
//     de ~26s. El chat con streaming SSE + KB router routinely supera
//     ese límite (el modelo razonando + cargando contexto del KB).
//   - Resultado del proxy: 504 desde Netlify Edge, aunque Railway haya
//     devuelto 200 OK. La conexión SSE se corta.
//   - Solución: API_BASE apunta directo a Railway. CORS ya está bien
//     configurado server-side (FRONTEND_URL incluye re-expert.netlify.app).
//   - Trade-off: dos dominios visibles para el browser, pero a cambio
//     conseguimos streams largos sin cortes. Histórico: af20676.
//
// Para local dev hay dos modos:
//   - docker-compose con nginx (puerto :5173, same-origin → API_BASE='').
//   - backend FastAPI suelto en :8000 → API_BASE='http://localhost:8000'.

window.RE_CONFIG = {
  SUPABASE_URL: 'https://uaiiqjouxlcvleiimokz.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_lPyD13RGcJG4bjJIew9z6g_cYQ9n269',
  // En prod se setea a la URL de Railway abajo. En dev queda local.
  API_BASE: '',
  // Sentry — dejar vacío para deshabilitar. sentry.js además ignora localhost.
  SENTRY_DSN: '',
  SENTRY_ENVIRONMENT: 'production',
  SENTRY_TRACES_SAMPLE_RATE: 0.0,
  VERSION: '0.1.0'
};

// Detección automática del API_BASE:
//   - Cualquier dominio público (Netlify, Cloudflare Tunnel, custom):
//       → Railway directo (bypass del proxy por timeout de 26s en SSE).
//   - localhost:5173 (docker-compose nginx con proxy a /api/):
//       → same-origin (API_BASE='').
//   - localhost otro puerto (dev frontend suelto):
//       → backend separado en :8000.
(function () {
  var loc = (typeof window !== 'undefined' && window.location) || {};
  var h = (loc.hostname || '').toLowerCase();
  var port = loc.port || (loc.protocol === 'https:' ? '443' : '80');
  var isLocalhost = (h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0');

  if (!isLocalhost) {
    // Prod / cualquier dominio público → Railway directo.
    window.RE_CONFIG.API_BASE = 'https://re-expert-production.up.railway.app';
    return;
  }

  // Local: :5173 (compose nginx) = same-origin, otros = backend en :8000.
  window.RE_CONFIG.API_BASE = (port === '5173') ? '' : 'http://localhost:8000';
})();
