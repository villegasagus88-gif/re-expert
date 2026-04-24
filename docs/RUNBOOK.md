# Runbook operativo

Pasos concretos para tareas operativas frecuentes. Pensado para que puedas
resolver solo lo urgente sin depender de memoria.

---

## Ver logs del backend en producción

1. Ir a Railway → proyecto RE Expert → servicio backend.
2. Solapa **Deployments** → click en el deploy activo → **View Logs**.
3. Filtros útiles: buscar por `ERROR`, por `user_id`, por ruta (`/api/chat`).

## Forzar un redeploy sin cambios

- Railway → Deployments → botón **⋯** en el deploy actual → **Redeploy**.

## Rollback del backend

1. Railway → Deployments.
2. Encontrar el deploy anterior **Success**.
3. **⋯** → **Redeploy**.

## Rotar un secret (ej: `ANTHROPIC_API_KEY` filtrada)

1. Anthropic Console → crear nueva API key.
2. Railway → Variables → pegar la nueva en `ANTHROPIC_API_KEY` → **Deploy**.
3. Anthropic Console → revocar la vieja.
4. Verificar con `curl https://<host>/health` y una request real al chat.
5. Agregar entrada en [`TASKS_COMPLETED.md`](TASKS_COMPLETED.md) como incident note.

Para `JWT_SECRET` de Supabase **no lo rotes vos**: implica invalidar todas las sesiones activas.
Coordinar con el equipo.

## Correr una migración Alembic manual

Solo si el auto-deploy falla o hay que testear localmente:

```bash
cd backend
alembic upgrade head          # aplica todas las pendientes
alembic downgrade -1          # rollback de la última (si es reversible)
alembic current               # ver en qué versión está la DB
alembic history               # ver todas las migraciones
```

En producción, **siempre** las corre Railway vía `preDeployCommand`.

## Crear una migración nueva

```bash
cd backend
alembic revision -m "add xyz table"       # esqueleto vacío (recomendado, más control)
# editar el archivo creado en alembic/versions/
alembic upgrade head                       # probar local
```

> Importante: numerar manualmente (`0003`, `0004`, etc.) y setear `down_revision`
> al anterior. Ver `0003_add_token_usage.py` como template.

## Resolver "user can't log in" o errores 401

1. ¿El usuario existe en Supabase? → Supabase → Authentication → Users, buscar por email.
2. ¿Confirmó el email? Si no, botón **Send confirmation email**.
3. ¿El JWT que manda el frontend es válido? Probar en jwt.io con `JWT_SECRET` de Supabase.
4. ¿El backend usa la `JWT_SECRET` correcta? Verificar en Railway Variables.

## Resolver "Stream timeout" o respuestas cortadas

1. Ver logs del backend durante el timeout: buscar `Stream timeout after 60s`.
2. Causas comunes:
   - Prompt muy largo → chequear tamaño del contexto inyectado por `context_router`.
   - Anthropic API lenta → mirar status.anthropic.com.
   - Railway instance saturada → ver CPU/RAM en Railway Metrics.

## Verificar rate limiting funcionando

```bash
JWT=<token>
for i in {1..25}; do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST https://<host>/api/chat \
    -H "Authorization: Bearer $JWT" \
    -H "Content-Type: application/json" \
    -d '{"message":"test"}'
done
# esperamos ver 200s y después 429 con Retry-After
```

## Subir un archivo de knowledge

1. Subirlo a Supabase Storage → bucket `knowledge` → formato `.md`.
2. No requiere redeploy — `anthropic_service.load_knowledge_context()` lo lee en cada request.
3. Si agregaste un **dominio nuevo**, editar `services/context_router.py` para incluir keywords.

## Renombrar/mover `DATABASE_URL`

- Usar siempre la connection string del **pooler transaction mode** de Supabase.
- Formato: `postgresql+asyncpg://postgres.<project>:<pass>@aws-0-<region>.pooler.supabase.com:6543/postgres`.
- La string directa (`5432`) **no** sirve bajo carga porque no usa pooling.

## Ver consumo y costo por usuario

Query directa en Supabase SQL editor:

```sql
select
  p.email,
  count(tu.id) as requests,
  sum(tu.total_tokens) as tokens,
  round(sum(tu.cost_usd)::numeric, 4) as cost_usd
from token_usage tu
join profiles p on p.id = tu.user_id
where tu.created_at > now() - interval '30 days'
group by p.email
order by cost_usd desc;
```

## Pre-checklist antes de mergear un PR

- [ ] CI verde (ruff + pytest).
- [ ] Si tocaste modelos → hay migración Alembic nueva.
- [ ] Si tocaste endpoints → `ARCHITECTURE.md` refleja el cambio.
- [ ] Si agregaste variables de entorno → `DEPLOYMENT.md` + Railway Variables.
- [ ] Commit message sigue convención (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`).
