# Política de Cookies y Almacenamiento Local — RE Expert


**Versión:** 1.0
**Fecha de última actualización:** {{vigenciaDesde}}

---

## 1. Aclaración inicial: RE Expert no usa cookies

Auditamos el código y lo decimos con precisión: **RE Expert no instala cookies propias
ni de terceros con fines publicitarios, de analítica ni de seguimiento.** No utilizamos
Google Analytics, píxeles de redes sociales ni herramientas de perfilado publicitario.

Lo que sí usamos es **almacenamiento local del navegador** (`localStorage` y
`sessionStorage`), una tecnología distinta de las cookies pero que también guarda
información en tu dispositivo. Por transparencia, la detallamos igual que si fueran
cookies.

---

## 2. Qué guardamos en tu navegador

### 2.1. Almacenamiento técnico o necesario

Imprescindible para que la aplicación funcione. **Sin esto no podrías iniciar sesión ni
usar el Servicio**, por lo que no requiere consentimiento previo.

| Clave | Qué guarda | Duración |
|---|---|---|
| `re_access_token` | Token de sesión de corta duración | ~15 minutos |
| `re_refresh_token` | Token para renovar la sesión sin volver a ingresar la contraseña | Hasta 7 días (hasta 90 en cuentas de administración) |
| `re_user` | Tu identificador, nombre y correo, para mostrarlos en la interfaz | Mientras dure la sesión |
| `re_accounts` | Datos de sesión de las cuentas adicionales que agregues (hasta 5) para poder cambiar entre ellas | Hasta que cierres esas sesiones |
| `re_authed` | Indicador temporal de sesión iniciada (se borra al cerrar la pestaña) | Sesión del navegador |

> ⚠️ **Importante sobre seguridad:** estas claves incluyen credenciales de sesión.
> **No uses la función de múltiples cuentas en computadoras compartidas o públicas**, y
> cerrá sesión al terminar. Ver punto 5.

### 2.2. Almacenamiento de preferencias

Guarda tus elecciones para no volver a preguntártelas. No identifica personas.

| Clave | Qué guarda |
|---|---|
| `re_theme` | Si preferís el tema claro u oscuro |
| `re_animations` | Si activaste o desactivaste las animaciones de fondo |
| `re_onboarding_done` | Si ya completaste la presentación inicial |

### 2.3. Almacenamiento funcional

Guarda trabajo en curso para que no lo pierdas al recargar la página.

| Clave | Qué guarda |
|---|---|
| `re_mat_lista` | Tu lista de materiales en preparación |
| `re_acad_cart`, `re_acad_cart_inflight` | Cursos seleccionados y estado de una compra en curso |
| `re_voice_memory` | Datos que le pediste al asistente de voz que recuerde (por ejemplo tu nombre, tu zona de trabajo o tus preferencias). **Los guarda el asistente a tu pedido y se le envían a OpenAI al iniciar cada conversación por voz** (ver punto 3) |

### 2.4. Lo que NO guardamos

**No hay almacenamiento publicitario, de analítica ni de seguimiento entre sitios**, ni
se usa ninguna de estas claves para construir un perfil publicitario.

**Una excepción que corresponde declarar:** el contenido de `re_voice_memory` se
transmite a OpenAI al comenzar cada conversación por voz, para que el asistente recuerde
lo que le pediste recordar.

---

## 3. Servicios de terceros que cargan recursos en la aplicación

Aunque no instalemos cookies, tu navegador solicita algunos recursos a servidores
externos. **Esos servidores reciben tu dirección IP y datos técnicos de tu navegador**,
por el solo hecho de la solicitud.

| Servicio | Qué recibe | Cuándo | Finalidad |
|---|---|---|---|
| **Google Fonts** (`fonts.googleapis.com`, `fonts.gstatic.com`) | Dirección IP, navegador y página de origen | **En todas las páginas, incluidas las de inicio de sesión y registro** — es decir, **antes de que inicies sesión o aceptes nada** | Tipografías de la interfaz |
| **Google (iconos de sitios)** (`google.com/s2/favicons`) | Dirección IP y **los dominios de las fuentes que se muestran en tus respuestas** | Al mostrarse respuestas con fuentes citadas | Ícono identificatorio de cada fuente |
| **Cloudflare CDN** (`cdnjs.cloudflare.com`) | Dirección IP y navegador | Al visualizar un plano en PDF | Biblioteca del visor de PDF. **Aclaración importante:** el plano **sí se sube a nuestros servidores**, se almacena y se analiza con inteligencia artificial; lo que se descarga de Cloudflare es únicamente el programa que lo muestra en pantalla. El tratamiento del archivo se detalla en la Política de Privacidad |
| **OpenAI** (`api.openai.com`) | Dirección IP, **audio en tiempo real**, la **transcripción de la conversación**, los datos que le pediste recordar (`re_voice_memory`) y los datos de tu cuenta que el asistente consulte para responderte (por ejemplo, el resumen de tus proyectos de planos) | Sólo si usás la conversación por voz en vivo | Voz. La conexión se establece directamente desde tu navegador |

---

## 4. Cómo controlarlo

4.1. **Desde tu navegador** podés borrar el almacenamiento local de este sitio en
cualquier momento (Configuración → Privacidad → Datos de sitios). **Al hacerlo se
cerrará tu sesión** y perderás las preferencias y el trabajo en curso no guardado.

4.2. **Bloquear el almacenamiento técnico impide el funcionamiento del Servicio**: sin
él no es posible mantener una sesión iniciada.

4.3. **Desde la aplicación**, cerrar sesión elimina los datos de sesión de tu
navegador.

4.4. Para bloquear las solicitudes a los servicios del punto 3 podés usar extensiones
de bloqueo, aunque algunas funciones (tipografías, visor de PDF, voz) podrían verse
afectadas.

---

## 5. Recomendación de seguridad

Como el almacenamiento local conserva credenciales de sesión, si usás una computadora
compartida:

- Cerrá sesión al terminar.
- No agregues cuentas adicionales con la función de múltiples cuentas.
- Preferí una ventana de navegación privada.

---

## 6. Cambios y contacto

Actualizaremos esta Política ante cambios en las tecnologías utilizadas, con aviso en
la aplicación. Consultas: {{email}}.
