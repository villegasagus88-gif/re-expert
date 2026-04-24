# RE Expert — Documentación del proyecto

Carpeta central donde guardamos todo el conocimiento importante del proyecto:
decisiones de arquitectura, trade-offs conocidos, runbook de operaciones y
changelog de tareas.

> **Objetivo:** que cualquier persona que entre al proyecto (socio, nuevo dev,
> vos mismo dentro de 6 meses) pueda entender **cómo** está construido, **por
> qué** se tomaron las decisiones y **cómo operarlo** sin tener que leer todo
> el código.

---

## Índice

| Documento | Para qué sirve |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Cómo está armado el sistema: stack, módulos, flujo de datos. Leer **primero**. |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Cómo se deploya (Railway + Netlify + Supabase), CI/CD, variables de entorno. |
| [`DECISIONS.md`](DECISIONS.md) | ADRs — decisiones técnicas tomadas y **por qué**. |
| [`TRADE_OFFS.md`](TRADE_OFFS.md) | Deuda técnica conocida. Cosas simplificadas para MVP y cómo migrar después. |
| [`RUNBOOK.md`](RUNBOOK.md) | Operaciones comunes: rotar credenciales, ver logs, resolver errores típicos. |
| [`TASKS_COMPLETED.md`](TASKS_COMPLETED.md) | Changelog humano de las tareas completadas (no confundir con `git log`). |

---

## Convenciones del repo

- **Idioma:** código y commits en inglés; documentación y comentarios de producto en español rioplatense.
- **Ramas:** `feat/<nombre>`, `fix/<nombre>`, `docs/<nombre>`, `ci/<nombre>`.
- **PRs:** siempre pasan por GitHub Actions (ruff lint + pytest) antes de mergear a `main`.
- **Deploys:** cada merge a `main` dispara auto-deploy (Railway backend + Netlify frontend).

## Cómo actualizar esta documentación

Cuando hagas un cambio importante:
1. Si afecta la arquitectura → actualizar `ARCHITECTURE.md`.
2. Si es una decisión con alternativas → agregar entrada en `DECISIONS.md`.
3. Si dejás algo pendiente para después → anotarlo en `TRADE_OFFS.md`.
4. Si completaste una tarea → agregar línea en `TASKS_COMPLETED.md`.
