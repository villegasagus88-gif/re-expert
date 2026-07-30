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

  // ── Multi-cuenta (estilo ChatGPT) ─────────────────────────────────────────
  // La sesión ACTIVA sigue viviendo en las 3 claves de arriba, exactamente como
  // antes: todo el código que ya existe (app.html, admin*, account, pricing…)
  // no se entera de nada. Acá solo se guarda un ROSTER extra de las cuentas que
  // el usuario dejó agregadas, para poder cambiar entre ellas sin re-loguearse.
  const STORAGE_ACCOUNTS = 're_accounts';
  // Datos que el asistente de voz guarda A PEDIDO del usuario (nombre, zona,
  // preferencias). Es contenido personal, no una preferencia de interfaz: tiene
  // que irse al cerrar sesión, sobre todo en computadoras compartidas.
  const STORAGE_VOZ = 're_voice_memory';
  const MAX_ACCOUNTS = 5;

  function _readAccounts() {
    try {
      const raw = localStorage.getItem(STORAGE_ACCOUNTS);
      const arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr.filter(a => a && a.email && a.refresh) : [];
    } catch { return []; }
  }

  function _writeAccounts(list) {
    try {
      localStorage.setItem(STORAGE_ACCOUNTS, JSON.stringify(list.slice(0, MAX_ACCOUNTS)));
    } catch { /* storage lleno o bloqueado: multi-cuenta es opcional, no rompe nada */ }
  }

  function _accountKey(user, email) {
    return String((user && user.id) || email || '').toLowerCase();
  }

  /** Registra (o actualiza) la cuenta en el roster y la marca como activa. */
  function _rememberAccount(accessToken, refreshToken, user) {
    const email = (user && user.email) || '';
    if (!email || !refreshToken) return;          // sin refresh no se puede volver
    const key = _accountKey(user, email);
    const list = _readAccounts().filter(a => a.key !== key);
    list.unshift({
      key,
      email,
      name: (user && user.full_name) || '',
      refresh: refreshToken,
      access: accessToken || '',
      savedAt: Date.now(),
    });
    _writeAccounts(list);
  }

  /** Saca una cuenta del roster (por key). Devuelve el roster resultante. */
  function _forgetAccount(key) {
    const list = _readAccounts().filter(a => a.key !== key);
    _writeAccounts(list);
    return list;
  }

  /** Key de la cuenta que está activa ahora (según re_user). */
  function _currentKey() {
    try {
      const u = JSON.parse(localStorage.getItem(STORAGE_USER) || 'null');
      return u ? _accountKey(u, u.email) : '';
    } catch { return ''; }
  }

  // Solo nombres base. isPublicPage() acepta tanto "/login" como "/login.html"
  // (Netlify Pretty URLs rewrites internal links a la forma sin extensión).
  const PUBLIC_ROUTES = [
    'login',
    'register',
    'forgot-password',
    'reset-password',
    'pricing',
    'success',
  ];

  let _accessToken = null;
  let _refreshTimer = null;
  let _logoutEnCurso = null;   // guard de reentrada de logout() (ver abajo)

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
    return PUBLIC_ROUTES.some((name) => {
      return (
        p.endsWith('/' + name) ||
        p.endsWith('/' + name + '.html') ||
        p.endsWith('/' + name + '/')
      );
    });
  }
  const isAuthPage = isPublicPage;

  function redirectToLogin() {
    // Multi-cuenta: la sesión que expiró sale del roster (su refresh ya no
    // sirve), pero las OTRAS cuentas guardadas se conservan. Sin esto, vencer
    // una sesión borraba todas las cuentas del usuario.
    const key = _currentKey();
    if (key) _forgetAccount(key);
    sessionStorage.removeItem(FLAG_KEY);
    localStorage.removeItem(STORAGE_ACCESS);
    localStorage.removeItem(STORAGE_REFRESH);
    localStorage.removeItem(STORAGE_USER);
    localStorage.removeItem(STORAGE_VOZ);
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

  // Single-flight: en el arranque frío, bootstrap() + los 4 authFetch del
  // Promise.all inicial pueden disparar hasta 5 refresh concurrentes con el
  // mismo refresh_token contra un backend frío. Coalescemos todos en UNA sola
  // request. (Además blinda para el día que haya rotación single-use de refresh:
  // hoy los 4 extra devolverían 401 y desloguearían al usuario.)
  let _refreshInFlight = null;
  function doRefresh() {
    if (_refreshInFlight) return _refreshInFlight;
    _refreshInFlight = _doRefreshImpl().finally(() => { _refreshInFlight = null; });
    return _refreshInFlight;
  }

  async function _doRefreshImpl() {
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
        // Solo un rechazo REAL del token (401/400/403) invalida la sesión.
        // Un 5xx/429 transitorio (deploy, rate limit, hipo del server) NO
        // debe desloguear al usuario ni borrar su refresh token: se reintenta
        // en ~30s y la sesión sobrevive.
        if (resp.status === 400 || resp.status === 401 || resp.status === 403) {
          redirectToLogin();
          return null;
        }
        if (_refreshTimer) clearTimeout(_refreshTimer);
        _refreshTimer = setTimeout(doRefresh, 30000);
        return null;
      }
      const data = await resp.json();
      _storeSession(data.access_token, data.refresh_token, data.user || null);
      return data.access_token;
    } catch {
      // Error de red (offline, DNS): conservar la sesión y reintentar.
      if (_refreshTimer) clearTimeout(_refreshTimer);
      _refreshTimer = setTimeout(doRefresh, 30000);
      return null;
    }
  }

  function _storeSession(accessToken, refreshToken, user) {
    _accessToken = accessToken;
    localStorage.setItem(STORAGE_ACCESS, accessToken);
    if (refreshToken) localStorage.setItem(STORAGE_REFRESH, refreshToken);
    if (user) localStorage.setItem(STORAGE_USER, JSON.stringify(user));
    // Multi-cuenta: además de la sesión activa (arriba, sin cambios), dejamos
    // registrada la cuenta para poder volver a ella sin re-loguearse.
    _rememberAccount(accessToken, refreshToken || localStorage.getItem(STORAGE_REFRESH), user);
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

    // Modelo pago-only: un 403 con detalle de paywall (trial vencido / sin
    // suscripción) avisa a la UI vía evento, sin romper el flujo del caller.
    if (resp.status === 403) {
      try {
        const body = await resp.clone().json();
        const d = body && body.detail;
        if (d && (d.upgrade_url || d.reason)) {
          window.dispatchEvent(new CustomEvent('re:paywall', { detail: d }));
        }
      } catch (_) { /* no era JSON de paywall */ }
    }

    return resp;
  }

  /**
   * Cierra la sesión de la cuenta ACTUAL (decisión de producto, estilo ChatGPT).
   * Si quedan otras cuentas guardadas, cambia a la más reciente en vez de
   * mandar al login. Con una sola cuenta, se comporta igual que siempre.
   */
  async function logout() {
    // Guard de reentrada: varios 401 en paralelo (p.ej. el Promise.all de
    // loaders al abrir la app) llaman logout() casi a la vez. Sin esto se
    // dispararían N cambios de cuenta y N reloads. El primero manda.
    if (_logoutEnCurso) return _logoutEnCurso;
    _logoutEnCurso = (async () => {
    const key = _currentKey();
    const quedan = key ? _forgetAccount(key) : _readAccounts();
    localStorage.removeItem(STORAGE_ACCESS);
    localStorage.removeItem(STORAGE_REFRESH);
    localStorage.removeItem(STORAGE_USER);
    localStorage.removeItem(STORAGE_VOZ);
    sessionStorage.removeItem(FLAG_KEY);
    _accessToken = null;
    if (_refreshTimer) { clearTimeout(_refreshTimer); _refreshTimer = null; }
    if (quedan.length) {
      const ok = await switchAccount(quedan[0].key);   // recarga si sale bien
      if (ok) return;
    }
    redirectToLogin();
    })();
    return _logoutEnCurso;
  }

  /** Cierra TODAS las cuentas guardadas y va al login. */
  async function logoutAll() {
    _writeAccounts([]);
    localStorage.removeItem(STORAGE_ACCOUNTS);
    localStorage.removeItem(STORAGE_ACCESS);
    localStorage.removeItem(STORAGE_REFRESH);
    localStorage.removeItem(STORAGE_USER);
    localStorage.removeItem(STORAGE_VOZ);
    sessionStorage.removeItem(FLAG_KEY);
    _accessToken = null;
    if (_refreshTimer) { clearTimeout(_refreshTimer); _refreshTimer = null; }
    if (!isAuthPage()) window.location.replace(LOGIN_URL);
  }

  /** Cuentas guardadas, con `current:true` en la activa. */
  function listAccounts() {
    const cur = _currentKey();
    return _readAccounts().map(a => ({
      key: a.key, email: a.email, name: a.name || '', current: a.key === cur,
    }));
  }

  /**
   * Cambia a otra cuenta guardada: canjea su refresh token por una sesión nueva
   * y RECARGA la página (garantiza que no quede en pantalla ningún dato de la
   * cuenta anterior: chats, proyectos, memoria). Devuelve false si no pudo.
   */
  async function switchAccount(key) {
    const acc = _readAccounts().find(a => a.key === key);
    if (!acc) return false;
    if (key === _currentKey()) return true;          // ya estás en esa cuenta
    try {
      const resp = await fetch(_apiBase() + '/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: acc.refresh }),
      });
      if (!resp.ok) {                                 // refresh vencido/revocado
        _forgetAccount(key);
        return false;
      }
      const data = await resp.json();
      _storeSession(data.access_token, data.refresh_token || acc.refresh, data.user || null);
      window.location.reload();
      return true;
    } catch {
      return false;                                   // red caída: no tocamos nada
    }
  }

  /** Saca una cuenta guardada (sin tocar la sesión activa, salvo que sea ella). */
  async function removeAccount(key) {
    if (key === _currentKey()) return logout();
    _forgetAccount(key);
    return true;
  }

  /**
   * "Añadir cuenta": va al login conservando el roster. Al loguearse, la nueva
   * queda registrada y activa (lo hace _storeSession).
   */
  function addAccount() {
    window.location.href = LOGIN_URL + '?add=1';
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
    // Multi-cuenta (aditivo: nada de lo de arriba cambió de firma)
    logoutAll,
    listAccounts,
    switchAccount,
    removeAccount,
    addAccount,
    MAX_ACCOUNTS,
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
