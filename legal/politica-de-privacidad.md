# Política de Privacidad — RE Expert

> ## ⚠️ BORRADOR — Requiere revisión de abogado matriculado antes de su publicación
>
> Redactado sobre una auditoría técnica del código fuente de RE Expert. **No constituye
> asesoramiento legal.** Debe ser revisado y aprobado por un profesional matriculado
> antes de publicarse.
>
> **Advertencia de exactitud:** este documento describe el comportamiento del código a
> la fecha de la auditoría. Varias integraciones dependen de variables de entorno que
> sólo pueden verificarse en el panel de producción. Los puntos marcados
> **[CONFIRMAR CON TITULAR]** deben validarse contra la configuración real **antes** de
> publicar: declarar un proveedor que no se usa es inexacto, y omitir uno que sí se usa
> es una infracción.

**Versión:** 1.3 (borrador)
**Fecha de última actualización:** [CONFIRMAR CON TITULAR]
**Marco normativo:** Ley 25.326 de Protección de los Datos Personales, su Decreto
Reglamentario 1558/2001 y las resoluciones de la Agencia de Acceso a la Información
Pública (AAIP).

---

## 1. Quiénes somos

**Responsable de la base de datos:** [CONFIRMAR CON TITULAR — razón social o nombre
completo], CUIT [CONFIRMAR CON TITULAR], con domicilio en [CONFIRMAR CON TITULAR].

**Contacto para cuestiones de privacidad y ejercicio de derechos:**
`contacto@re-expert.app` [CONFIRMAR CON TITULAR — ver advertencia]

> **[CONFIRMAR CON TITULAR]** ⚠️ **Casilla de contacto.** Verificar que esta dirección
> exista, reciba y sea leída. Hoy figura únicamente como texto en el código y el envío
> de correos depende de una clave de servicio que puede no estar configurada. **Un canal
> de contacto que no funciona vacía de contenido todo el punto 9 (derechos ARCO)**, cuyo
> plazo legal de respuesta es de 10 días corridos.

> **[CONFIRMAR CON TITULAR]** ⚠️ La Ley 25.326 (art. 21) exige **inscribir la base de
> datos en el Registro Nacional de Bases de Datos Personales** de la AAIP. Es un
> trámite gratuito y previo al tratamiento. Verificar si está hecho; si no, hacerlo
> antes de publicar esta política. Su omisión es sancionable con independencia del
> contenido de este documento.

---

## 2. Resumen honesto (lo importante en 8 líneas)

- Guardamos **todo lo que escribís en el chat**, y lo conservamos mientras tu cuenta
  exista.
- **El contenido de tus conversaciones, tus planos y la información de tus proyectos se
  envía a proveedores de inteligencia artificial ubicados en Estados Unidos** (Anthropic
  y, según configuración, Google u OpenAI). Sin eso, el producto no funciona.
- Tus datos se alojan en servidores de **Estados Unidos** (Supabase, Railway, Netlify).
- **No vendemos tus datos.** No hacemos publicidad con ellos ni los cedemos a terceros
  con fines comerciales.
- **Sí analizamos tu uso de forma identificada** para mejorar el producto (ver 5.4);
  podés oponerte.
- **No tocamos los datos de tu tarjeta**: los procesa la pasarela de pago.
- Podés **descargar una copia de tus datos** y **eliminar tu cuenta** desde la
  aplicación; si tenés un período pago vigente, la baja implica renunciar a los días
  restantes. Se hace efectiva a los 30 días.
- Si cargás datos de otras personas (contactos, clientes, proveedores), **la
  responsabilidad de tener permiso para hacerlo es tuya** (ver 4.4).

---

## 3. Qué datos tratamos

### 3.1. Datos que nos das al registrarte y usar la cuenta

| Dato | Obligatorio | Finalidad |
|---|---|---|
| Nombre y apellido | Sí | Identificación, personalización, comunicaciones |
| Correo electrónico | Sí | Identificador de cuenta, autenticación, avisos, recuperación |
| Contraseña | Sí | Autenticación. **Se guarda hasheada con bcrypt y sal, nunca en texto legible** |
| Teléfono | No | Avisos y contacto. Podés cargarlo vos o pedírselo al Asistente |
| Secreto y códigos de verificación en dos pasos | No (opt-in) | Segundo factor de autenticación. **El secreto se guarda cifrado** |

### 3.2. Contenido que generás usando el Servicio

