# 05 — Construcción

Aspectos técnicos y operativos: rubros, rendimientos, materiales, modalidades de
contratación, control de obra, calidad y seguridad.

## Archivos en esta carpeta

Listado dinámico — ver el `ls` real de la carpeta.

- `rendimientos-mano-obra.md` — m²/día por tarea (datos técnicos estables).
- `modalidades-contratacion.md` — llave en mano, costo+honorario, gerenciamiento.
- `gestion-subcontratistas.md` + `laboral-patologia-subcontratistas-y-fraude.md` (en `03-laboral`).
- `certificacion-obra.md` + `control-presupuestario.md` (en `14-costos-presupuesto`).
- `change-orders-claims.md` — gestión de cambios y adicionales.
- `higiene-seguridad.md` — programa SRT, ART, plan de prevención.
- `recepcion-obra.md` + `final-obra.md` + `cierre-traspaso.md` — recepción y traspaso.
- `garantias-vicios-ruina.md` + `garantias-vicios-aplicado.md` — vicios y ruina.
- `patologia-constructor-en-problemas.md` — qué hacer si el constructor falla.
- `documentacion-obra.md` — soportes legales y operativos.

> Estructura de costos y composición $/m² → `14-costos-presupuesto/estructura-costos.md`.
> Criterios técnicos de materiales clave → `13-arquitectura-ingenieria/`.

## Reglas
- $/m² siempre en USD billete + ARS al cambio del día.
- Citar ICC INDEC + CAC + paritarias UOCRA.
- Diferenciar zonas: GBA / interior.

## 🔴 Datos volátiles vs 🟢 estables

Aplican las reglas de `_meta/politica-datos.md`.

**🔴 Volátil — el chat NO da el número:**
- Precios de materiales en ARS (lista del proveedor del día).
- Costos USD/m² por categoría (cambian por inflación en USD y costo de MO).
- Jornales por categoría UOCRA.
- Variación mensual ICC INDEC.
- Valor del flete y servicios accesorios.
- Costo de hormigón elaborado por proveedor.

**🟡 Semivolátil — guardar con fecha:**
- Rangos USD/m² por categoría (refrescar trimestral, marcar como referencia, no presupuesto).
- Pesos típicos de cada rubro sobre el total (más estables, refrescar anual).
- Rendimientos de MO por tarea (m²/día) — son técnicos, cambian poco.

**🟢 Estable — respuesta directa:**
- Estructura de un cómputo y presupuesto.
- Rubros de obra y orden de ejecución.
- Modalidades de contratación (llave en mano, costo+honorario, gerenciamiento) — ventajas, riesgos, cuándo usar cada una.
- Curva S de avance financiero típica.
- Protocolo de certificación de obra y manejo de adicionales / órdenes de cambio.
- Programa de higiene y seguridad SRT — obligaciones del empleador.
- Plazos legales de garantía: vicios aparentes, ocultos, ruina (CCyCN art. 1273).
- Calidad: protocolos de recepción, pruebas de instalaciones.
- Criterios técnicos de materiales clave (hormigón, acero, cerámicos).

**Para datos del día → enviar a:** ICC INDEC (mensual), CAC (cac.com.ar), proveedores mayoristas con lista vigente, MTEySS para jornales.
