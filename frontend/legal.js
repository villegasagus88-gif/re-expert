/**
 * Render de las páginas legales.
 *
 * Cada página (privacidad.html, terminos.html, cookies.html) llama a
 * `RELegal.render({slug, titulo})`, que busca `legal/<slug>.md` y lo renderiza.
 * Esos .md los genera `scripts/publicar_legales.py` a partir de `legal/*.md`,
 * sacándoles las anotaciones internas.
 *
 * Tokens: el documento trae `{{titular}}`, `{{cuit}}`, `{{domicilio}}`,
 * `{{email}}`, `{{sitio}}` y `{{vigenciaDesde}}`, que se reemplazan con lo que
 * haya en `legal-config.js`. Los que todavía no estén cargados se muestran como
 * un hueco marcado en vez de desaparecer: el texto completo se puede leer desde
 * hoy, y salta a la vista qué falta cerrar.
 *
 * Mientras falte alguno, arriba del documento va un aviso de versión preliminar
 * que dice exactamente cuáles son. Eso es distinto de esconder el documento:
 * el usuario tiene derecho a leer las condiciones que se le aplican, y no
 * poder identificar al responsable es un defecto que hay que declarar, no
 * tapar.
 *
 * El markdown se sanitiza SIEMPRE con DOMPurify, igual que el chat. Es contenido
 * propio, pero un documento legal es exactamente el lugar donde no querés
 * descubrir que alguien metió un <script> por una ruta que no previste.
 */
(function () {
  'use strict';

  var CONTACTO_FALLBACK = 'el formulario de Ayuda → Informar un error dentro de la app';

  function el(id) { return document.getElementById(id); }

  // Etiqueta legible de cada token, para poder nombrar lo que falta.
  var ETIQUETAS = {
    titular: 'razón social o nombre del responsable',
    cuit: 'CUIT',
    domicilio: 'domicilio legal',
    email: 'casilla de contacto',
    vigenciaDesde: 'fecha de vigencia',
    sitio: 'dirección del sitio',
  };

  /** Tokens que el documento usa y todavía no tienen valor cargado. */
  function faltantes(md) {
    var L = window.RE_LEGAL || {};
    var usados = {};
    (md.match(/\{\{(\w+)\}\}/g) || []).forEach(function (t) {
      usados[t.slice(2, -2)] = true;
    });
    return Object.keys(usados).filter(function (k) { return !L[k]; });
  }

  function avisoPreliminar(pendientes) {
    var lista = pendientes.map(function (k) {
      return ETIQUETAS[k] || k;
    }).join(', ');
    return '' +
      '<div class="lg-aviso">' +
        '<div class="lg-aviso-t">Versión preliminar</div>' +
        '<p>Podés leer el documento completo: <b>lo que dice es lo que se aplica</b>. ' +
        'Lo que todavía no está cerrado son los datos de identificación del responsable ' +
        '(' + escaparHtml(lista) + '), que aparecen abajo marcados como pendientes.</p>' +
        '<p>Eso no te quita ningún derecho. Podés ejercerlos igual: escribinos por ' +
        CONTACTO_FALLBACK + ', o usá el ' +
        '<a href="arrepentimiento.html">Botón de Arrepentimiento</a> si querés revocar ' +
        'una contratación.</p>' +
      '</div>';
  }

  /** Reemplaza {{token}} por su valor; lo que falta queda marcado, no borrado. */
  function sustituir(md) {
    var L = window.RE_LEGAL || {};
    return md.replace(/\{\{(\w+)\}\}/g, function (_, k) {
      if (L[k]) return String(L[k]);
      return '`[' + (ETIQUETAS[k] || k) + ' — pendiente]`';
    });
  }

  function escaparHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /** Markdown → HTML sanitizado. Fail-closed: sin las librerías, texto plano. */
  function renderMd(md) {
    if (!window.marked || !window.DOMPurify) return '<pre>' + escaparHtml(md) + '</pre>';
    window.marked.setOptions({ gfm: true, breaks: false });
    return window.DOMPurify.sanitize(window.marked.parse(md), {
      // Un documento legal no tiene por qué traer imágenes ni embeds.
      FORBID_TAGS: ['img', 'svg', 'video', 'audio', 'iframe', 'embed', 'object', 'form', 'input'],
      FORBID_ATTR: ['onerror', 'onload', 'onclick', 'style'],
    });
  }

  function render(opts) {
    var cont = el('lgContenido');
    if (!cont) return;

    cont.innerHTML = '<div class="lg-card"><p>Cargando el documento…</p></div>';
    fetch('legal/' + opts.slug + '.md', { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error(String(r.status));
        return r.text();
      })
      .then(function (md) {
        var pendientes = faltantes(md);
        cont.innerHTML =
          (pendientes.length ? avisoPreliminar(pendientes) : '') +
          '<div class="lg-doc">' + renderMd(sustituir(md)) + '</div>';
      })
      .catch(function () {
        // El .md no está donde se lo espera: hay que correr el conversor. Se
        // dice tal cual para no dejar la página muda ni fingir que no existe.
        cont.innerHTML = '<div class="lg-aviso">' +
          '<div class="lg-aviso-t">No pudimos cargar el documento</div>' +
          '<p>No encontramos <code>legal/' + escaparHtml(opts.slug) + '.md</code>. ' +
          'Se genera con <code>python scripts/publicar_legales.py</code>.</p>' +
          '<p>Mientras tanto podés escribirnos por ' + CONTACTO_FALLBACK + ', o usar el ' +
          '<a href="arrepentimiento.html">Botón de Arrepentimiento</a>.</p></div>';
      });
  }

  window.RELegal = { render: render, escaparHtml: escaparHtml, faltantes: faltantes };
})();
