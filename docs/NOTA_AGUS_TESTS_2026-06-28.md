# Nota para Agus (Claude) — 3 tests en rojo, dominio tuyo

> De: Mati + Claude · 2026-06-28. Al hacer una auditoría completa post-reskin
> (frontend), corrimos toda la suite de backend. **~298 tests verdes.** Tres
> quedaron en rojo, **todos en tu dominio (backend) y NO causados por el reskin**
> (nuestros cambios fueron solo frontend: `app.css` + `app.html`). Te los dejamos
> acá para que tu Claude los mire cuando hagas retrieve. **No los tocamos** (no
> es nuestro dominio).

## Cómo reproducir
```
cd backend
python -m pytest tests/test_context_router.py tests/test_https.py --import-mode=importlib -q
```

## 1. `test_context_router.py::test_classify_query_typical` (×2) 🟠
El clasificador de dominio manda 2 queries a la categoría equivocada:
- `"¿Cuánto sale el m2 de construcción en CABA?"` → el test espera **`costos`** (devuelve otra).
- `"Cómo funciona el Distrito Tecnológico CABA?"` → el test espera **`estrategia`** (devuelve otra).

Es `services/context_router.py` (el router de contexto que inyecta el KB por
tema). Puede ser que el clasificador necesite ajuste de keywords, o que el test
quedó desactualizado respecto a tu última lógica. Mirá cuál de los dos.

## 2. `test_https.py::test_http_request_is_redirected_to_https` 🟠
Falla la aserción del redirect HTTP→HTTPS (infra, `main.py` / middleware
`_HTTPSRedirectExceptHealth`). Puede ser env-dependiente del TestClient o algo
que cambió. Verificá que el redirect a HTTPS siga andando en prod (es seguridad).

---

**Contexto del reskin (lo nuestro, ya en `main`):** tema naranja teja `#BE5103`,
chat en burbujas + fondo de skyline de edificios, y un par de ajustes visuales.
Todo CSS/markup, sin tocar lógica de chat ni backend. Si algo del frontend te
hace ruido, avisá. El estado completo está en `docs/HANDOFF_2026-06-22.md`.
