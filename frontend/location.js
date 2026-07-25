// ════════════════════════════════════════════════════════════════════
// RELocation — módulo de geolocalización de RE Expert.
// ════════════════════════════════════════════════════════════════════
// Standalone y autocontenido: NO toca app.html ni ningún otro archivo.
// Para usarlo, la página que lo necesite lo incluye con:
//     <script src="location.js"></script>
// (después de authService.js — usa REAuthService.authFetch para hablar
//  con el backend). Expone window.RELocation.
//
// API pública:
//   RELocation.isSupported()                  → bool
//   RELocation.permissionState()              → Promise<'granted'|'prompt'|'denied'|'unsupported'>
//   RELocation.getConsent()                   → Promise<{consent, precision, consent_updated_at}>
//   RELocation.setConsent(consent, precision) → Promise<idem>  (consent: 'granted'|'denied')
//   RELocation.captureOnce(opts)              → Promise<fix>   (pide permiso al browser si hace falta)
//   RELocation.startWatch(opts)               → id de watch    (tracking continuo con throttle)
//   RELocation.stopWatch()                    → void
//   RELocation.getLatest(opts)                → Promise<fix|null>  (cache 5 min + backend)
//   RELocation.purge()                        → Promise<{deleted}> (borra todo el historial server-side)
//
// Privacidad:
//   - El backend NO acepta fixes sin consent 'granted' (403) — setConsent primero.
//   - En precision 'coarse' el server redondea a ~1.1 km antes de guardar.
//   - Cache local en sessionStorage (muere al cerrar la pestaña), nunca localStorage.
//   - Cero console.log de coordenadas.
// ════════════════════════════════════════════════════════════════════
(function () {
  'use strict';

  var CACHE_KEY = 're_loc_last';          // sessionStorage — efímero por diseño
  var CACHE_TTL_MS = 5 * 60 * 1000;       // 5 min
  var DEFAULT_MIN_INTERVAL_MS = 30 * 1000; // watch: no reportar más seguido que esto
  var DEFAULT_MIN_DELTA_M = 25;            // watch: ni si se movió menos que esto

  var _watchId = null;
  var _lastReported = null; // {lat, lon, t} para throttle del watch

  function _api() {
    return (window.RE_CONFIG && window.RE_CONFIG.API_BASE) || '';
  }

  function _authFetch(url, opts) {
    if (!window.REAuthService || !window.REAuthService.authFetch) {
      return Promise.reject(new Error('RELocation: sesión no inicializada (falta authService.js)'));
    }
    return window.REAuthService.authFetch(_api() + url, opts);
  }

  async function _jsonOrThrow(resp) {
    if (!resp.ok) {
      var detail = '';
      try {
        var e = await resp.json();
        detail = typeof e.detail === 'object' ? (e.detail.message || JSON.stringify(e.detail)) : (e.detail || '');
      } catch (_ignored) { /* body no-JSON */ }
      var err = new Error(detail || ('HTTP ' + resp.status));
      err.status = resp.status;
      throw err;
    }
    return resp.json();
  }

  // Haversine en metros — para el throttle por distancia del watch.
  function _distanceM(lat1, lon1, lat2, lon2) {
    var R = 6371008.8;
    var toRad = function (d) { return d * Math.PI / 180; };
    var dp = toRad(lat2 - lat1);
    var dl = toRad(lon2 - lon1);
    var a = Math.sin(dp / 2) * Math.sin(dp / 2) +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  function _positionToFix(pos) {
    var c = pos.coords;
    return {
      lat: c.latitude,
      lon: c.longitude,
      accuracy_m: (typeof c.accuracy === 'number' && isFinite(c.accuracy)) ? c.accuracy : null,
      altitude_m: (typeof c.altitude === 'number' && isFinite(c.altitude)) ? c.altitude : null,
      heading_deg: (typeof c.heading === 'number' && isFinite(c.heading)) ? c.heading : null,
      speed_mps: (typeof c.speed === 'number' && isFinite(c.speed)) ? c.speed : null,
      // GeolocationPosition.timestamp es epoch ms del momento del fix.
      captured_at: new Date(pos.timestamp).toISOString(),
      source: 'gps'
    };
  }

  function _cacheSet(fix) {
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), fix: fix }));
    } catch (_ignored) { /* storage lleno/bloqueado: el cache es best-effort */ }
  }

  function _cacheGet(maxAgeMs) {
    try {
      var raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      var entry = JSON.parse(raw);
      if (Date.now() - entry.t > (maxAgeMs || CACHE_TTL_MS)) return null;
      return entry.fix;
    } catch (_ignored) {
      return null;
    }
  }

  // ── Capacidades del browser ─────────────────────────────────────────
  function isSupported() {
    return typeof navigator !== 'undefined' && 'geolocation' in navigator;
  }

  async function permissionState() {
    if (!isSupported()) return 'unsupported';
    // Permissions API no está en todos los browsers (Safari viejo) → 'prompt'
    // como default conservador: no sabemos hasta intentar.
    if (!navigator.permissions || !navigator.permissions.query) return 'prompt';
    try {
      var st = await navigator.permissions.query({ name: 'geolocation' });
      return st.state; // 'granted' | 'prompt' | 'denied'
    } catch (_ignored) {
      return 'prompt';
    }
  }

  // ── Consentimiento (backend) ────────────────────────────────────────
  async function getConsent() {
    return _jsonOrThrow(await _authFetch('/api/location/consent'));
  }

  async function setConsent(consent, precision) {
    return _jsonOrThrow(await _authFetch('/api/location/consent', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consent: consent, precision: precision || 'exact' })
    }));
  }

  // ── Captura ─────────────────────────────────────────────────────────
  function _getCurrentPosition(opts) {
    return new Promise(function (resolve, reject) {
      if (!isSupported()) {
        reject(new Error('Geolocalización no soportada en este dispositivo'));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, function (err) {
        // Traducimos el código a un mensaje accionable, sin filtrar coords.
        var msg =
          err.code === 1 ? 'Permiso de ubicación denegado por el usuario' :
          err.code === 2 ? 'Ubicación no disponible (sin señal GPS/red)' :
          err.code === 3 ? 'Timeout esperando la ubicación' :
          'Error de geolocalización';
        var e = new Error(msg);
        e.code = err.code;
        reject(e);
      }, {
        enableHighAccuracy: opts.highAccuracy !== false,
        timeout: opts.timeoutMs || 15000,
        maximumAge: opts.maximumAgeMs || 0
      });
    });
  }

  async function _report(fix) {
    var stored = await _jsonOrThrow(await _authFetch('/api/location/fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fix)
    }));
    return stored;
  }

  /**
   * Captura la ubicación actual una vez.
   * opts: {report=true, highAccuracy=true, timeoutMs=15000, maximumAgeMs=0}
   * Devuelve el fix local; si report=true incluye `stored` (lo que guardó el
   * backend, ya con la precisión del usuario aplicada).
   */
  async function captureOnce(opts) {
    opts = opts || {};
    var pos = await _getCurrentPosition(opts);
    var fix = _positionToFix(pos);
    _cacheSet(fix);
    if (opts.report === false) return { fix: fix, stored: null };
    var stored = await _report(fix);
    return { fix: fix, stored: stored };
  }

  /**
   * Tracking continuo con doble throttle (tiempo Y distancia) para no
   * spamear el backend ni la batería.
   * opts: {minIntervalMs=30000, minDeltaM=25, report=true, highAccuracy=true,
   *        onFix(fix, stored), onError(err)}
   */
  function startWatch(opts) {
    opts = opts || {};
    if (!isSupported()) throw new Error('Geolocalización no soportada');
    if (_watchId !== null) stopWatch();
    var minInterval = opts.minIntervalMs || DEFAULT_MIN_INTERVAL_MS;
    var minDelta = (typeof opts.minDeltaM === 'number') ? opts.minDeltaM : DEFAULT_MIN_DELTA_M;

    _watchId = navigator.geolocation.watchPosition(function (pos) {
      var fix = _positionToFix(pos);
      var now = Date.now();
      if (_lastReported) {
        var tooSoon = (now - _lastReported.t) < minInterval;
        var tooClose = _distanceM(_lastReported.lat, _lastReported.lon, fix.lat, fix.lon) < minDelta;
        if (tooSoon || tooClose) return; // throttle: ni tiempo ni distancia suficientes
      }
      _lastReported = { lat: fix.lat, lon: fix.lon, t: now };
      _cacheSet(fix);
      if (opts.report === false) {
        if (opts.onFix) opts.onFix(fix, null);
        return;
      }
      _report(fix).then(function (stored) {
        if (opts.onFix) opts.onFix(fix, stored);
      }).catch(function (err) {
        if (opts.onError) opts.onError(err);
      });
    }, function (err) {
      if (opts.onError) opts.onError(err);
    }, {
      enableHighAccuracy: opts.highAccuracy !== false,
      timeout: opts.timeoutMs || 20000,
      maximumAge: 5000
    });
    return _watchId;
  }

  function stopWatch() {
    if (_watchId !== null && isSupported()) {
      navigator.geolocation.clearWatch(_watchId);
    }
    _watchId = null;
    _lastReported = null;
  }

  // ── Lectura ─────────────────────────────────────────────────────────
  /**
   * Última ubicación conocida: primero cache de sesión (TTL 5 min),
   * después el backend. opts: {maxAgeMs, skipCache}
   */
  async function getLatest(opts) {
    opts = opts || {};
    if (!opts.skipCache) {
      var cached = _cacheGet(opts.maxAgeMs);
      if (cached) return { source: 'cache', fix: cached };
    }
    var data = await _jsonOrThrow(await _authFetch('/api/location/me'));
    if (!data.found) return null;
    return { source: 'backend', fix: data.fix };
  }

  async function purge() {
    try { sessionStorage.removeItem(CACHE_KEY); } catch (_ignored) { /* best-effort */ }
    return _jsonOrThrow(await _authFetch('/api/location/me', { method: 'DELETE' }));
  }

  // ── Export ──────────────────────────────────────────────────────────
  window.RELocation = {
    isSupported: isSupported,
    permissionState: permissionState,
    getConsent: getConsent,
    setConsent: setConsent,
    captureOnce: captureOnce,
    startWatch: startWatch,
    stopWatch: stopWatch,
    getLatest: getLatest,
    purge: purge
  };
})();