| Dato | Detalle |
|---|---|
| **Conversaciones completas** | Todos los mensajes que escribís y las respuestas recibidas, con su título y sección |
| **Memoria del Asistente** | Datos que el sistema guarda automáticamente para recordar tu contexto: perfil profesional, preferencias, y por proyecto: dirección, lote, superficies, indicadores urbanísticos, y **nombres de clientes o inversores y montos en negociación** cuando los mencionás. Ver el punto 6 sobre cómo se decide qué se guarda |
| **Planos y documentación** | Archivos PDF o imagen que subís (hasta 8 MB). Suelen contener nombre del comitente, matrícula profesional, domicilio de obra y número de expediente |
| **Proyectos de obra** | Presupuestos, costos reales, avance, hitos, materiales y notas |
| **Pagos de obra** | Concepto, **nombre del proveedor**, monto, fecha y estado (registro de gastos de tu obra, distinto de tu pago del Servicio) |
| **Oportunidades / Deal Room** | Zona, ciudad, precios, puntajes y notas |
| **Contactos** | Ver punto 4.4 — datos de terceros |
| **Reportes de error** | Título, descripción y contexto técnico de tu navegador (versión, idioma, resolución, tema, hora local y pantalla donde ocurrió), que se te informa al enviarlos |

### 3.3. Datos que se generan automáticamente

| Dato | Finalidad |
|---|---|
| Fecha del último acceso, estado y vigencia de tu acceso al Servicio | Operación del servicio y control de acceso |
| **Registro de consumo de modelos de IA** (modelo usado, cantidad de tokens y costo por consulta) | Control de costos y de límites de uso |
| **Eventos de interés en cursos y materiales, asociados a tu cuenta** | Mejora del producto y de la oferta (ver 5.4) |
| **Ubicación geográfica**, si la autorizás en el navegador: latitud y longitud tal como las informa tu dispositivo | Resolver el nombre de tu zona para buscar corralones y precios de materiales |
| Datos técnicos de conexión (dirección IP, navegador) | Seguridad, prevención de abuso y funcionamiento |

> **Cómo se trata tu ubicación.** Hoy la coordenada se usa en el momento y **no se
> almacena**: tu navegador se la envía a nuestro servidor, que la **redondea a unos 110
> metros antes** de consultar al servicio de mapas que devuelve el nombre de tu localidad
> (punto 7.3). La Plataforma incluye además una función de **historial de ubicaciones**
> —hasta 500 posiciones de los últimos 90 días, guardadas con la precisión que informe tu
> dispositivo— que **requiere tu consentimiento específico y todavía no está habilitada
> en la interfaz**. Si la habilitamos te lo vamos a informar, y vas a poder elegir entre
> precisión exacta o aproximada y purgar el historial.

### 3.4. Datos de facturación

Cuando contratás el Servicio se registra el **hecho del pago** (fecha, importe, estado e
identificadores que devuelve la pasarela), y si un cobro se rechaza, **el motivo que nos
informa el procesador** y la fecha, para poder avisarte y darte el período de gracia.

**Tarjetas guardadas.** Si guardás una tarjeta para la suscripción, conservamos
únicamente: la **marca** (Visa, Mastercard…), los **últimos cuatro dígitos**, el
**mes y año de vencimiento**, el **nombre del titular tal como lo ingresaste** y un
**identificador que nos devuelve Mercado Pago** para poder operar el cobro.

> **Lo que NO guardamos, y no es una promesa vacía sino cómo está construido:** el
> número completo de la tarjeta y el código de seguridad **nunca llegan a nuestros
> servidores**. Cuando cargás una tarjeta, los campos donde escribís pertenecen al
> procesador de pago —están incrustados en nuestra pantalla pero son suyos—, y esos
> datos viajan de tu navegador directo a él. Lo único que nuestro sistema recibe es un
> código de un solo uso. Por eso tampoco podemos "recuperar" ni mostrarte tu número de
> tarjeta: no lo tenemos.

### 3.5. Datos que NO tratamos

- **No guardamos los datos de tu tarjeta de crédito o débito.**
- **No solicitamos ni queremos datos sensibles** (salud, origen étnico, opiniones
  políticas, convicciones religiosas, afiliación sindical, vida sexual). Su carga está
  prohibida por los Términos.
- **Las imágenes que adjuntás al chat no se almacenan**: se envían al proveedor de IA
  para su análisis y se descartan de nuestros sistemas; en la conversación queda sólo
  una referencia a que hubo un adjunto.
- **Filtramos los datos financieros antes de que entren en la memoria automática:** un
  control del servidor detecta y descarta patrones de CBU/CVU, alias bancarios, números
  de tarjeta, códigos de seguridad y contraseñas, para que el Asistente no los persista
  en su memoria. **Atención: ese control alcanza a la memoria, no al chat.** Si escribís
  uno de esos datos en una conversación, el mensaje se guarda como cualquier otro
  (punto 3.2) y se transmite al proveedor de inteligencia artificial (punto 7.1). Es un
  filtro automático por patrones, pensado para los casos habituales; no lo presentamos
  como infalible. **No cargues datos bancarios ni contraseñas en el chat.**

---

## 4. Base legal y consentimiento

4.1. Tratamos tus datos sobre la base de:

a) **Tu consentimiento libre, expreso e informado** (art. 5 Ley 25.326), que prestás al
registrarte y aceptar esta Política.

b) La **necesidad para la ejecución del contrato** que celebrás al contratar el Servicio
(art. 5 inc. 2.d).

