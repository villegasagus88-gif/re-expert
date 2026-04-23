// Auth pages shared helpers (login + register)
// Asume que supabase-client.js ya cargó window.SB

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

  function validateName(name) {
    if (!name || !name.trim()) return 'Ingresá tu nombre';
    if (name.trim().length < 2) return 'El nombre es muy corto';
    return null;
  }

  // ===== Redirect post-login =====
  async function redirectIfAuthenticated() {
    try {
      const user = await window.SB.getUser();
      if (user) window.location.replace('index.html');
    } catch {
      // No autenticado — seguimos en la página
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
      const { error } = await window.SB.signIn(email, password);
      if (error) {
        showAlert(translateSupabaseError(error.message));
        return;
      }
      window.location.replace('index.html');
    } catch (e) {
      showAlert('No pudimos conectarnos. Intentá de nuevo en un momento.');
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
    const passErr = validatePassword(password);
    if (nameErr) setInputError('fullName', nameErr);
    if (emailErr) setInputError('email', emailErr);
    if (passErr) setInputError('password', passErr);
    if (nameErr || emailErr || passErr) return;

    setLoading('submit-btn', true);
    try {
      const { data, error } = await window.SB.signUp(email, password, fullName.trim());
      if (error) {
        showAlert(translateSupabaseError(error.message));
        return;
      }
      // Si Supabase devuelve session directamente → logueado: redirect.
      // Si no (email confirmation obligatoria), mostramos success + dejamos que el usuario vaya a login.
      if (data && data.session) {
        window.location.replace('index.html');
      } else {
        showAlert(
          'Cuenta creada. Revisá tu email para confirmar y después iniciá sesión.',
          'success'
        );
        byId('register-form').reset();
      }
    } catch (e) {
      showAlert('No pudimos conectarnos. Intentá de nuevo en un momento.');
    } finally {
      setLoading('submit-btn', false);
    }
  }

  // ===== FORGOT PASSWORD =====
  async function handleForgotPassword() {
    const email = (byId('email') && byId('email').value || '').trim();
    const target = email || window.prompt('Ingresá tu email para recuperar la contraseña:');
    if (!target) return;
    if (!EMAIL_RE.test(target)) {
      showAlert('Formato de email inválido');
      return;
    }
    try {
      const { error } = await window.SB.client.auth.resetPasswordForEmail(target, {
        redirectTo: window.location.origin + '/index.html',
      });
      if (error) {
        showAlert(translateSupabaseError(error.message));
        return;
      }
      showAlert(
        'Si esa cuenta existe, te enviamos un email con instrucciones para restablecer la contraseña.',
        'success'
      );
    } catch {
      showAlert('No pudimos enviar el email. Intentá de nuevo en un momento.');
    }
  }

  // Traduce los mensajes más comunes de Supabase al castellano.
  function translateSupabaseError(msg) {
    if (!msg) return 'Error desconocido. Intentá de nuevo.';
    const m = msg.toLowerCase();
    if (m.includes('invalid login credentials')) return 'Email o contraseña incorrectos.';
    if (m.includes('email not confirmed')) return 'Tu email aún no está confirmado. Revisá tu bandeja.';
    if (m.includes('user already registered') || m.includes('already registered')) {
      return 'Ya existe una cuenta con ese email. Probá iniciar sesión.';
    }
    if (m.includes('password should be at least')) return 'La contraseña es muy corta.';
    if (m.includes('rate limit') || m.includes('too many')) {
      return 'Demasiados intentos. Esperá unos minutos antes de volver a probar.';
    }
    if (m.includes('network') || m.includes('failed to fetch')) {
      return 'Problema de red. Verificá tu conexión y reintentá.';
    }
    return msg; // Fallback: mostrar el mensaje original
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
