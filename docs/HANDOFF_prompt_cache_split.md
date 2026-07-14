# Handoff para Agus — split del system prompt en bloques de cache

**Branch:** `perf/prompt-cache-split-agus` (sale de `main`, NO mergeada aún)
**Dominio:** tuyo (system prompt del chat / `anthropic_service.py`) → por eso queda
para tu review, no lo pusheé a main.
**Impacto:** menor TTFT (tiempo hasta el primer token) y menor costo en el 1er
mensaje de **cada** conversación. **Cero cambio de comportamiento ni de calidad.**

## Qué cambia (1 función)

Solo `_system_with_cache()` en `backend/services/anthropic_service.py`.

**Antes:** el system (`BASE_SYSTEM_PROMPT` + memoria + KB ruteado) viajaba como
**un solo bloque** con `cache_control`. Como la memoria (por usuario) y el KB
(por query, ruteado por dominio) varían, el prefijo cacheable cambiaba casi
siempre → el `BASE` grande y estable (~15k tokens) casi nunca pegaba en cache.

**Ahora:** se parte en dos bloques con breakpoints de cache separados, de estable
a variable:

1. `BASE_SYSTEM_PROMPT` (constante) → **pega en el cache en TODAS las
   conversaciones** (dentro del TTL de 5 min de Anthropic, que se refresca en
   cada uso). El prefijo grande deja de invalidarse por memoria/KB.
2. memoria + KB ruteado (variable) → pega entre las **iteraciones del loop de
   tools del mismo turno** (el `system_payload` se reenvía igual en cada
   iteración), y cross-user si el KB ruteado coincide.

## Por qué NO baja la calidad

Los bloques `text` de un system de Anthropic se concatenan **sin separador**, y
por construcción `bloque1.text + bloque2.text == system` original, byte por byte.
El modelo recibe **exactamente el mismo texto** que antes; lo único que cambia es
cómo se particiona para el caching. Está cubierto por un test:

```
cd backend && python -m pytest tests/test_prompt_cache_split.py --import-mode=importlib -q
```

`test_split_reconstruye_identico_y_estructura` verifica la reconstrucción
byte-idéntica. Regresión de chat/Capa 2: `test_chat.py` + `test_capa2_fixes.py`
(27, verdes).

## Para mergear

Si te cierra: `git checkout main && git merge perf/prompt-cache-split-agus`
(fast-forward) y push. No toca schema, ni migraciones, ni deps. Cualquier duda,
lo hablamos.

## Contexto

Sale de un plan de optimización de latencia (cold start). Las otras patas ya
están en `main` (warmup en el lifespan, KB en paralelo, SWR de noticias, prefetch
de noticias en el front). Esta era la de mayor impacto en el **primer mensaje de
cada chat**, pero como toca tu system prompt, va para tu review.