c) El **cumplimiento de obligaciones legales** que pesan sobre el Titular (fiscales,
contables y de respuesta a requerimientos de autoridad competente).

d) El **interés legítimo** del Titular en garantizar la seguridad del Servicio, prevenir
fraudes y abusos, y ejercer o defender derechos ante reclamos.

4.2. **Revocación.** Podés revocar tu consentimiento en cualquier momento, lo que
implicará la baja del Servicio, ya que sin tratamiento de datos no es técnicamente
posible prestarlo. La revocación **no afecta la licitud del tratamiento previo** ni los
tratamientos que se apoyen en las bases (c) y (d).

4.3. **Registro del consentimiento.** Conservamos constancia de cuándo aceptaste esta
Política y qué versión aceptaste, como prueba del consentimiento prestado.

> **[CONFIRMAR CON TITULAR]** ⚠️ Esta constancia **todavía no se registra**. El art. 5
> de la Ley 25.326 exige que el consentimiento sea probado por el responsable, y en una
> inspección lo primero que se pide es esa evidencia. **Antes de publicar** hay que
> guardar, al momento del alta: fecha y hora, versión del documento aceptado y dirección
> IP. Es una columna y un registro — barato de hacer, caro de no tener.

### 4.4. Datos de terceros que vos cargás — leer con atención

> La Plataforma te permite cargar datos de personas que no son usuarias: **contactos
> (nombre, teléfono, correo), el comitente o cliente de un proyecto de planos, los
> proveedores de tus pagos y los responsables asignados a tareas.**

4.4.1. **Respecto de esos datos, vos sos el responsable del tratamiento y nosotros
actuamos como encargados**, tratándolos únicamente para prestarte el Servicio y según
tus instrucciones.

4.4.2. Al cargarlos, **declarás y garantizás** contar con base legal suficiente y haber
informado a esas personas, conforme a la cláusula 9.3 de los Términos, y **nos mantenés
indemnes** por cualquier reclamo derivado del incumplimiento de esa declaración.

4.4.3. **Estos datos también se transmiten a los proveedores de inteligencia
artificial** descriptos en el punto 7, en la medida en que el Asistente necesite
consultarlos para responderte.

4.4.4. **Se eliminan junto con tu cuenta**, en los términos del punto 8.

4.4.5. **Si sos una de esas personas** y querés ejercer derechos sobre datos tuyos que
un usuario cargó, escribinos a `contacto@re-expert.app`. Daremos intervención al
usuario responsable y atenderemos el pedido conforme a la ley.

---

## 5. Para qué usamos tus datos

> Enumeramos las finalidades de forma completa y expresa. Un tratamiento que no esté
> acá no está amparado por tu consentimiento.

5.1. **Prestar el Servicio:** procesar tus consultas, generar respuestas, análisis,
estimaciones e informes, guardar tu trabajo, mantener tu sesión y ejecutar las acciones
que le pidas al Asistente.

5.2. **Administrar tu cuenta:** autenticación, recuperación de contraseña, verificación
en dos pasos, gestión del acceso y de tu contratación, y emisión de comprobantes.

5.3. **Comunicaciones operativas:** avisos de seguridad, cambios en el servicio,
vencimientos, y los recordatorios que vos configurés. **No son publicidad y no podés
desuscribirte de las estrictamente necesarias para la relación contractual.**

5.4. **Mejorar y desarrollar el Servicio (tratamiento identificado).**
Analizamos cómo usás la Plataforma —incluyendo qué secciones, cursos y materiales te
interesan, asociado a tu cuenta— para corregir errores, medir el uso de cada
funcionalidad, priorizar el desarrollo de funciones nuevas, ajustar la calidad de las
respuestas y orientar la oferta de contenidos.
**Este tratamiento es identificado, no anónimo, y así lo declaramos.**
**Podés oponerte** escribiendo a `contacto@re-expert.app`, sin que ello afecte tu acceso
al Servicio.

> **[REVISIÓN LEGAL]** Este tratamiento excede la mera ejecución del contrato, por lo
> que requiere consentimiento informado diferenciado y un mecanismo efectivo de
> oposición. Se recomienda instrumentar la oposición como un interruptor en
> Configuración, no sólo por correo.

5.5. **Seguridad, prevención de fraude y abuso:** detectar accesos no autorizados,
limitar peticiones abusivas, prevenir usos indebidos e investigar incidentes.

5.6. **Cumplimiento legal:** responder requerimientos de autoridad judicial o
administrativa competente y cumplir obligaciones fiscales y contables.

5.7. **Ejercicio y defensa de derechos:** conservar y utilizar la información
estrictamente necesaria para atender reclamos, ejercer derechos o defendernos ante
acciones legales, propias o de terceros.

5.8. **Elaboración de información agregada y anonimizada**, en los términos del punto 12.

5.9. **NO usamos tus datos para:** venderlos, cederlos con fines comerciales, publicidad
de terceros, ni para adoptar decisiones automatizadas que produzcan efectos jurídicos
sobre vos o te afecten significativamente de modo similar.

