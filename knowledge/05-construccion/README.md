# 05 — Construcción

Aspectos técnicos y operativos: rubros, rendimientos, materiales, modalidades de
contratación, control de obra, calidad y seguridad.

## Archivos previstos
- `rubros-obra.md` (migrar desde raíz legacy)
- `rendimientos.md` (migrar)
- `costo-construccion-ar.md` — cómo se compone $/m² en AR
- `contratacion-modalidades.md` — llave en mano, costo+honorario, gerenciamiento
- `gestion-cambios.md` — ordenes de cambio, adicionales
- `control-certificaciones.md` — certificación contra avance verificado
- `higiene-seguridad.md` — programa SRT, ART, plan de prevención
- `calidad-recepcion.md` — protocolo de recepción de obra
- `materiales-clave.md` — hormigón, acero, cerámicos, aberturas (criterios técnicos + variación de precio)

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
