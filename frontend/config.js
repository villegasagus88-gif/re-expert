// Configuración pública del frontend.
// - anon key de Supabase es pública: la seguridad la da Row Level Security.
// - API_BASE: URL del backend RE Expert (FastAPI en Railway).
//   En desarrollo local se puede overridear por hostname en el bloque de abajo.
window.RE_CONFIG = {
  SUPABASE_URL: 'https://uaiiqjouxlcvleiimokz.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_lPyD13RGcJG4bjJIew9z6g_cYQ9n269',
  // Producción (Railway). Reemplazar por el dominio definitivo cuando se configure.
  API_BASE: 'https://re-expert-production.up.railway.app'
};

// Override automático en desarrollo local (localhost/127.0.0.1 → backend en :8000)
(function () {
  var h = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';
  if (h === 'localhost' || h === '127.0.0.1') {
    window.RE_CONFIG.API_BASE = 'http://localhost:8000';
  }
})();
