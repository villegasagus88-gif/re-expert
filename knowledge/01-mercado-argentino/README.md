# 01 — Mercado Argentino

Datos vivos del mercado: segmentos, zonas, absorción, precios de cierre, ciclos.

## Archivos previstos
- `segmentos-residencial.md` — premium, alto, medio, vivienda asequible
- `segmentos-comercial.md` — oficinas, retail, logística, hotelería
- `zonas-caba.md` — barrios, indicadores y dinámica
- `zonas-pba-norte.md` — corredor norte
- `zonas-pba-sur-oeste.md`
- `ciclos-historicos.md` — 2001 / 2018 / 2020 / actual
- `volumen-escrituras.md` — series Colegio Escribanos CABA + PBA

## Reglas de la carpeta
- **Cierres reales > listados.**
- Indexar todo precio en **USD** (preferentemente MEP) y aclarar fecha.
- Citar fuente: Colegio de Escribanos, Reporte Inmobiliario, BCRA.
- Marcar `last_verified` mensual; los datos envejecen rápido.

## 🔴 Datos volátiles vs 🟢 estables

Aplican las reglas de `_meta/politica-datos.md`.

**🔴 Volátil — el chat NO da el número:**
- Valor m² USD por barrio / zona.
- Rentabilidad bruta y neta por barrio.
- Volumen mensual de escrituración.
- Cap rate de referencia.
- Listados activos y absorción del mes.

**🟡 Semivolátil:**
- Rangos históricos de USD/m² por zona (informativo, marcar como tal).
- Cap Rate típico CABA por categoría (referencia, no operativo).

**🟢 Estable — respuesta directa:**
- Caracterización de zonas (qué público, qué tipologías predominan, conectividad).
- Segmentos de demanda y motivo de compra.
- Ciclos históricos del mercado AR (qué pasó en 2001, 2018, 2020 y por qué).
- Métricas de mercado conceptuales: cómo se mide absorción, vacancia, time on market.
- Cómo se construye un comparable book.
- Diferencia listado vs cierre.

**Para datos del día → enviar a:** Colegio de Escribanos CABA, Reporte Inmobiliario, ZonaProp/Argenprop (sólo listados — usar con cuidado), BCRA informe inmobiliario.
