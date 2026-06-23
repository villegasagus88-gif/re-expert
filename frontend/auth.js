// Auth pages shared helpers (login + register)
// Usa los endpoints del backend (/api/auth/login, /api/auth/register).

(function () {
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function byId(id) { return document.getElementById(id); }

  function setInputInvalid(input, isInvalid) {
    input.classList.toggle('is-invalid', isInvalid);
  }

  function setInputError(inputId, message) {
    const input = byId(inputId);
    const err = byId(inputId + '-error');
    if (!input) return;
    if (message) {
      setInputInvalid(input, true);
      if (err) { err.textContent = message; err.classList.add('is-visible'); }
    } else {
      setInputInvalid(input, false);
      if (err) { err.textContent = ''; err.classList.remove('is-visible'); }
    }
  }

  function clearAllErrors(formId) {
    const form = byId(formId);
    if (!form) return;
    form.querySelectorAll('.form-input.is-invalid').forEach(i => i.classList.remove('is-invalid'));
    form.querySelectorAll('.form-error').forEach(e => { e.textContent = ''; e.classList.remove('is-visible'); });
    hideAlert();
  }

  function showAlert(message, variant) {
    const el = byId('auth-alert');
    if (!el) return;
    el.textContent = message;
    el.className = 'alert is-visible alert-' + (variant || 'error');
  }

  function hideAlert() {
    const el = byId('auth-alert');
    if (!el) return;
    el.className = 'alert';
    el.textContent = '';
  }

  function setLoading(btnId, isLoading) {
    const btn = byId(btnId);
    if (!btn) return;
    btn.disabled = !!isLoading;
    btn.classList.toggle('is-loading', !!isLoading);
  }

  function validateEmail(email) {
    if (!email) return 'Ingresá tu email';
    if (!EMAIL_RE.test(email)) return 'Formato de email inválido';
    return null;
  }

  function validatePassword(password, { minLen = 8 } = {}) {
    if (!password) return 'Ingresá tu contraseña';
    if (password.length < minLen) return `La contraseña debe tener al menos ${minLen} caracteres`;
    return null;
  }

  function validatePasswordStrength(password) {
    const basic = validatePassword(password);
    if (basic) return basic;
    if (!/[A-Z]/.test(password)) return 'Debe contener al menos una letra mayúscula';
    if (!/[0-9]/.test(password)) return 'Debe contener al menos un número';
    return null;
  }

  function validateName(name) {
    if (!name || !name.trim()) return 'Ingresá tu nombre';
    if (name.trim().length < 2) return 'El nombre es muy corto';
    return null;
  }

  function _apiBase() {
    return (window.RE_CONFIG && window.RE_CONFIG.API_BASE) || '';
  }

  function _parseJwtPayload(token) {
    try {
      const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(base64));
    } catch {
      return null;
    }
  }

  // Si el usuario llegó al login/register vía ?redirect=foo.html (desde
  // pricing.html o account.html), volvemos ahí post-login. Si no, va al
  // app principal. Solo aceptamos rutas relativas mismas-origen para
  // evitar open redirect.
  function _postAuthDestination() {
    const params = new URLSearchParams(window.location.search);
    const r = params.get('redirect');
    if (!r) return 'app.html';
    // Aceptar solo "foo.html" o "foo.html?bar=baz" relativos.
    if (/^[a-z0-9_\-]+\.html(\?.*)?$/i.test(r)) return r;
    return 'app.html';
  }

  // ===== Redirect post-login =====
  // Solo redirige a app.html si el backend confirma que la sesión es válida.
  // No alcanza con que el JWT no esté vencido localmente: la firma puede haber
  // dejado de ser válida (rotación del secreto de firma, deploy nuevo, etc.). Si ese
  // es el caso, limpiamos los tokens viejos y dejamos al usuario usar la
  // página de login/register normalmente.
  function _clearStaleSession() {
    localStorage.removeItem('re_access_token');
    localStorage.removeItem('re_refresh_token');
    localStorage.removeItem('re_user');
    sessionStorage.removeItem('re_authed');
  }

  async function redirectIfAuthenticated() {
    const stored = localStorage.getItem('re_access_token');
    if (!stored) return;
    const payload = _parseJwtPayload(stored);
    if (!payload || !payload.exp || Date.now() >= payload.exp * 1000) {
      _clearStaleSession();
      return;
    }
    try {
      const resp = await fetch(_apiBase() + '/api/auth/me', {
        headers: { 'Authorization': 'Bearer ' + stored },
      });
      if (resp.ok) {
        window.location.replace(_postAuthDestination());
        return;
      }
      if (resp.status === 401 || resp.status === 403) {
        _clearStaleSession();
        return;
      }
      // Cualquier otra respuesta (5xx, red, etc.) — nos quedamos en la página
      // actual sin tocar la sesión, así el usuario puede reintentar.
    } catch {
      // Backend inalcanzable: nos quedamos en la página, no redirigimos.
    }
  }

  // ===== LOGIN =====
  async function handleLogin(event) {
    event.preventDefault();
    clearAllErrors('login-form');

    const email = byId('email').value.trim();
    const password = byId('password').value;

    const emailErr = validateEmail(email);
    const passErr = validatePassword(password);
    if (emailErr) setInputError('email', emailErr);
    if (passErr) setInputError('password', passErr);
    if (emailErr || passErr) return;

    setLoading('submit-btn', true);
    try {
      const resp = await fetch(_apiBase() + '/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (resp.status === 401) {
        showAlert('Email o contraseña incorrectos.');
        return;
      }
      if (resp.status === 429) {
        showAlert('Demasiados intentos. Esperá unos minutos antes de volver a probar.');
        return;
      }
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        showAlert(data.detail || 'Error al iniciar sesión. Intentá de nuevo.');
        return;
      }

      const data = await resp.json();
      if (window.REAuthService && window.REAuthService._storeSession) {
        window.REAuthService._storeSession(data.access_token, data.refresh_token, data.user || null);
      } else {
        localStorage.setItem('re_access_token', data.access_token);
        localStorage.setItem('re_refresh_token', data.refresh_token);
        if (data.user) localStorage.setItem('re_user', JSON.stringify(data.user));
        sessionStorage.setItem('re_authed', '1');
      }
      window.location.replace(_postAuthDestination());
    } catch {
      showAlert('No pudimos conectarnos. Verificá tu conexión e intentá de nuevo.');
    } finally {
      setLoading('submit-btn', false);
    }
  }

  // ===== REGISTER =====
  async function handleRegister(event) {
    event.preventDefault();
    clearAllErrors('register-form');

    const fullName = byId('fullName').value;
    const email = byId('email').value.trim();
    const password = byId('password').value;

    const nameErr = validateName(fullName);
    const emailErr = validateEmail(email);
    const passErr = validatePasswordStrength(password);
    if (nameErr) setInputError('fullName', nameErr);
    if (emailErr) setInputError('email', emailErr);
    if (passErr) setInputError('password', passErr);
    if (nameErr || emailErr || passErr) return;

    setLoading('submit-btn', true);
    try {
      const resp = await fetch(_apiBase() + '/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName.trim() }),
      });

      if (resp.status === 409) {
        showAlert('Ya existe una cuenta con ese email. Probá iniciar sesión.');
        return;
      }
      if (resp.status === 429) {
        showAlert('Demasiados intentos. Esperá unos minutos antes de volver a probar.');
        return;
      }
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        showAlert(data.detail || 'Error al registrarse. Intentá de nuevo.');
        return;
      }

      const data = await resp.json();
      if (window.REAuthService && window.REAuthService._storeSession) {
        window.REAuthService._storeSession(data.access_token, data.refresh_token, data.user || null);
      } else {
        localStorage.setItem('re_access_token', data.access_token);
        localStorage.setItem('re_refresh_token', data.refresh_token);
        if (data.user) localStorage.setItem('re_user', JSON.stringify(data.user));
        sessionStorage.setItem('re_authed', '1');
      }
      window.location.replace(_postAuthDestination());
    } catch {
      showAlert('No pudimos conectarnos. Verificá tu conexión e intentá de nuevo.');
    } finally {
      setLoading('submit-btn', false);
    }
  }

  // ===== FORGOT PASSWORD (en login.html) =====
  // Lleva al usuario al formulario de recuperación. La lógica de
  // forgot/reset vive en forgot-password.html y reset-password.html.
  function handleForgotPassword() {
    window.location.href = 'forgot-password.html';
  }

  // Handler del formulario de forgot-password.html (envía el mail).
  async function handleForgotSubmit(event) {
    event.preventDefault();
    clearAllErrors('forgot-form');

    const email = byId('email').value.trim();
    const emailErr = validateEmail(email);
    if (emailErr) { setInputError('email', emailErr); return; }

    setLoading('submit-btn', true);
    try {
      const resp = await fetch(_apiBase() + '/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (resp.status === 429) {
        showAlert('Demasiados intentos. Esperá unos minutos antes de volver a probar.');
        return;
      }
      // El backend siempre responde 200 si el email es válido (no leak).
      if (!resp.ok && resp.status !== 200) {
        const data = await resp.json().catch(() => ({}));
        showAlert(data.detail || 'Error al solicitar recuperación. Intentá de nuevo.');
        return;
      }
      showAlert(
        'Listo. Si el email está registrado, te enviamos un link para restablecer tu contraseña. Revisá tu bandeja de entrada (y spam).',
        'success'
      );
      byId('forgot-form').reset();
    } catch {
      showAlert('No pudimos conectarnos. Verificá tu conexión e intentá de nuevo.');
    } finally {
      setLoading('submit-btn', false);
    }
  }

  // Handler del formulario de reset-password.html (aplica nueva contraseña).
  async function handleResetSubmit(event) {
    event.preventDefault();
    clearAllErrors('reset-form');

    const password = byId('password').value;
    const confirm = byId('password-confirm').value;
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token') || '';

    if (!token) {
      showAlert('Link inválido. Volvé a pedir uno nuevo desde "Olvidé mi contraseña".');
      return;
    }

    const passErr = validatePasswordStrength(password);
    if (passErr) { setInputError('password', passErr); return; }
    if (password !== confirm) {
      setInputError('password-confirm', 'Las contraseñas no coinciden');
      return;
    }

    setLoading('submit-btn', true);
    try {
      const resp = await fetch(_apiBase() + '/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (resp.status === 400) {
        const data = await resp.json().catch(() => ({}));
        showAlert(data.detail || 'El link de recuperación no es válido o expiró.');
        return;
      }
      if (resp.status === 429) {
        showAlert('Demasiados intentos. Esperá unos minutos antes de volver a probar.');
        return;
      }
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        showAlert(data.detail || 'Error actualizando contraseña.');
        return;
      }
      showAlert('Contraseña actualizada. Redirigiendo al login…', 'success');
      setTimeout(() => { window.location.replace('login.html'); }, 1800);
    } catch {
      showAlert('No pudimos conectarnos. Verificá tu conexión e intentá de nuevo.');
    } finally {
      setLoading('submit-btn', false);
    }
  }

  // ===== TOGGLE VER/OCULTAR CONTRASEÑA =====
  // Inyecta un botón "ojo" en cada input de contraseña (login/register/reset),
  // sin tener que editar cada HTML. El error sigue mostrándose vía la clase
  // .is-visible (independiente de la estructura del DOM), así envolver el input
  // no rompe el mensaje de error.
  const _EYE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>';
  const _EYE_OFF = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-10-8-10-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 10 8 10 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

  function _initPasswordToggles() {
    document.querySelectorAll('input[type="password"]').forEach((input) => {
      if (input.dataset.pwToggle) return;
      input.dataset.pwToggle = '1';
      const wrap = document.createElement('div');
      wrap.className = 'input-wrap';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pw-toggle';
      btn.tabIndex = -1;  // no robar el foco del flujo de tabulación del form
      btn.setAttribute('aria-label', 'Mostrar contraseña');
      btn.innerHTML = _EYE;
      wrap.appendChild(btn);
      btn.addEventListener('click', () => {
        const show = input.getAttribute('type') === 'password';
        input.setAttribute('type', show ? 'text' : 'password');
        btn.innerHTML = show ? _EYE_OFF : _EYE;
        btn.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _initPasswordToggles);
  } else {
    _initPasswordToggles();
  }

  // Exports
  window.REAuth = {
    handleLogin,
    handleRegister,
    handleForgotPassword,
    handleForgotSubmit,
    handleResetSubmit,
    redirectIfAuthenticated,
    clearAllErrors,
  };
})();
