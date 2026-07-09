# Activar la voz premium del Chat Experto (STT + TTS de OpenAI)

La voz del Chat Experto tiene dos niveles y **el switch es automático**:

- **Sin configurar** (hoy): usa el micrófono y las voces del navegador (gratis,
  solo Chrome/Edge/Safari, calidad de voz según el sistema operativo).
- **Configurada**: graba el audio y lo transcribe con Whisper de OpenAI, y las
  respuestas se leen con una voz neuronal de OpenAI. Un solo permiso estándar
  de micrófono, funciona en todos los navegadores, mucho mejor en español.

El cerebro NO cambia: la consulta transcripta entra por el mismo `/api/chat`
de siempre. OpenAI solo convierte audio ↔ texto.

## Pasos (los hace Agustín, ~10 minutos)

1. Crear cuenta / iniciar sesión en https://platform.openai.com
2. **Billing** → cargar crédito prepago (con USD 10 alcanza para arrancar) y
   configurar un **límite de gasto mensual** (recomendado: USD 20).
3. **API keys** → *Create new secret key* → copiarla (empieza con `sk-`).
4. En **Railway** → servicio del backend → **Variables** → agregar:
   - `OPENAI_API_KEY` = la key
   (el redeploy es automático al guardar)
5. Probar: recargar la app → Chat Experto → tocar el 🎤 → dictar → debería
   transcribir con la voz premium. En el modo "Hablar con el experto" la voz
   de respuesta pasa a ser la neuronal.

## Variables opcionales (ya tienen defaults razonables)

| Variable | Default | Para qué |
|---|---|---|
| `OPENAI_STT_MODEL` | `gpt-4o-mini-transcribe` | Transcripción. Alternativa: `whisper-1` |
| `OPENAI_TTS_MODEL` | `gpt-4o-mini-tts` | Voz. Alternativa: `tts-1` |
| `OPENAI_TTS_VOICE` | `nova` | Otras: `alloy`, `coral`, `sage`, `onyx`, `shimmer` |

## Costos de referencia

- Transcribir: ~US$ 0,003 por minuto hablado.
- Voz de respuesta: ~US$ 0,015 por minuto de audio.
- Conversación en modo Hablar: ~US$ 0,01/minuto (+ los tokens de Claude de
  siempre). 100 usuarios × 20 min/mes ≈ US$ 20–30/mes.

## Seguridad

- La key vive SOLO en Railway (nunca en el frontend ni en el repo).
- Los endpoints `/api/voice/*` requieren sesión activa y plan vigente
  (mismo gate `require_access` que el resto de la app).
- Límite de 8 MB por audio; el texto a voz se corta en 4.000 caracteres por
  pedido (se encadena por oraciones para respuestas largas).
