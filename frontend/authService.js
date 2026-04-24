// authService.js — Frontend session management
//
// Responsabilidades:
//   - Mantener el access token JWT en memoria (variable en closure).
//   - Agendar auto-refresh ~60s antes de que expire.
//   - Exponer authFetch(url, opts) que inyecta Authorization: Bearer <token>
//     y retry automático si el backend responde 401.
//   - Redirigir a /login si no hay sesión o el refresh falla.
//   - Flag booleano en sessionStorage ("re_authed") para poder chequear
//     estado sin pagar un await a Supabase en cada página.
//
// NOTA sobre httpOnly cookies:
//   El SDK de Supabase requiere leer el refresh token desde JS para poder
//   renovar la sesión, por lo que hoy vive en localStorage (manejado por
//   Supabase). Migrar a httpOnly cookie exige proxyar login/refresh/logout
//   a través del backend. Está en la lista de mejoras de seguridad pero no
//   es bloqueante para el MVP.

(function () {
  const LOGIN_URL = 'login.html';
  const FLAG_KEY = 're_authed';
  const REFRESH_LEAD_MS = 60_000; // refresh 60s antes de expirar

  // Rutas públicas (no requieren sesión). Cualquier otra es protegida.
  // Coincide por "endsWith" sobre pathname en minúsculas.
  const PUBLIC_ROUTES = [
    '/login.html',
    '/register.html',
    '/forgot-password.html', // reservado para futuro
  ];

  let _accessToken = null;
  let _refreshTimer = null;

  // `ready` resuelve con {authenticated, session?} cuando el bootstrap inicial
  // termina. Permite que páginas protegidas puedan `await requireAuth()` sin
  // preocuparse por orden de carga.
  let _readyResolve;
  const _readyPromise = new Promise((r) => { _readyResolve = r; });
  let _readyResolved = false;

  function _markReady(value) {
    if (_readyResolved) return;
    _readyResolved = true;
    _readyResolve(value);
  }

  // ----- util -----
  function isPublicPage() {
    const p = (window.location.pathname || '').toLowerCase();
    return PUBLIC_ROUTES.some((r) => p.endsWith(r));
  }
  // Alias retrocompat
  const isAuthPage = isPublicPage;

  function redirectToLogin() {
    sessionStorage.removeItem(FLAG_KEY);
    _accessToken = null;
    if (_refreshTimer) { clearTimeout(_refreshTimer); _refreshTimer = null; }
    if (isAuthPage()) return;
    window.location.replace(LOGIN_URL);
  }

  function scheduleRefresh(expiresAtSec) {
    if (_refreshTimer) clearTimeout(_refreshTimer);
    if (!expiresAtSec) return;
    const msUntil = (expiresAtSec * 1000) - Date.now() - REFRESH_LEAD_MS;
    if (msUntil <= 0) {
      // Ya está por expirar: refresh inmediato.
      doRefresh();
      return;
    }
    _refreshTimer = setTimeout(doRefresh, msUntil);
  }

  async function doRefresh() {
    try {
      const { data, error } = await window.SB.client.auth.refreshSession();
      if (error || !data || !data.session) {
        redirectToLogin();
        return null;
      }
      _accessToken = data.session.access_token;
      scheduleRefresh(data.session.expires_at);
      return _accessToken;
    } catch {
      redirectToLogin();
      return null;
    }
  }

  // ----- session bootstrap + listener -----
  async function bootstrap() {
    try {
      const { data: { session } } = await window.SB.client.auth.getSession();
      if (session) {
        _accessToken = session.access_token;
        sessionStorage.setItem(FLAG_KEY, '1');
        scheduleRefresh(session.expires_at);
        _markReady({ authenticated: true, session });
      } else {
        _markReady({ authenticated: false });
        if (!isPublicPage()) redirectToLogin();
      }
    } catch {
      _markReady({ authenticated: false });
      if (!isPublicPage()) redirectToLogin();
    }
  }

  // Guardia para rutas protegidas: await hasta que bootstrap termine y devuelve
  // true si hay sesión; si no, dispara redirect y lanza para que el caller
  // pueda cortar su propia inicialización.
  async function requireAuth() {
    const result = await _readyPromise;
    if (!result.authenticated) {
      redirectToLogin();
      throw new Error('requireAuth: no hay sesión');
    }
    return true;
  }

  window.SB.client.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_OUT' || !session) {
      _markReady({ authenticated: false });
      redirectToLogin();
      return;
    }
    // SIGNED_IN, TOKEN_REFRESHED, USER_UPDATED, INITIAL_SESSION
    _accessToken = session.access_token;
    sessionStorage.setItem(FLAG_KEY, '1');
    scheduleRefresh(session.expires_at);
    _markReady({ authenticated: true, session });
  });

  // ----- API pública -----
  async function getAccessToken() {
    if (_accessToken) return _accessToken;
    const { data: { session } } = await window.SB.client.auth.getSession();
    if (!session) return null;
    _accessToken = session.access_token;
    scheduleRefresh(session.expires_at);
    return _accessToken;
  }

  async function authFetch(url, options = {}) {
    let token = await getAccessToken();
    if (!token) {
      redirectToLogin();
      throw new Error('No hay sesión activa');
    }

    function buildInit(tk) {
      const headers = new Headers(options.headers || {});
      headers.set('Authorization', 'Bearer ' + tk);
      return { ...options, headers };
    }

    let resp = await fetch(url, buildInit(token));

    // Si el access token expiró justo en este request, intentar refresh + retry UNA vez.
    if (resp.status === 401) {
      token = await doRefresh();
      if (!token) return resp; // redirect ya disparado
      resp = await fetch(url, buildInit(token));
    }

    return resp;
  }

  async function logout() {
    try { await window.SB.signOut(); } catch { /* ignore */ }
    redirectToLogin();
  }

  function isAuthenticatedHint() {
    return sessionStorage.getItem(FLAG_KEY) === '1';
  }

  window.REAuthService = {
    getAccessToken,
    authFetch,
    logout,
    isAuthenticatedHint,
    requireAuth,
    ready: _readyPromise,
    isPublicPage,
    PUBLIC_ROUTES: PUBLIC_ROUTES.slice(),
    // expuesto para testing / debugging
    _bootstrap: bootstrap,
  };

  // Auto-bootstrap al cargar.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