---

## 6. Tratamiento automatizado e inteligencia artificial

> Este punto describe algo que conviene entender bien: **parte del tratamiento lo decide
> un sistema automatizado, no una persona.**

6.1. **Generación de respuestas.** Tus consultas se procesan con modelos de lenguaje de
terceros que generan las respuestas de forma automática. Esas respuestas **pueden ser
inexactas o incompletas**; su alcance y limitaciones están descriptos en la cláusula 3 de
los Términos y Condiciones.

6.2. **Memoria automática.** El sistema puede **decidir por sí mismo guardar información
de tus conversaciones** para recordar tu contexto en intercambios posteriores (por
ejemplo, tu perfil profesional, la dirección de una obra o los datos de un proyecto),
sin pedirte confirmación en cada caso.

- **Control técnico:** un filtro del servidor detecta y descarta patrones de datos
  financieros y credenciales **antes** de persistirlos en la memoria. Es un control
  automático por patrones, no una garantía absoluta, y **no alcanza al texto de la
  conversación** (ver 3.5).
- **Tu control:** podés ver, corregir y eliminar lo que el Asistente recordó, en
  cualquier momento y desde la propia aplicación.

6.3. **Valoraciones automatizadas.** El análisis de planos genera de forma automática
puntajes, niveles de riesgo y observaciones. **Son estimaciones de una herramienta
informática, no dictámenes profesionales**, y no adoptamos ninguna decisión sobre vos a
partir de ellas. **Podés impugnar, corregir o descartar cualquiera de esas
valoraciones** desde la aplicación o escribiéndonos.

> **[REVISIÓN LEGAL]** Declarar el tratamiento automatizado y el derecho a impugnar
> valoraciones (art. 20 Ley 25.326) es lo que evita el reproche por omisión. Validar si,
> dada la naturaleza del producto, corresponde algún recaudo adicional.

---

## 7. Con quién compartimos tus datos

> **Esta es la sección más importante del documento.** Para funcionar, RE Expert
> transmite información a proveedores externos. **La mayoría está en Estados Unidos**,
> país que no ha sido declarado con nivel adecuado de protección por la autoridad
> argentina.

### 7.1. Proveedores de inteligencia artificial

| Proveedor | Qué recibe | País |
|---|---|---|
| **Anthropic** (modelos Claude) | **El contenido íntegro de tus consultas y de los últimos mensajes de la conversación; tu memoria de perfil y de proyecto; los planos e imágenes que cargues; y los datos de proyecto necesarios para responderte** | Estados Unidos |
| **Google** (modelos Gemini) *[CONFIRMAR CON TITULAR: activo sólo si está configurada la clave correspondiente]* | Lo mismo que el anterior, cuando el Asistente opera con este proveedor | Estados Unidos |
| **OpenAI** *[CONFIRMAR CON TITULAR: activo sólo si está configurada la clave]* | **El audio de tu micrófono** para transcripción y el texto de las respuestas para generar voz. En el modo de conversación por voz en tiempo real recibe además: **(a)** tu dirección IP, porque la conexión se establece directamente desde tu navegador; **(b)** la **transcripción completa de la conversación**; y **(c)** la memoria que el asistente de voz guardó sobre vos y **los datos de tus proyectos que consulta para responderte**, que pueden incluir nombres de clientes o inversores y montos, conforme al punto 3.2 | Estados Unidos |

7.1.1. **Estos proveedores procesan tus datos para generar la respuesta y devolverla.**
No los utilizamos para que entrenen modelos por nuestra cuenta.

7.1.2. **Ficha de contexto en cada intercambio con el Asistente.** Junto con tu consulta
le enviamos automáticamente al proveedor de inteligencia artificial una ficha con: tu
**nombre** (o tu **correo electrónico**, si no cargaste nombre), tu **plan contratado**,
si tenés Telegram vinculado, la cantidad de contactos que cargaste, y un resumen de tus
**proyectos** (nombre, avance, presupuesto y costo real), tus **pagos pendientes**
(concepto, monto y fecha), tus **recordatorios** próximos y tus **oportunidades** con su
puntaje.

**Esta ficha se envía en todos los intercambios con el Asistente, aunque tu consulta no
tenga relación con esos datos**, para que pueda responderte con tu contexto. Si además le
pedís que gestione tu perfil, recibe también tu **teléfono**.

> **[CONFIRMAR CON TITULAR]** ⚠️ **Crítico.** Debe verificarse con cada proveedor y
> documentarse: (a) si la cuenta contratada es de tipo comercial/API, (b) si existe
> compromiso de **no utilizar los datos para entrenamiento**, y (c) cuál es el **plazo
> de retención** en su infraestructura. En particular, **los niveles gratuitos de
> algunos proveedores permiten expresamente el uso de los contenidos para mejorar sus
> modelos**: si se estuviera usando un nivel gratuito, esta declaración sería inexacta y
> debería corregirse antes de publicar.

