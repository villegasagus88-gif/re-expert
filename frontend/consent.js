/**
 * Consentimiento de almacenamiento y terceros.
 *
 * ─────────────────────────────────────────────────────────────────────────
 *  POR QUÉ ESTE BANNER NO TIENE "ANALÍTICA" NI "PUBLICIDAD"
 * ─────────────────────────────────────────────────────────────────────────
 *  Porque no existen. Se auditó el código: `document.cookie` no aparece en
 *  ningún lado, no hay Google Analytics, ni píxeles, ni herramientas de
 *  perfilado, y `SENTRY_DSN` está vacío. Un panel con toggles sobre categorías
 *  inexistentes da sensación de control sin darlo: es peor que no tenerlo,
 *  porque enseña a la gente que los banners son un trámite.
 *
 *  Lo que SÍ hay, y por eso el banner existe:
 *
 *  1. **Google Fonts.** `fonts.googleapis.com` y `fonts.gstatic.com` reciben la
 *     IP del visitante ANTES de cualquier consentimiento, con sólo abrir la
 *     página. Es una transferencia a un tercero en EE.UU. Este módulo la
 *     bloquea hasta que la persona decida: sin consentimiento se usa la
 *     tipografía del sistema, que ya está declarada como fallback en el CSS, así
 *     que no hay texto invisible ni salto de layout brusco.
 *  2. **localStorage de primera parte** (sesión, tema, preferencias). Es
 *     estrictamente necesario para que la app funcione: sin la sesión no se
 *     puede entrar. No se puede desactivar y se declara con nombre y propósito.
 *
 *  La decisión se guarda en localStorage —no en una cookie, coherente con no
 *  usarlas— junto con la versión del texto y la fecha, que es lo que permite
 *  volver a preguntar si algún día cambia lo que se recolecta.
 *
 *  Uso: incluir este script en cualquier página. Se autoinicializa.
 *  Para reabrir el panel desde un link: `RECookies.abrirPanel()`.
 */
