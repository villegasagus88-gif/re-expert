# 08 — Macroeconomía aplicada al RE

Variables macro que mueven el rubro y cómo leerlas como analista.

## Archivos previstos
- `inflacion-indices.md` — IPC, IPIM, ICC: qué miden y cómo se usan en RE
- `tipos-de-cambio.md` — oficial, MEP, CCL, blue, brecha — impacto en precios y costos
- `politica-monetaria.md` — BCRA: tasa, agregados, REM
- `politica-fiscal.md` — recaudación, déficit, deuda — efecto sobre crédito y demanda
- `salario-en-usd.md` — serie histórica + correlación con absorción
- `crisis-historicas.md` — 2001, 2018, 2020 — qué se aprendió en cada una
- `escenarios-2025-2027.md` — análisis prospectivo (volátil, refrescar)
- `riesgos-macro-proyecto.md` — checklist de cómo cada variable impacta el modelo

## Reglas
- Todo dato con fecha + fuente oficial.
- Distinguir **dato vs opinión** explícitamente.
- Cuando se cite estimación privada: nombre + fecha + metodología.
- No predicciones sin escenarios.

## 🔴 Datos volátiles vs 🟢 estables

**Esta carpeta es la más volátil del KB.** Aplican las reglas de `_meta/politica-datos.md` con extra rigor.

**🔴 Volátil — el chat NO da el número:**
- Tipo de cambio (oficial / MEP / CCL / blue / billete) — diario.
- Tasa de política BCRA — por reunión.
- IPC mensual / IPIM / ICC — mensual.
- Riesgo país (EMBI+) — diario.
- Tasas activas y pasivas en bancos — diario.
- Salario en USD — mensual.
- Reservas BCRA — diario.
- Brecha cambiaria — diaria.

**🟡 Semivolátil:**
- Régimen cambiario vigente (cepo, MULC, CCL legal vs ilegal): cambia por DNU/Comunicación BCRA.
- Tope para no aplicar percepciones cambiarias.
- Pisos de tasas reguladas.

**🟢 Estable — respuesta directa:**
- Cómo se calcula cada índice (IPC vs IPIM vs ICC, qué mide cada uno).
- Cómo se forma cada tipo de cambio (MEP = bono comprado en pesos / vendido en USD; CCL = …).
- Política monetaria conceptual: qué es y cómo opera la tasa de política.
- Lecciones de crisis pasadas (2001, 2018, 2020) — qué se aprendió como developer.
- Cómo cada variable macro impacta el modelo de un proyecto (sensibilidades, coberturas).
- Marco analítico para leer un escenario macro.

**Para datos del día → enviar a:** BCRA (bcra.gob.ar), INDEC (indec.gob.ar), Mecon (economia.gob.ar), REM (encuesta BCRA), ámbito.com / Rava (precios de mercado).