### 7.2. Infraestructura

| Proveedor | Qué recibe | País |
|---|---|---|
| **Supabase** | Base de datos y almacenamiento: **todos** los datos descriptos en el punto 3 | Estados Unidos |
| **Railway** | Ejecución del backend y registros de aplicación | Estados Unidos |
| **Netlify** | Distribución de la interfaz web; registros de acceso (IP, navegador) | Estados Unidos |

### 7.3. Otros proveedores

| Proveedor | Qué recibe | Estado |
|---|---|---|
| **Mercado Pago / Stripe** | Tu correo, tu nombre y un identificador interno de tu cuenta, para asociar el pago. Si guardás una tarjeta, **los datos de la tarjeta los recibe el procesador directamente desde tu navegador** y los conserva en su bóveda: nosotros sólo manejamos la referencia (ver 3.4) | Según configuración del medio de pago |
| **Resend** | Tu correo, tu nombre y el contenido de los mensajes transaccionales (códigos de verificación, enlaces de recuperación) | *[CONFIRMAR CON TITULAR]* |
| **OpenStreetMap / Nominatim** | Tu ubicación **redondeada a unos 110 metros antes de enviarse** —suficiente para identificar la localidad y no tu domicilio—, si autorizás la geolocalización. La coordenada exacta no sale de nuestros sistemas | **Activo** (Unión Europea / Reino Unido) |
| **Google Maps** | Las direcciones que le indicás al Asistente para optimizar recorridos | *[CONFIRMAR CON TITULAR]* |
| **Tavily** | El texto de la búsqueda que el sistema construye a partir de tu consulta y, para precios de materiales, tu zona | *[CONFIRMAR CON TITULAR]* |
| **Telegram** | Tu identificador de chat y el contenido de los avisos que pidas recibir por ese canal. **Si además activás la conversación con el Asistente por Telegram**, el contenido de los mensajes que le escribas y de sus respuestas | *[CONFIRMAR CON TITULAR]* |

7.3.1. **Servicios de terceros embebidos en la interfaz.** Al cargar cualquier página,
tu navegador solicita tipografías a **Google Fonts**, y al abrir el visor de planos
descarga la biblioteca de lectura de PDF desde el CDN de **Cloudflare**. En ambos casos
esos proveedores **reciben tu dirección IP y datos de tu navegador**; el primero, incluso
antes de que inicies sesión. Ver la Política de Cookies.

7.3.2. **Consultas a fuentes públicas.** Para mostrarte cotizaciones, noticias y datos
oficiales consultamos fuentes públicas (BCRA, portales de datos abiertos, medios). **No
les enviamos datos personales tuyos.**

7.3.3. **Políticas propias de cada proveedor.** Cada uno de estos terceros trata la
información conforme a sus propias políticas de privacidad, sobre las que no tenemos
control. Seleccionamos proveedores con estándares de seguridad reconocidos en la
industria, pero **no respondemos por incumplimientos que les sean exclusivamente
imputables.**

### 7.4. Contenido que compartís vos

Cuando generás un informe y decidís compartirlo, el sistema crea un **enlace temporal
(48 horas) que no requiere iniciar sesión**: quien tenga ese enlace puede ver el
documento mientras esté vigente. **La decisión de compartirlo y con quién es tuya, y esa
comunicación queda fuera de nuestro control.**

### 7.5. Otras comunicaciones

Podemos comunicar datos a autoridades judiciales o administrativas competentes cuando
exista requerimiento legal, y a asesores profesionales obligados a confidencialidad. En
caso de reorganización societaria o transferencia del negocio, los datos podrían
transferirse al continuador, **notificándotelo previamente**.

### 7.6. Transferencia internacional de datos

7.6.1. Como surge de los cuadros anteriores, **tus datos se transfieren fuera de la
Argentina**, principalmente a Estados Unidos.

7.6.2. El art. 12 de la Ley 25.326 prohíbe la transferencia a países que no
proporcionen niveles de protección adecuados, **salvo** —entre otros supuestos— que el
titular haya prestado **consentimiento expreso e informado**, o que la transferencia
sea necesaria para la ejecución del contrato entre el titular y el responsable.

7.6.3. **Al aceptar esta Política prestás tu consentimiento expreso e informado a estas
transferencias**, que además son imprescindibles para prestarte el Servicio: sin ellas,
la Plataforma no puede funcionar.

> **[REVISIÓN LEGAL]** ⚠️ **Punto de máxima exposición del documento.** Corresponde
> validar: (a) la suficiencia del consentimiento como base de legitimación bajo la
> Resolución AAIP 60/2016, (b) la conveniencia de suscribir **cláusulas contractuales
> tipo** o adherir a los DPA que ofrecen estos proveedores, y (c) la documentación de
> cada acuerdo. Hoy **no existe ningún contrato de tratamiento firmado en el repositorio
> del proyecto**. Ver "Riesgos detectados en el código", ítem R2.

---

## 8. Cuánto tiempo conservamos tus datos

