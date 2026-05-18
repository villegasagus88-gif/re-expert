// Configuración pública del frontend.
// - anon key de Supabase es pública: la seguridad la da Row Level Security.
// - API_BASE: URL del backend RE Expert (FastAPI en Railway).
//   En desarrollo local se puede overridear por hostname en el bloque de abajo.
window.RE_CONFIG = {
  SUPABASE_URL: 'https://uaiiqjouxlcvleiimokz.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_lPyD13RGcJG4bjJIew9z6g_cYQ9n269',
  // Producción (Railway). Reemplazar por el dominio definitivo cuando se configure.
  API_BASE: 'https://re-expert-production.up.railway.app',
  // Sentry — dejar vacío para deshabilitar. sentry.js además ignora localhost.
  SENTRY_DSN: '',
  SENTRY_ENVIRONMENT: 'production',
  SENTRY_TRACES_SAMPLE_RATE: 0.0,
  VERSION: '0.1.0'
};

// Detección automática del API_BASE según contexto (heurística por puerto):
//   - localhost:5173 (docker-compose nginx con proxy a /api/):
//       same-origin → API_BASE='' (rutas relativas)
//   - localhost en otro puerto (http-server/live-server suelto):
//       backend separado en :8000 → API_BASE='http://localhost:8000'
//   - Cualquier dominio público (Cloudflare Tunnel, Netlify, etc):
//       same-origin (asume reverse proxy a /api/* en producción)
(function () {
  var loc = (typeof window !== 'undefined' && window.location) || {};
  var h = (loc.hostname || '').toLowerCase();
  var port = loc.port || (loc.protocol === 'https:' ? '443' : '80');
  var isLocalhost = (h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0');

  if (!isLocalhost) {
    // Dominio público: same-origin (reverse proxy maneja /api/*).
    window.RE_CONFIG.API_BASE = '';
    return;
  }

  // Local: si estamos en :5173 (compose nginx con proxy), same-origin.
  // Cualquier otro puerto → backend separado en :8000.
  window.RE_CONFIG.API_BASE = (port === '5173') ? '' : 'http://localhost:8000';
})();
