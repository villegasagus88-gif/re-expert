/**
 * Datos del titular — fuente ÚNICA para todo lo legal.
 *
 * ─────────────────────────────────────────────────────────────────────────
 *  QUÉ PASA SI ESTO ESTÁ VACÍO (que es el estado de hoy)
 * ─────────────────────────────────────────────────────────────────────────
 *  Los documentos SE PUBLICAN IGUAL y se pueden leer completos. Lo único que
 *  cambia es que los datos de identificación aparecen marcados como
 *  `[razón social — pendiente]` y arriba del documento va un aviso de versión
 *  preliminar que dice cuáles faltan.
 *
 *  Esa decisión es deliberada: no tener publicadas las condiciones es un
 *  incumplimiento en sí mismo, y el usuario tiene derecho a leer lo que se le
 *  aplica. Declarar el hueco es mejor que esconder el documento entero, y
 *  muchísimo mejor que inventar una razón social.
 *
 * ─────────────────────────────────────────────────────────────────────────
 *  CÓMO CERRARLO
 * ─────────────────────────────────────────────────────────────────────────
 *  Completá los campos de abajo. Nada más: los huecos se llenan solos en las
 *  tres páginas y el aviso preliminar desaparece cuando no queda ninguno.
 *
 *  Si además cambiás el TEXTO de los documentos, editá los de `legal/` (que es
 *  la versión de trabajo, con las anotaciones internas) y regenerá los
 *  publicables con:
 *
 *      python scripts/publicar_legales.py
 *
 *  Nunca edites `frontend/legal/*.md` a mano: se sobrescriben.
 *
 *  ⚠️ Este archivo se sirve al navegador. NO poner acá nada que no sea
 *  información pública del titular (la que va impresa en los documentos).
 */
window.RE_LEGAL = {
  titular: '',        // Razón social, o nombre y apellido si es persona física
  cuit: '',           // CUIT / CUIL, con guiones
  domicilio: '',      // Calle y número, ciudad, provincia, país
  email: '',          // Casilla real de contacto (tiene que recibir y leerse)
  vigenciaDesde: '',  // Fecha de publicación, formato DD/MM/AAAA

  sitio: 'https://re-expert.netlify.app',
};