8.1. **Mientras tu cuenta exista.** Tus conversaciones, proyectos, planos y demás
contenido se conservan mientras mantengas la cuenta activa: **no les aplicamos un plazo
de borrado por antigüedad**, y así lo declaramos de forma honesta.

Sí aplicamos borrado automático, por diseño, a dos categorías:

- **Historial de ubicaciones** (cuando la función esté habilitada, ver 3.3): se
  conservan los últimos 90 días con un máximo de 500 registros; el excedente se elimina
  automáticamente en cada nueva captura.
- **Recordatorios ya enviados, fallidos o cancelados:** se eliminan a los 30 días.

8.2. **Borrado a tu pedido.** Podés eliminar conversaciones individualmente cuando
quieras y borrar archivos desde Configuración → Almacenamiento. Para purgar el historial
de ubicaciones, escribinos a `contacto@re-expert.app`: el control autoservicio está
desarrollado pero todavía no expuesto en la aplicación.

8.3. **Al dar de baja la cuenta:** se desactiva de inmediato y, transcurridos **30 días
corridos**, se elimina de forma definitiva junto con conversaciones y mensajes,
proyectos, hitos y presupuestos, planos y sus archivos, pagos de obra, contactos,
memoria del asistente, oportunidades, recordatorios, canales de notificación,
ubicaciones, registros de consumo y **el correo asociado a los reportes de error que
hayas enviado**. **Es un borrado real, no una marca de "eliminado".** Si iniciás sesión
dentro de esos 30 días, la baja se cancela.

El borrado alcanza a los datos alojados en nuestros servidores. **La memoria que el
asistente de voz guarda en tu propio navegador** se elimina al cerrar sesión, y también
podés borrarla vos limpiando los datos del sitio (ver Política de Cookies).

8.4. **Qué sobrevive a la baja — declaración honesta de excepciones:**

| Qué | Por qué | Plazo |
|---|---|---|
| **Documentos generados** (informes PDF/planillas) alojados en el almacenamiento de archivos | Se generan sin vínculo con tu cuenta, por lo que técnicamente no pueden identificarse para su borrado selectivo | *[CONFIRMAR CON TITULAR]* |
| **Copias de seguridad** | Rotación técnica del proveedor de base de datos | Según el plan contratado *[CONFIRMAR CON TITULAR]* |
| **Registros técnicos (logs)** | Diagnóstico y seguridad. **No registramos tu correo al purgar la cuenta** | Según retención del proveedor de hosting *[CONFIRMAR CON TITULAR]* |
| **Reportes de error, disociados de tu cuenta** | Conservar el seguimiento de un problema técnico. Al purgar la cuenta se elimina tu correo y se corta el vínculo con tu usuario. **Se conservan el título, la descripción y las notas que escribiste, y el contexto técnico de tu navegador** (navegador y versión, idioma, resolución, tema, hora local y pantalla donde ocurrió), que no te identifican por sí solos pero podrían contribuir a identificarte si se cruzaran con otra información. No los cruzamos con ninguna otra base para reidentificarte, y **si escribiste datos personales en el texto, pedinos que lo depuremos** | Indefinido, en forma disociada |
| Información necesaria para **ejercer o defender derechos** ante un reclamo existente o previsible | Base legal del punto 4.1.d | Mientras dure el reclamo y el plazo de prescripción aplicable |

> **[CONFIRMAR CON TITULAR]** ⚠️ **Registros contables.** Este cuadro **no incluye** una
> excepción por conservación de comprobantes fiscales, porque hoy el código **borra
> también los pagos y las compras** al eliminar la cuenta (relación en cascada). Si el
> Titular necesita conservar respaldo contable por 10 años (art. 328 CCyC), hay que
> implementarlo como una tabla desvinculada de la cuenta y **recién entonces** declararlo
> acá. Declarar una retención que no ocurre es tan riesgoso como omitir una que sí.

---

## 9. Tus derechos (Acceso, Rectificación, Actualización y Supresión)

9.1. Como titular de los datos tenés derecho a:

- **Acceder** gratuitamente a tus datos, en intervalos no menores a seis meses (art. 14
  Ley 25.326).
- **Rectificar, actualizar o suprimir** los datos inexactos o cuyo tratamiento no se
  ajuste a la ley (art. 16).
- **Oponerte** a tratamientos no necesarios para la ejecución del contrato, como el
  descripto en 5.4.
- **Impugnar valoraciones** producidas por tratamiento automatizado (art. 20), conforme
  al punto 6.3.
- **Revocar tu consentimiento**, con el efecto previsto en 4.2.

9.2. **Ejercelos vos mismo, sin trámite.** Desde la aplicación podés:

