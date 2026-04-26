// authService.js — Frontend session management
//
// Responsabilidades:
//   - Mantener el access token JWT (backend) en memoria + localStorage.
//   - Agendar auto-refresh ~60s antes de que expire.
//   - Exponer authFetch(url, opts) que inyecta Authorization: Bearer <token>
//     y retry automático si el backend responde 401.
//   - Redirigir a /login si no hay sesión o el refresh falla.
//   - Flag booleano en sessionStorage ("re_authed") para poder chequear
//     estado sin pagar un await en cada página.

(function () {
  const LOGIN_URL = 'login.html';
  const FLAG_KEY = 're_authed';
  const STORAGE_ACCESS = 're_access_token';
  const STORAGE_REFRESH = 're_refresh_token';
  const STORAGE_USER = 're_user';
  const REFRESH_LEAD_MS = 60_000;

  const PUBLIC_ROUTES = [
    '/login.html',
    '/register.html',
    '/forgot-password.html',
    '/pricing.html',
    '/success.html',
  ];

  let _accessToken = null;
  let _refreshTimer = null;

  let _readyResolve;
  const _readyPromise = new Promise((r) => { _readyResolve = r; });
  let _readyResolved = false;

  function _markReady(value) {
    if (_readyResolved) return;
    _readyResolved = true;
    _readyResolve(value);
  }

  function isPublicPage() {
    const p = (window.location.pathname || '').toLowerCase();
    return PUBLIC_ROUTES.some((r) => p.endsWith(r));
  }
  const isAuthPage = isPublicPage;

  function redirectToLogin() {
    sessionStorage.removeItem(FLAG_KEY);
    localStorage.removeItem(STORAGE_ACCESS);
    localStorage.removeItem(STORAGE_REFRESH);
    localStorage.removeItem(STORAGE_USER);
    _accessToken = null;
    if (_refreshTimer) { clearTimeout(_refreshTimer); _refreshTimer = null; }
    if (isAuthPage()) return;
    window.location.replace(LOGIN_URL);
  }

  function _parseJwtPayload(token) {
    try {
      const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(base64));
    } catch {
      return null;
    }
  }

  function _isTokenExpired(token) {
    const payload = _parseJwtPayload(token);
    if (!payload || !payload.exp) return true;
    return Date.now() >= payload.exp * 1000;
  }

  function _apiBase() {
    return (window.RE_CONFIG && window.RE_CONFIG.API_BASE) || '';
  }

  function scheduleRefresh(expiresAtSec) {
    if (_refreshTimer) clearTimeout(_refreshTimer);
    if (!expiresAtSec) return;
    const msUntil = (expiresAtSec * 1000) - Date.now() - REFRESH_LEAD_MS;
    if (msUntil <= 0) {
      doRefresh();
      return;
    }
    _refreshTimer = setTimeout(doRefresh, msUntil);
  }

  async function doRefresh() {
    const refreshToken = localStorage.getItem(STORAGE_REFRESH);
    if (!refreshToken) {
      redirectToLogin();
      return null;
    }
    try {
      const resp = await fetch(_apiBase() + '/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!resp.ok) {
        redirectToLogin();
        return null;
      }
      const data = await resp.json();
      _storeSession(data.access_token, data.refresh_token, data.user || null);
      return data.access_token;
    } catch {
      redirectToLogin();
      return null;
    }
  }

  function _storeSession(accessToken, refreshToken, user) {
    _accessToken = accessToken;
    localStorage.setItem(STORAGE_ACCESS, accessToken);
    if (refreshToken) localStorage.setItem(STORAGE_REFRESH, refreshToken);
    if (user) localStorage.setItem(STORAGE_USER, JSON.stringify(user));
    sessionStorage.setItem(FLAG_KEY, '1');
    const payload = _parseJwtPayload(accessToken);
    if (payload && payload.exp) scheduleRefresh(payload.exp);
  }

  async function bootstrap() {
    try {
      const storedAccess = localStorage.getItem(STORAGE_ACCESS);
      const storedRefresh = localStorage.getItem(STORAGE_REFRESH);

      if (!storedAccess || !storedRefresh) {
        _markReady({ authenticated: false });
        if (!isPublicPage()) redirectToLogin();
        return;
      }

      if (!_isTokenExpired(storedAccess)) {
        _accessToken = storedAccess;
        sessionStorage.setItem(FLAG_KEY, '1');
        const payload = _parseJwtPayload(storedAccess);
        if (payload && payload.exp) scheduleRefresh(payload.exp);
        _markReady({ authenticated: true });
        return;
      }

      // Token expirado — intentar refresh
      const newToken = await doRefresh();
      if (newToken) {
        _markReady({ authenticated: true });
      } else {
        _markReady({ authenticated: false });
        if (!isPublicPage()) redirectToLogin();
      }
    } catch {
      _markReady({ authenticated: false });
      if (!isPublicPage()) redirectToLogin();
    }
  }

  async function requireAuth() {
    const result = await _readyPromise;
    if (!result.authenticated) {
      redirectToLogin();
      throw new Error('requireAuth: no hay sesión');
    }
    return true;
  }

  async function getAccessToken() {
    if (_accessToken && !_isTokenExpired(_accessToken)) return _accessToken;
    const stored = localStorage.getItem(STORAGE_ACCESS);
    if (stored && !_isTokenExpired(stored)) {
      _accessToken = stored;
      return _accessToken;
    }
    return await doRefresh();
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

    // Si el access token expiró justo en este request, retry una vez.
    if (resp.status === 401) {
      token = await doRefresh();
      if (!token) return resp;
      resp = await fetch(url, buildInit(token));
    }

    return resp;
  }

  async function logout() {
    localStorage.removeItem(STORAGE_ACCESS);
    localStorage.removeItem(STORAGE_REFRESH);
    localStorage.removeItem(STORAGE_USER);
    sessionStorage.removeItem(FLAG_KEY);
    _accessToken = null;
    if (_refreshTimer) { clearTimeout(_refreshTimer); _refreshTimer = null; }
    redirectToLogin();
  }

  function isAuthenticatedHint() {
    return sessionStorage.getItem(FLAG_KEY) === '1';
  }

  function getStoredUser() {
    try {
      const raw = localStorage.getItem(STORAGE_USER);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  window.REAuthService = {
    getAccessToken,
    authFetch,
    logout,
    isAuthenticatedHint,
    requireAuth,
    getStoredUser,
    ready: _readyPromise,
    isPublicPage,
    PUBLIC_ROUTES: PUBLIC_ROUTES.slice(),
    _bootstrap: bootstrap,
    // Expuesto para que auth.js guarde sesión al loguearse
    _storeSession,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
