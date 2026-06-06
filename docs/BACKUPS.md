# Backups y restore — RE Expert

> Plan de respaldo de la base (Supabase Postgres) y del Storage. Pre-launch hay
> pocos datos, pero esto debe estar antes de meter usuarios reales: una DB sin
> backup verificado es un incidente de pérdida total esperando a pasar.
>
> Quién: la **configuración** de backups automáticos la hace Agustín (owner de
> Supabase). El **backup manual** lo puede correr cualquiera con la connection
> string. Este doc cubre ambos + cómo restaurar.

---

## 1. Qué hay que respaldar

| Dato | Dónde vive | Cómo se respalda |
|------|-----------|------------------|
| Base Postgres (users, conversaciones, memoria, pagos, proyecto, etc.) | Supabase Postgres | Backup automático Supabase + `pg_dump` manual |
| Knowledge base (240 archivos) | Supabase Storage, bucket `knowledge` | Ver §5 (Storage no entra en el backup de Postgres) |
| Secrets / env vars | Railway + Netlify | NO se respaldan acá; viven en los dashboards. Mantener un registro seguro aparte (`.env.example` lista las claves, sin valores) |

---

## 2. Backup automático (Supabase) — lo configura Agustín

Depende del plan de Supabase:

| Plan Supabase | Backups |
|---------------|---------|
| **Free** | **NO hay backups automáticos.** El backup manual (§3) es obligatorio. |
| **Pro** | Backups diarios automáticos, retención 7 días. |
| **Team/Enterprise** | Point-in-Time Recovery (PITR), restore a cualquier segundo dentro de la ventana. |

**Acción para Agustín:** Supabase Dashboard → Database → **Backups**. Confirmar el
plan y la retención. Si estamos en Free, **subir a Pro antes del launch** o
automatizar el `pg_dump` de §3 en un cron (GitHub Action / Railway cron).

Recomendado para el launch: **Pro (daily) como mínimo**; PITR cuando haya
facturación real (RPO de minutos en vez de 24 h).

---

## 3. Backup manual (`pg_dump`) — universal, funciona en cualquier plan

Usar la connection string **directa** (puerto `5432`, no el pooler `6543`):

```bash
# Connection string directa de Supabase (Settings → Database → Connection string → URI)
export PGURL="postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres"

# Dump completo comprimido, con timestamp
pg_dump "$PGURL" -Fc -f "re-expert-$(date +%Y%m%d-%H%M).dump"
```

- `-Fc` = formato custom comprimido (restaurable con `pg_restore`, selectivo).
- Guardar el `.dump` **fuera de Supabase** (Drive, S3, disco local cifrado).
- Para un dump en SQL plano legible: `pg_dump "$PGURL" -f backup.sql`.

> **Pre-launch:** correr esto a mano antes de cada cambio grande de schema
> (migración Alembic riesgosa) — es la red de seguridad más rápida.

---

## 4. Restore

### Desde backup automático de Supabase
Supabase Dashboard → Database → Backups → elegir el punto → **Restore**.
⚠️ El restore **reemplaza** la base actual. Confirmar bien la fecha.

### Desde un dump manual (`pg_restore`)
```bash
# A una base NUEVA/vacía (recomendado: restaurar a un proyecto de staging primero)
pg_restore --clean --if-exists --no-owner -d "$PGURL" "re-expert-YYYYMMDD-HHMM.dump"
```
- `--clean --if-exists` = dropea objetos antes de recrearlos (restore sobre una DB con datos).
- `--no-owner` = evita errores de ownership entre proyectos Supabase.
- Tras restaurar: correr `alembic current` para confirmar que la versión de
  schema coincide con el código desplegado; si no, `alembic upgrade head`.

---

## 5. Storage (knowledge base)

El bucket `knowledge` (240 archivos) **no entra** en el backup de Postgres.
Opciones:
- Es contenido semi-estático (seed en el repo bajo `knowledge/` como fuente). Si
  se pierde el bucket, se re-sube desde el repo.
- Para respaldo del estado vivo del bucket: Supabase CLI →
  `supabase storage cp --recursive ss://knowledge ./knowledge-backup/` (o la API
  de Storage). Hacerlo si el contenido del bucket diverge del repo.

---

## 6. Objetivos (MVP) y verificación

| Métrica | Objetivo MVP | Con PITR |
|---------|--------------|----------|
| **RPO** (cuánto dato se puede perder) | ≤ 24 h (backup diario) | ≤ 5 min |
| **RTO** (cuánto tarda volver) | ≤ 1 h (restore manual) | ≤ 30 min |

**Verificar el restore (clave):** un backup sin restore probado no es un backup.
Antes del launch, hacer **una** prueba completa: tomar un dump, restaurarlo a un
proyecto Supabase de staging, levantar el backend apuntando ahí y confirmar que
login + chat funcionan. Repetir trimestralmente.

---

## 7. Relación con incidentes

Si la DB se corrompe o se borra datos por error, este es el camino de recuperación
referenciado desde [RUNBOOK_INCIDENTS.md](./RUNBOOK_INCIDENTS.md) §4 (DB caída).
Mantener el último `.dump` manual accesible acelera el RTO.