- **Descargar una copia de tus datos** en un archivo, desde Configuración → Cuenta
  (`Exportar mis datos`). Incluye los datos de tu cuenta, conversaciones y mensajes,
  proyectos de obra, pagos, presupuestos, hitos, materiales y listas, proyectos y fichas
  de planos con sus análisis, observaciones y tareas, espacios de trabajo y memoria del
  Asistente, contactos, oportunidades, recordatorios, canales de notificación,
  ubicaciones y sus preferencias, compras de cursos, tus intereses registrados, el
  consumo de modelos de IA y tus reportes de error. **No incluye** el archivo binario de
  los planos —que se descarga de a uno desde Configuración → Almacenamiento— ni tus
  credenciales (contraseña, secreto y códigos del doble factor), porque exportarlas
  sería crear una vía de fuga.
- **Modificar** tu nombre, correo electrónico y teléfono, y cambiar tu contraseña.
- **Borrar** conversaciones y archivos individualmente. Para purgar el historial de
  ubicaciones, escribinos a `contacto@re-expert.app` y lo hacemos en los plazos del
  punto 9.3.
- **Ver y corregir** lo que el Asistente recordó sobre vos.
- **Solicitar la eliminación** de tu cuenta.

> **Si tenés un período pago vigente**, la aplicación no acepta el pedido de baja hasta
> que ese período venza o lo canceles. Es un recaudo para que no quede un cobro sin
> cuenta asociada, **no una limitación de tu derecho de supresión**: si querés ejercerlo
> igual, escribinos a `contacto@re-expert.app` y lo tramitamos nosotros dentro de los
> plazos del punto 9.3.

9.3. **Si preferís escribirnos**, hacelo a `contacto@re-expert.app` desde el correo
registrado. **Responderemos dentro de los 10 días corridos** para pedidos de acceso y de
los 5 días hábiles para rectificación o supresión, conforme a los arts. 14 y 16 de la
Ley 25.326.

9.4. **Autoridad de control.** La **Agencia de Acceso a la Información Pública** es el
órgano de control de la Ley 25.326 y tiene atribuciones para atender denuncias respecto
del incumplimiento de las normas de protección de datos personales.

---

## 10. Cómo protegemos tus datos

10.1. **Medidas implementadas** (descripción honesta de lo que existe):

- Comunicaciones cifradas mediante **HTTPS** con redirección forzada.
- Contraseñas almacenadas con **función de hash bcrypt con sal**; nunca en texto
  legible ni recuperables por nosotros.
- Autenticación mediante **tokens de vigencia limitada**, con mecanismo de invalidación
  global de todas las sesiones ante el cambio de contraseña.
- **Verificación en dos pasos opcional** mediante aplicación de autenticación o código
  por correo, con códigos de recuperación de un solo uso. **El secreto del segundo
  factor se almacena cifrado**, de modo que no resulte utilizable ante un acceso
  indebido a la base de datos.
- **Aislamiento por cuenta**: las consultas de la aplicación a datos de usuario filtran
  por el identificador de la cuenta, de modo que ningún usuario puede acceder a los
  datos de otro. Un número acotado de **administradores del Servicio, sujetos a deber de
  confidencialidad**, puede acceder a los reportes de error que envíes —incluido tu
  correo— para poder responderlos, y a estadísticas de uso de cursos y materiales.
- **Enlaces firmados y con vencimiento** para los informes que se comparten fuera de la
  aplicación, de modo que no puedan descubrirse por tanteo.
- **Filtrado de datos financieros** en la memoria automática (ver 6.2).
- **Minimización de la ubicación**: las coordenadas se redondean antes de enviarse a un
  tercero para resolver el nombre de tu zona.
- **Límites de tasa** de peticiones para prevenir abuso y ataques de fuerza bruta.
- Cabeceras de seguridad y **política de seguridad de contenidos (CSP)**.
- Validación y saneamiento de las entradas del usuario.
- Cifrado en reposo y en tránsito provisto por el proveedor de base de datos.

10.2. **Compromiso de medios.** Nos obligamos a aplicar medidas razonables y adecuadas
al estado de la técnica. **No garantizamos seguridad absoluta**: ningún sistema conectado
a internet puede garantizarla, y cualquier afirmación en contrario sería falsa.

10.3. **Tu parte.** Usá una contraseña robusta y única, activá la verificación en dos
pasos, no uses la función multicuenta en dispositivos compartidos y cuidá con quién
compartís los enlaces de tus informes.

10.4. **Notificación de incidentes.** Ante un incidente de seguridad que afecte
significativamente tus datos personales, te lo notificaremos al correo registrado **sin
dilación indebida y, como criterio general, dentro de las 72 horas de detectado**,
informando la naturaleza del incidente, las categorías de datos afectadas, las medidas
adoptadas y las recomendaciones a tu alcance. Daremos aviso a la autoridad de control
cuando corresponda.

> **[CONFIRMAR CON TITULAR]** No incluir en esta sección afirmaciones sobre **copias de
> seguridad** hasta verificar que existen y que se probó una restauración. La
> documentación del proyecto indica que, en el plan actual del proveedor de base de
> datos, **podrían no existir backups automáticos**. Declarar copias que no existen es
> una afirmación verificable y falsa. Ver ítem R10.

---

