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
      if (err) err.textContent = message;
    } else {
      setInputInvalid(input, false);
      if (err) err.textContent = '';
    }
  }

  function clearAllErrors(formId) {
    const form = byId(formId);
    if (!form) return;
    form.querySelectorAll('.form-input.is-invalid').forEach(i => i.classList.remove('is-invalid'));
    form.querySelectorAll('.form-error').forEach(e => { e.textContent = ''; });
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

  // ===== Redirect post-login =====
  async function redirectIfAuthenticated() {
    const stored = localStorage.getItem('re_access_token');
    if (!stored) return;
    const payload = _parseJwtPayload(stored);
    if (payload && payload.exp && Date.now() < payload.exp * 1000) {
      window.location.replace('index.html');
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
      window.location.replace('index.html');
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
      window.location.replace('index.html');
    } catch {
      showAlert('No pudimos conectarnos. Verificá tu conexión e intentá de nuevo.');
    } finally {
      setLoading('submit-btn', false);
    }
  }

  // ===== FORGOT PASSWORD =====
  async function handleForgotPassword() {
    showAlert(
      'La recuperación de contraseña estará disponible próximamente. Contactá al soporte si necesitás acceso urgente.',
      'success'
    );
  }

  // Exports
  window.REAuth = {
    handleLogin,
    handleRegister,
    handleForgotPassword,
    redirectIfAuthenticated,
    clearAllErrors,
  };
})();
