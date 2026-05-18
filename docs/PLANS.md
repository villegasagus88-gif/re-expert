# Planes y precios — RE Expert

> Fuente única en código: [`backend/config/plans.py`](../backend/config/plans.py).
> Toda copy en frontend (`pricing.html`, `success.html`, `account.html`) debe coincidir con esta tabla.

## Comparativa

| Feature                              | Free                  | Pro                          |
| ------------------------------------ | --------------------- | ---------------------------- |
| **Precio**                           | USD 0 / mes           | **USD 19 / mes**             |
| Mensajes al asistente IA             | 20 / día (5 / hora)   | 200 / día (50 / hora)        |
| Chat con base de conocimiento        | ✅                    | ✅                           |
| Lectura de Materiales / Noticias     | ✅                    | ✅                           |
| Historial de conversaciones          | últimas 3             | completo                     |
| **Asistente SOL** (contexto proyecto)| ❌                    | ✅                           |
| Dashboard de Proyecto                | ❌                    | ✅                           |
| Presupuestos / Hitos / Materiales    | ❌                    | ✅                           |
| Indicadores CPI / SPI / EAC          | ❌                    | ✅                           |
| Ingesta de datos vía SOL             | ❌                    | ✅                           |
| Export (CSV / PDF)                   | ❌                    | ✅                           |
| Soporte prioritario                  | ❌                    | ✅                           |

## Límites de rate

Enforzados por `services/rate_limit_service.py`. Headers `X-RateLimit-*` se devuelven en cada respuesta de `/api/chat`.

| Plan | per_hour | per_day |
| ---- | -------- | ------- |
| free | 5        | 20      |
| pro  | 50       | 200     |

Al excederlos: `HTTP 429` + `Retry-After` calculado contra el mensaje más viejo de la ventana.

## Decisiones (2026-04-28)

- **Precio Pro: USD 19/mes.** Punto medio del rango objetivo (USD 15-25). Alineado con SaaS comparables (ChatGPT Plus 20, Cursor 20, Notion 10). Cobro en USD vía Stripe.
- **200 msgs/día en Pro en lugar de "ilimitadas".** Más honesto con costos de Anthropic (cada mensaje invoca Claude Sonnet 4.6 con contexto largo) y permite proyectar gross margin con variabilidad acotada.
- **20 msgs/día en Free.** Suficiente para que un usuario nuevo evalúe la calidad del producto (5-10 consultas reales) sin que el costo de adquisición de Anthropic se desboque.
- **SOL es Pro-only.** Es el feature de mayor valor agregado (contexto proyecto) y el más caro de servir (system prompt largo + ingesta).
- **Export es Pro-only** (cuando se implemente). CSV/PDF de presupuestos, materiales, conversaciones.

## Cómo cambiar un límite o feature

1. Editar `backend/config/plans.py`.
2. Actualizar copy visible en:
   - `frontend/pricing.html` (tarjetas y hero)
   - `frontend/success.html` (perks de bienvenida)
   - `frontend/account.html` (CTA de upgrade)
3. Actualizar esta tabla.
4. Si cambia el precio: actualizar el Stripe Price (ID en `STRIPE_PRICE_ID_PRO`) — el código no usa el monto de Python para cobrar, solo para mostrar.