## 11. Menores de edad

El Servicio está dirigido a personas mayores de [CONFIRMAR CON TITULAR — se sugiere 18]
años. No recopilamos deliberadamente datos de menores. Si tomamos conocimiento de que
una cuenta corresponde a un menor, la daremos de baja y eliminaremos sus datos. Si sos
madre, padre o representante legal y detectás una situación así, escribinos a
`contacto@re-expert.app`.

---

## 12. Información agregada y anonimizada

Podemos elaborar estadísticas e información agregada a partir del uso del Servicio,
**disociada de forma que no permita identificar a ninguna persona**. Una vez anonimizada
de manera irreversible, esa información **deja de constituir dato personal** en los
términos del art. 2 de la Ley 25.326, y podemos utilizarla y divulgarla sin
restricciones —por ejemplo, para informes de mercado, materiales de comunicación o
mejora de nuestros modelos de producto.

---

## 13. Cambios en esta Política

Podemos actualizar esta Política. **Los cambios sustanciales se notificarán con al menos
15 días corridos de antelación** al correo registrado y mediante aviso en la aplicación,
indicando la fecha de entrada en vigencia. Conservaremos las versiones anteriores para
consulta.

---

## 14. Contacto

**Responsable:** [CONFIRMAR CON TITULAR]
**Correo para privacidad y derechos:** `contacto@re-expert.app`
**Autoridad de control:** Agencia de Acceso a la Información Pública — `www.argentina.gob.ar/aaip`

---

## Anexo — Marcadores para revisión legal

### [REVISIÓN LEGAL]
| # | Punto | A validar |
|---|---|---|
| 1 | 5.4 | Suficiencia del consentimiento para tratamiento identificado con fines de mejora; instrumentar la oposición en la aplicación. |
| 2 | 6 | Tratamiento automatizado: suficiencia de la declaración y del derecho de impugnación (art. 20 Ley 25.326). |
| 3 | 7.6 | **Transferencia internacional**: suficiencia del consentimiento como base, conveniencia de cláusulas contractuales tipo y documentación de los acuerdos con cada proveedor. |
| 4 | 12 | Que el criterio de anonimización sea efectivamente irreversible antes de ampararse en este punto. |

### [CONFIRMAR CON TITULAR]
| # | Qué | Punto |
|---|---|---|
| 1 | Razón social, CUIT y domicilio | 1, 14 |
| 2 | ⚠️ **Inscripción de la base en el Registro de la AAIP** | 1 |
| 3 | ⚠️ **Registrar la constancia de aceptación** (fecha, versión, IP) — hoy no se guarda | 4.3 |
| 4 | ⚠️ **Condiciones contractuales con cada proveedor de IA**: tipo de cuenta, compromiso de no entrenamiento y plazo de retención | 7.1 |
| 5 | Qué integraciones están efectivamente activas en producción (Google, OpenAI, Resend, Tavily, Maps, Telegram, medio de pago) | 7.1, 7.3 |
| 6 | Plazos de retención de logs, backups y documentos generados | 8.4 |
| 7 | Respaldo contable desvinculado de la cuenta, si se necesita conservarlo | 8.4 |
| 8 | Existencia y prueba de copias de seguridad antes de mencionarlas | 10.4 |
| 9 | Edad mínima | 11 |
| 10 | Fecha de publicación | Encabezado |

---

## Registro de cambios

| Versión | Fecha | Cambios |
|---|---|---|
| 1.3 | — | Se suma la gestión de medios de pago: qué se guarda de una tarjeta (marca, últimos cuatro, vencimiento, titular y la referencia del procesador) y qué explícitamente no, con la explicación de por qué el número no puede llegar a nuestros servidores. Se detalla el registro de cobros rechazados y su motivo. |
| 1.2 | — | Correcciones de exactitud tras contrastar contra el código: se declara la **ficha de contexto** que se envía al proveedor de IA en cada intercambio con el Asistente (nombre, correo, plan, proyectos, pagos pendientes, recordatorios y oportunidades); se corrige el alcance del **filtro de datos financieros** (aplica a la memoria, no al chat); se describe con precisión el tratamiento de la **ubicación** y se aclara que el historial todavía no está habilitado ni tiene purga autoservicio; los reportes de error pasan de "anónimos" a **"disociados"**, declarando qué sobrevive; se detalla el alcance real del **export** (ampliado a 27 colecciones) y la restricción de la baja con período pago vigente. |
| 1.1 | — | Se actualiza tras el endurecimiento técnico: secreto de 2FA cifrado, enlaces de informes firmados y con vencimiento, filtrado de datos financieros en la memoria automática, minimización de la ubicación, exportación integral de datos disponible y anonimización del correo en los reportes de error al dar de baja. Se incorporan: bases legales completas, punto 6 sobre tratamiento automatizado, punto 12 sobre información anonimizada, conservación para defensa de derechos, plazo concreto de notificación de incidentes y registro del consentimiento. |
| 1.0 | — | Versión inicial. |