(function () {
  'use strict';

  var CLAVE = 're_consent';
  // Subir esta versión cuando cambie QUÉ se recolecta (no cuando cambie el
  // texto): invalida el consentimiento anterior y se vuelve a preguntar.
  var VERSION = 1;

  // La URL la declara cada página en <meta name="re-fuentes">: cada una pide
  // familias y pesos distintos, así que hardcodearla acá le rompería la
  // tipografía a alguna. Si la meta no está, no hay nada que gatear.
  function urlFuentes() {
    var m = document.querySelector('meta[name="re-fuentes"]');
    return (m && m.getAttribute('content')) || '';
  }

  // ── Estado ────────────────────────────────────────────────────────────
  function leer() {
    try {
      var raw = localStorage.getItem(CLAVE);
      if (!raw) return null;
      var d = JSON.parse(raw);
      if (!d || d.v !== VERSION) return null;   // cambió lo que recolectamos
      return d;
    } catch (e) { return null; }
  }

  function guardar(fuentes) {
    try {
      localStorage.setItem(CLAVE, JSON.stringify({
        v: VERSION,
        fuentes: !!fuentes,
        fecha: new Date().toISOString(),
      }));
    } catch (e) { /* modo privado sin storage: se vuelve a preguntar */ }
  }

  /** ¿Se pueden cargar las tipografías de Google? */
  function permiteFuentes() {
    var d = leer();
    return !!(d && d.fuentes);
  }

  // ── Efecto real del consentimiento ────────────────────────────────────
  function cargarFuentes() {
    if (document.getElementById('reFuentesGoogle')) return;
    var url = urlFuentes();
    if (!url) return;
    var l = document.createElement('link');
    l.id = 'reFuentesGoogle';
    l.rel = 'stylesheet';
    l.href = url;
    document.head.appendChild(l);
  }

  function quitarFuentes() {
    var l = document.getElementById('reFuentesGoogle');
    if (l) l.remove();
  }

  function aplicar() {
    if (permiteFuentes()) cargarFuentes(); else quitarFuentes();
  }

  // ── UI ────────────────────────────────────────────────────────────────
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function cerrar() {
    var n = document.getElementById('reConsent');
    if (n) n.remove();
    document.removeEventListener('keydown', onEsc);
  }

  function onEsc(e) {
    // Esc equivale a "sólo lo necesario": cerrar sin elegir no puede
    // interpretarse como aceptación.
    if (e.key === 'Escape') { decidir(false); }
  }

  function decidir(fuentes) {
    guardar(fuentes);
    aplicar();
    cerrar();
  }

  function plantillaBanner() {
    return '' +
    '<div class="rec-banner" role="dialog" aria-modal="false" aria-labelledby="recTitulo">' +
      '<div class="rec-banner-in">' +
        '<div class="rec-txt">' +
          '<div class="rec-t" id="recTitulo">Tu privacidad, en concreto</div>' +
          '<p class="rec-p"><b>No usamos cookies.</b> Ni de analítica, ni de publicidad, ' +
          'ni de seguimiento. Lo único que sale hacia afuera al abrir esta página son ' +
          'las <b>tipografías de Google</b>, que reciben tu dirección IP. Podés ' +
          'impedirlo y la página se ve igual con la tipografía de tu sistema.</p>' +
        '</div>' +
        '<div class="rec-btns">' +
          '<button type="button" class="rec-btn rec-btn-ghost" id="recConfig">Configurar</button>' +
          '<button type="button" class="rec-btn rec-btn-sec" id="recSolo">Sólo lo necesario</button>' +
          '<button type="button" class="rec-btn rec-btn-pri" id="recTodas">Aceptar todo</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  function plantillaPanel(fuentesOn) {
    return '' +
    '<div class="rec-overlay" id="recOverlay"></div>' +
    '<div class="rec-panel" role="dialog" aria-modal="true" aria-labelledby="recPanelT">' +
      '<div class="rec-panel-head">' +
        '<div class="rec-t" id="recPanelT">Preferencias de privacidad</div>' +
        '<button type="button" class="rec-x" id="recCerrar" aria-label="Cerrar">✕</button>' +
      '</div>' +
      '<div class="rec-panel-body">' +

        '<div class="rec-cat">' +
          '<div class="rec-cat-head">' +
            '<div>' +
              '<div class="rec-cat-t">Estrictamente necesario</div>' +
              '<div class="rec-cat-d">Sin esto no podés iniciar sesión ni usar la app.</div>' +
            '</div>' +
            '<span class="rec-fijo">Siempre activo</span>' +
          '</div>' +
          '<ul class="rec-lista">' +
            '<li><code>re_access_token</code> · <code>re_refresh_token</code> — mantienen tu sesión abierta</li>' +
            '<li><code>re_user</code> · <code>re_accounts</code> — tu perfil y las cuentas que guardaste para cambiar entre ellas</li>' +
            '<li><code>re_theme</code> · <code>re_animations</code> — modo claro/oscuro y preferencia de animaciones</li>' +
            '<li><code>re_onboarding_done</code> y estado de la app — para no repetirte pasos</li>' +
          '</ul>' +
          '<p class="rec-nota">Todo esto vive <b>en tu navegador</b>, es de primera parte y ' +
          'no se comparte con nadie. No son cookies: es <code>localStorage</code>.</p>' +
        '</div>' +

        '<div class="rec-cat">' +
          '<div class="rec-cat-head">' +
            '<div>' +
              '<div class="rec-cat-t">Tipografías de Google</div>' +
              '<div class="rec-cat-d">Cargar la tipografía Inter desde los servidores de Google.</div>' +
            '</div>' +
            '<label class="rec-sw">' +
              '<input type="checkbox" id="recSwFuentes"' + (fuentesOn ? ' checked' : '') + '>' +
              '<span class="rec-sw-track" aria-hidden="true"></span>' +
              '<span class="rec-sw-lbl" id="recSwLbl">' + (fuentesOn ? 'Activado' : 'Desactivado') + '</span>' +
            '</label>' +
          '</div>' +
          '<p class="rec-nota">Al cargarlas, <b>Google recibe tu dirección IP</b> y los datos ' +
          'de tu navegador, en Estados Unidos. No instalan cookies, pero es una ' +
          'transferencia a un tercero y por eso te la preguntamos. ' +
          '<b>Si la desactivás, la página usa la tipografía de tu sistema</b> y no ' +
          'perdés ninguna función.</p>' +
        '</div>' +

        '<div class="rec-cat rec-cat-vacia">' +
          '<div class="rec-cat-t">Analítica, publicidad y seguimiento</div>' +
          '<p class="rec-nota">No tenemos. No usamos Google Analytics, ni píxeles de redes ' +
          'sociales, ni perfilado publicitario, ni vendemos datos. Si algún día se ' +
          'agregara algo, este panel te lo volvería a preguntar antes de activarlo.</p>' +
        '</div>' +

        '<p class="rec-legal">Más detalle en la <a href="cookies.html">Política de Cookies</a> ' +
        'y en la <a href="privacidad.html">Política de Privacidad</a>.</p>' +
      '</div>' +
      '<div class="rec-panel-foot">' +
        '<button type="button" class="rec-btn rec-btn-sec" id="recRechazar">Rechazar todo</button>' +
        '<button type="button" class="rec-btn rec-btn-pri" id="recGuardar">Guardar preferencias</button>' +
      '</div>' +
    '</div>';
  }

  function montar(html) {
    var cont = document.getElementById('reConsent');
    if (!cont) {
      cont = document.createElement('div');
      cont.id = 'reConsent';
      document.body.appendChild(cont);
    }
    cont.innerHTML = html;
    return cont;
  }

  function mostrarBanner() {
    var cont = montar(plantillaBanner());
    cont.querySelector('#recTodas').addEventListener('click', function () { decidir(true); });
    cont.querySelector('#recSolo').addEventListener('click', function () { decidir(false); });
    cont.querySelector('#recConfig').addEventListener('click', function () { abrirPanel(); });
    document.addEventListener('keydown', onEsc);
  }

  function abrirPanel() {
    var d = leer();
    var cont = montar(plantillaPanel(d ? !!d.fuentes : false));
    var sw = cont.querySelector('#recSwFuentes');
    var lbl = cont.querySelector('#recSwLbl');
    sw.addEventListener('change', function () {
      lbl.textContent = sw.checked ? 'Activado' : 'Desactivado';
    });
    cont.querySelector('#recGuardar').addEventListener('click', function () {
      decidir(sw.checked);
    });
    cont.querySelector('#recRechazar').addEventListener('click', function () { decidir(false); });
    // Cerrar sin guardar: si NUNCA hubo decisión, vuelve el banner (no se puede
    // seguir navegando como si hubiera aceptado). Si ya había, no se toca.
    var volver = function () { cerrar(); if (!leer()) mostrarBanner(); };
    cont.querySelector('#recCerrar').addEventListener('click', volver);
    cont.querySelector('#recOverlay').addEventListener('click', volver);
    document.addEventListener('keydown', onEsc);
  }

  function init() {
    aplicar();                      // respeta una decisión previa
    if (!leer()) mostrarBanner();   // sin decisión: preguntar
  }

  window.RECookies = {
    abrirPanel: abrirPanel,
    permiteFuentes: permiteFuentes,
    /** Para tests y para el link de "preferencias de privacidad" del footer. */
    _leer: leer,
    VERSION: VERSION,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
