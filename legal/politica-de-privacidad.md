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

**Versión:** 1.0 (borrador)
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
> de contacto que no funciona vacía de contenido todo el punto 8 (derechos ARCO)**, cuyo
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
- **No vendemos tus datos.** No hacemos publicidad con ellos.
- **Sí analizamos tu uso de forma identificada** para mejorar el producto (ver 5.4);
  podés oponerte.
- **No tocamos los datos de tu tarjeta**: los procesa la pasarela de pago.
- Podés pedir la eliminación de tu cuenta desde Configuración → Cuenta. **Si tenés una
  suscripción paga vigente, primero tenés que cancelarla**; la baja queda habilitada
  inmediatamente después. Se desactiva al instante y se borra a los 30 días.
- Si cargás datos de otras personas (contactos, clientes, proveedores), **la
  responsabilidad de tener permiso para hacerlo es tuya** (ver 4.3).

---

## 3. Qué datos tratamos

### 3.1. Datos que nos das al registrarte y usar la cuenta

| Dato | Obligatorio | Finalidad |
|---|---|---|
| Nombre y apellido | Sí | Identificación, personalización, comunicaciones |
| Correo electrónico | Sí | Identificador de cuenta, autenticación, avisos, recuperación |
| Contraseña | Sí | Autenticación. **Se guarda hasheada con bcrypt y sal, nunca en texto legible** |
| Teléfono | No | Avisos y contacto. Podés cargarlo vos o pedírselo al Asistente |
| Secreto y códigos de verificación en dos pasos | No (opt-in) | Segundo factor de autenticación |

### 3.2. Contenido que generás usando el Servicio

| Dato | Detalle |
|---|---|
| **Conversaciones completas** | Todos los mensajes que escribís y las respuestas recibidas, con su título y sección |
| **Memoria del Asistente** | Datos que el sistema guarda automáticamente para recordar tu contexto: perfil profesional, preferencias, y por proyecto: dirección, lote, superficies, indicadores urbanísticos, y **nombres de clientes o inversores y montos en negociación** cuando los mencionás |
| **Planos y documentación** | Archivos PDF o imagen que subís (hasta 8 MB). Suelen contener nombre del comitente, matrícula profesional, domicilio de obra y número de expediente |
| **Proyectos de obra** | Presupuestos, costos reales, avance, hitos, materiales y notas |
| **Pagos de obra** | Concepto, **nombre del proveedor**, monto, fecha y estado (registro de gastos de tu obra, distinto de tu suscripción) |
| **Oportunidades / Deal Room** | Zona, ciudad, precios, puntajes y notas |
| **Contactos** | Ver punto 4.3 — datos de terceros |
| **Reportes de error** | Título, descripción y contexto técnico de tu navegador (versión, idioma, resolución, tema, hora local y pantalla donde ocurrió), que se te informa al enviarlos |

### 3.3. Datos que se generan automáticamente

| Dato | Finalidad |
|---|---|
| Fecha del último acceso, estado del plan, fin del período de prueba | Operación del servicio y control de acceso |
| **Registro de consumo de modelos de IA** (modelo usado, cantidad de tokens y costo por consulta) | Control de costos y de límites de uso |
| **Eventos de interés en cursos y materiales, asociados a tu cuenta** | Mejora del producto y de la oferta (ver 5.4) |
| **Ubicación geográfica**, si la autorizás en el navegador | Buscar corralones y precios de materiales de tu zona |
| Datos técnicos de conexión (dirección IP, navegador) | Seguridad, prevención de abuso y funcionamiento |

### 3.4. Datos que NO tratamos

- **No guardamos los datos de tu tarjeta de crédito o débito.** Los procesa
  íntegramente la pasarela de pago.
- **No solicitamos ni queremos datos sensibles** (salud, origen étnico, opiniones
  políticas, convicciones religiosas, afiliación sindical, vida sexual). Su carga está
  prohibida por los Términos.
- **Las imágenes que adjuntás al chat no se almacenan**: se envían al proveedor de IA
  para su análisis y se descartan de nuestros sistemas; en la conversación queda sólo
  una referencia a que hubo un adjunto.

---

## 4. Base legal y consentimiento

4.1. Tratamos tus datos con tu **consentimiento libre, expreso e informado** (art. 5
Ley 25.326), que prestás al registrarte y aceptar esta Política, y porque el
tratamiento es **necesario para la ejecución del contrato** que celebrás al contratar
el Servicio (art. 5 inc. 2.d).

4.2. Podés **revocar tu consentimiento** en cualquier momento, lo que implicará la baja
del Servicio, ya que sin tratamiento de datos no es técnicamente posible prestarlo.

### 4.3. Datos de terceros que vos cargás — leer con atención

> La Plataforma te permite cargar datos de personas que no son usuarias: **contactos
> (nombre, teléfono, correo), el comitente o cliente de un proyecto de planos, los
> proveedores de tus pagos y los responsables asignados a tareas.**

4.3.1. **Respecto de esos datos, vos sos el responsable del tratamiento y nosotros
actuamos como encargados**, tratándolos únicamente para prestarte el Servicio y según
tus instrucciones.

4.3.2. Al cargarlos, declarás contar con base legal suficiente y haber informado a esas
personas, conforme a la cláusula 9.3 de los Términos.

4.3.3. **Estos datos también se transmiten a los proveedores de inteligencia
artificial** descriptos en el punto 6, en la medida en que el Asistente necesite
consultarlos para responderte.

4.3.4. **Si sos una de esas personas** y querés ejercer derechos sobre datos tuyos que
un usuario cargó, escribinos a `contacto@re-expert.app`. Daremos intervención al
usuario responsable y atenderemos el pedido conforme a la ley.

---

## 5. Para qué usamos tus datos

5.1. **Prestar el Servicio:** procesar tus consultas, generar respuestas y análisis,
guardar tu trabajo y mantener tu sesión.

5.2. **Administrar tu cuenta:** autenticación, recuperación de contraseña,
verificación en dos pasos, gestión del plan y de la suscripción.

5.3. **Comunicaciones operativas:** avisos de seguridad, cambios en el servicio,
vencimientos, recordatorios que vos configurás. **No son publicidad y no podés
desuscribirte de las estrictamente necesarias para la relación contractual.**

5.4. **Mejorar el producto (tratamiento identificado).**
Analizamos cómo usás la Plataforma —incluyendo qué cursos y materiales te interesan,
asociado a tu cuenta— para mejorar funcionalidades y orientar la oferta.
**Este tratamiento es identificado, no anónimo, y así lo declaramos.**
**Podés oponerte** escribiendo a `contacto@re-expert.app`, sin que ello afecte tu acceso
al Servicio.

> **[REVISIÓN LEGAL]** Este tratamiento excede la mera ejecución del contrato, por lo
> que requiere consentimiento informado diferenciado y un mecanismo efectivo de
> oposición (art. 27 Ley 25.326 por analogía). Se recomienda instrumentar la oposición
> como un interruptor en Configuración, no sólo por correo.

5.5. **Seguridad y prevención de abusos:** detectar accesos no autorizados, limitar
peticiones abusivas e investigar incidentes.

5.6. **Cumplimiento legal:** responder requerimientos de autoridad competente y cumplir
obligaciones fiscales y contables.

5.7. **NO usamos tus datos para:** venderlos o cederlos con fines comerciales, publicidad
de terceros, ni decisiones automatizadas con efectos jurídicos sobre vos.

---

## 6. Con quién compartimos tus datos

> **Esta es la sección más importante del documento.** Para funcionar, RE Expert
> transmite información a proveedores externos. **La mayoría está en Estados Unidos**,
> país que no ha sido declarado con nivel adecuado de protección por la autoridad
> argentina.

### 6.1. Proveedores de inteligencia artificial

| Proveedor | Qué recibe | País |
|---|---|---|
| **Anthropic** (modelos Claude) | **El contenido íntegro de tus consultas y de los últimos mensajes de la conversación; tu memoria de perfil y de proyecto; los planos e imágenes que cargues; y los datos de proyecto necesarios para responderte** | Estados Unidos |
| **Google** (modelos Gemini) *[CONFIRMAR CON TITULAR: activo sólo si está configurada la clave correspondiente]* | Lo mismo que el anterior, cuando el Asistente opera con este proveedor | Estados Unidos |
| **OpenAI** *[CONFIRMAR CON TITULAR: activo sólo si está configurada la clave]* | **El audio de tu micrófono** para transcripción y el texto de las respuestas para generar voz. En el modo de conversación por voz en tiempo real recibe además: **(a)** tu dirección IP, porque la conexión se establece directamente desde tu navegador; **(b)** la **transcripción completa de la conversación**; y **(c)** la memoria que el asistente de voz guardó sobre vos y **los datos de tus proyectos que consulta para responderte**, que pueden incluir nombres de clientes o inversores y montos, conforme al punto 3.2 | Estados Unidos |

6.1.1. **Estos proveedores procesan tus datos para generar la respuesta y devolverla.**
No los utilizamos para que entrenen modelos por nuestra cuenta.

> **[CONFIRMAR CON TITULAR]** ⚠️ **Crítico.** Debe verificarse con cada proveedor y
> documentarse: (a) si la cuenta contratada es de tipo comercial/API, (b) si existe
> compromiso de **no utilizar los datos para entrenamiento**, y (c) cuál es el **plazo
> de retención** en su infraestructura. En particular, **los niveles gratuitos de
> algunos proveedores permiten expresamente el uso de los contenidos para mejorar sus
> modelos**: si se estuviera usando un nivel gratuito, esta declaración sería inexacta y
> debería corregirse antes de publicar.

### 6.2. Infraestructura

| Proveedor | Qué recibe | País |
|---|---|---|
| **Supabase** | Base de datos y almacenamiento: **todos** los datos descriptos en el punto 3 | Estados Unidos |
| **Railway** | Ejecución del backend y registros de aplicación | Estados Unidos |
| **Netlify** | Distribución de la interfaz web; registros de acceso (IP, navegador) | Estados Unidos |

### 6.3. Otros proveedores

| Proveedor | Qué recibe | Estado |
|---|---|---|
| **Mercado Pago / Stripe** | Tu correo y un identificador interno de tu cuenta, para asociar el pago. **Nunca los datos de tu tarjeta, que trata el propio procesador** | Según configuración del medio de pago |
| **Resend** | Tu correo, tu nombre y el contenido de los mensajes transaccionales (códigos de verificación, enlaces de recuperación) | *[CONFIRMAR CON TITULAR]* |
| **OpenStreetMap / Nominatim** | **Tus coordenadas geográficas exactas**, si autorizás la ubicación, para convertirlas en el nombre de tu zona | **Activo** (Unión Europea / Reino Unido) |
| **Google Maps** | Las direcciones que le indicás al Asistente para optimizar recorridos | *[CONFIRMAR CON TITULAR]* |
| **Tavily** | El texto de la búsqueda que el sistema construye a partir de tu consulta y, para precios de materiales, tu zona | *[CONFIRMAR CON TITULAR]* |
| **Telegram** | Tu identificador de chat y el contenido de los avisos que pidas recibir por ese canal. **Si además activás la conversación con el Asistente por Telegram**, el contenido de los mensajes que le escribas y de sus respuestas | *[CONFIRMAR CON TITULAR]* |

6.3.1. **Servicios de terceros embebidos en la interfaz.** Al cargar cualquier página,
tu navegador solicita tipografías a **Google Fonts**, y al abrir el visor de planos
descarga la biblioteca de lectura de PDF desde el CDN de **Cloudflare**. En ambos casos
esos proveedores **reciben tu dirección IP y datos de tu navegador**; el primero, incluso
antes de que inicies sesión. Ver la Política de Cookies.

6.3.2. **Consultas a fuentes públicas.** Para mostrarte cotizaciones, noticias y datos
oficiales consultamos fuentes públicas (BCRA, portales de datos abiertos, medios). **No
les enviamos datos personales tuyos.**

### 6.4. Otras comunicaciones

Podemos comunicar datos a autoridades judiciales o administrativas competentes cuando
exista requerimiento legal, y a asesores profesionales obligados a confidencialidad. En
caso de reorganización societaria o transferencia del negocio, los datos podrían
transferirse al continuador, **notificándotelo previamente**.

### 6.5. Transferencia internacional de datos

6.5.1. Como surge de los cuadros anteriores, **tus datos se transfieren fuera de la
Argentina**, principalmente a Estados Unidos.

6.5.2. El art. 12 de la Ley 25.326 prohíbe la transferencia a países que no
proporcionen niveles de protección adecuados, **salvo** —entre otros supuestos— que el
titular haya prestado **consentimiento expreso e informado**, o que la transferencia
sea necesaria para la ejecución del contrato entre el titular y el responsable.

6.5.3. **Al aceptar esta Política prestás tu consentimiento expreso e informado a estas
transferencias**, que además son imprescindibles para prestarte el Servicio: sin ellas,
la Plataforma no puede funcionar.

> **[REVISIÓN LEGAL]** ⚠️ **Punto de máxima exposición del documento.** Corresponde
> validar: (a) la suficiencia del consentimiento como base de legitimación bajo la
> Resolución AAIP 60/2016, (b) la conveniencia de suscribir **cláusulas contractuales
> tipo** o adherir a los DPA que ofrecen estos proveedores, y (c) la documentación de
> cada acuerdo. Hoy **no existe ningún contrato de tratamiento firmado en el repositorio
> del proyecto**. Ver "Riesgos detectados en el código", ítem R2.

---

## 7. Cuánto tiempo conservamos tus datos

7.1. **Mientras tu cuenta exista.** Tus conversaciones, proyectos, planos y demás
contenido se conservan mientras mantengas la cuenta activa: **no les aplicamos un plazo
de borrado por antigüedad**, y así lo declaramos de forma honesta.

Sí aplicamos borrado automático, por diseño, a dos categorías:

- **Historial de ubicaciones:** se conservan los últimos 90 días, con un máximo de 500
  registros. Además podés purgarlo por completo cuando quieras desde la aplicación.
- **Recordatorios ya enviados, fallidos o cancelados:** se eliminan a los 30 días.

7.2. **Borrado a tu pedido.** Podés eliminar conversaciones individualmente cuando
quieras, y purgar tu historial de ubicaciones desde la propia aplicación.

7.3. **Al dar de baja la cuenta:** se desactiva de inmediato y, transcurridos **30 días
corridos**, se elimina de forma definitiva junto con conversaciones y mensajes,
proyectos, hitos y presupuestos, planos y sus archivos, pagos de obra, contactos,
memoria del asistente, oportunidades, recordatorios, canales de notificación,
ubicaciones y registros de consumo. **Es un borrado real, no una marca de "eliminado".**
Si iniciás sesión dentro de esos 30 días, la baja se cancela.

El borrado alcanza a los datos alojados en nuestros servidores. **La memoria que el
asistente de voz guarda en tu propio navegador se elimina borrando los datos del sitio**;
podés hacerlo vos en cualquier momento (ver Política de Cookies).

7.4. **Qué sobrevive a la baja — declaración honesta de excepciones:**

| Qué | Por qué | Plazo |
|---|---|---|
| El correo asociado a **reportes de error** que hayas enviado | Se conserva para poder responder consultas de soporte ya iniciadas | *[CONFIRMAR CON TITULAR]* |
| **Documentos generados** (informes PDF/planillas) alojados en el almacenamiento de archivos | Se generan sin vínculo con tu cuenta, por lo que técnicamente no pueden identificarse para su borrado selectivo | *[CONFIRMAR CON TITULAR]* |
| **Copias de seguridad** | Rotación técnica del proveedor de base de datos | Según el plan contratado *[CONFIRMAR CON TITULAR]* |
| **Registros técnicos (logs)** que puedan contener tu correo | Diagnóstico y seguridad | Según retención del proveedor de hosting *[CONFIRMAR CON TITULAR]* |

> **[CONFIRMAR CON TITULAR]** ⚠️ **Registros contables.** Este cuadro **no incluye** una
> excepción por conservación de comprobantes fiscales, porque hoy el código **borra
> también los pagos y las compras** al eliminar la cuenta (relación en cascada). Si el
> Titular necesita conservar respaldo contable por 10 años (art. 328 CCyC), hay que
> implementarlo como una tabla desvinculada de la cuenta y **recién entonces** declararlo
> acá. Declarar una retención que no ocurre es tan riesgoso como omitir una que sí.

> **[CONFIRMAR CON TITULAR]** ⚠️ **Contradicción a resolver antes de publicar.** El
> aviso que hoy muestra la aplicación al eliminar la cuenta dice que se borran *"todos
> tus datos"*. Las excepciones de este cuadro lo desmienten. Hay dos salidas honestas y
> hay que elegir una: **(a)** modificar el código para que la purga elimine también el
> correo de los reportes de error y los documentos generados, o **(b)** ajustar el texto
> de la aplicación para que anuncie estas excepciones. **Mantener ambas versiones es la
> peor opción**: una promesa escrita que el sistema incumple. Ver ítem R8.

---

## 8. Tus derechos (Acceso, Rectificación, Actualización y Supresión)

8.1. Como titular de los datos tenés derecho a:

- **Acceder** gratuitamente a tus datos, en intervalos no menores a seis meses (art. 14
  Ley 25.326).
- **Rectificar, actualizar o suprimir** los datos inexactos o cuyo tratamiento no se
  ajuste a la ley (art. 16).
- **Oponerte** a tratamientos no necesarios para la ejecución del contrato, como el
  descripto en 5.4.
- **Revocar tu consentimiento**, con el efecto previsto en 4.2.

8.2. **Cómo ejercerlos.** Escribiendo a `contacto@re-expert.app` desde el correo
registrado. **Responderemos dentro de los 10 días corridos** para pedidos de acceso y
de los 5 días hábiles para rectificación o supresión, conforme a los arts. 14 y 16 de
la Ley 25.326.

8.3. Muchos de estos derechos podés ejercerlos directamente desde la aplicación:
modificar tu nombre, correo y teléfono, cambiar tu contraseña, borrar conversaciones,
purgar ubicaciones y solicitar la eliminación de la cuenta.

8.4. **Autoridad de control.** La **Agencia de Acceso a la Información Pública** es el
órgano de control de la Ley 25.326 y tiene atribuciones para atender denuncias respecto
del incumplimiento de las normas de protección de datos personales.

> **[REVISIÓN LEGAL]** ⚠️ **Hoy no existe una función de exportación integral de datos**
> ni un procedimiento formalizado para responder pedidos de acceso en 10 días: habría
> que atenderlos manualmente contra la base. Se recomienda implementar la exportación
> antes de publicar esta Política, o al menos documentar el procedimiento interno. Ver
> ítem R11.

---

## 9. Cómo protegemos tus datos

9.1. **Medidas implementadas** (descripción honesta de lo que existe):

- Comunicaciones cifradas mediante **HTTPS** con redirección forzada.
- Contraseñas almacenadas con **función de hash bcrypt con sal**; nunca en texto
  legible ni recuperables por nosotros.
- Autenticación mediante **tokens de vigencia limitada**, con mecanismo de invalidación
  global de todas las sesiones ante el cambio de contraseña.
- **Verificación en dos pasos opcional** mediante aplicación de autenticación o código
  por correo, con códigos de recuperación de un solo uso.
- **Aislamiento por cuenta**: las consultas de la aplicación a datos de usuario filtran
  por el identificador de la cuenta, de modo que ningún usuario puede acceder a los
  datos de otro. Un número acotado de **administradores del Servicio, sujetos a deber de
  confidencialidad**, puede acceder a los reportes de error que envíes —incluido tu
  correo— para poder responderlos, y a estadísticas de uso de cursos y materiales.
- **Límites de tasa** de peticiones para prevenir abuso y ataques de fuerza bruta.
- Cabeceras de seguridad y **política de seguridad de contenidos (CSP)**.
- Validación y saneamiento de las entradas del usuario.
- Cifrado en reposo y en tránsito provisto por el proveedor de base de datos.

9.2. **Compromiso de medios.** Nos obligamos a aplicar medidas razonables y adecuadas
al estado de la técnica. **No garantizamos seguridad absoluta**: ningún sistema conectado
a internet puede garantizarla, y cualquier afirmación en contrario sería falsa.

9.3. **Tu parte.** Usá una contraseña robusta y única, activá la verificación en dos
pasos y no uses la función multicuenta en dispositivos compartidos.

9.4. **Notificación de incidentes.** Ante un incidente de seguridad que afecte
significativamente tus datos, te lo notificaremos sin dilación indebida al correo
registrado, junto con las medidas adoptadas y las recomendaciones a tu alcance, y
daremos aviso a la autoridad de control cuando corresponda.

> **[CONFIRMAR CON TITULAR]** No incluir en esta sección afirmaciones sobre **copias de
> seguridad** hasta verificar que existen y que se probó una restauración. La
> documentación del proyecto indica que, en el plan actual del proveedor de base de
> datos, **podrían no existir backups automáticos**. Declarar copias que no existen es
> una afirmación verificable y falsa. Ver ítem R10.

---

## 10. Menores de edad

El Servicio está dirigido a personas mayores de [CONFIRMAR CON TITULAR — se sugiere 18]
años. No recopilamos deliberadamente datos de menores. Si tomamos conocimiento de que
una cuenta corresponde a un menor, la daremos de baja y eliminaremos sus datos. Si sos
madre, padre o representante legal y detectás una situación así, escribinos a
`contacto@re-expert.app`.

---

## 11. Cambios en esta Política

Podemos actualizar esta Política. **Los cambios sustanciales se notificarán con al menos
15 días corridos de antelación** al correo registrado y mediante aviso en la aplicación,
indicando la fecha de entrada en vigencia. Conservaremos las versiones anteriores para
consulta.

---

## 12. Contacto

**Responsable:** [CONFIRMAR CON TITULAR]
**Correo para privacidad y derechos:** `contacto@re-expert.app`
**Autoridad de control:** Agencia de Acceso a la Información Pública — `www.argentina.gob.ar/aaip`

---

## Anexo — Marcadores para revisión legal

### [REVISIÓN LEGAL]
| # | Punto | A validar |
|---|---|---|
| 1 | 5.4 | Suficiencia del consentimiento para tratamiento identificado con fines de mejora; instrumentar la oposición en la aplicación. |
| 2 | 6.5 | **Transferencia internacional**: suficiencia del consentimiento como base, conveniencia de cláusulas contractuales tipo y documentación de los acuerdos con cada proveedor. |
| 3 | 8 | Ausencia de exportación integral y de procedimiento formal para responder pedidos de acceso en plazo. |

### [CONFIRMAR CON TITULAR]
| # | Qué | Punto |
|---|---|---|
| 1 | Razón social, CUIT y domicilio | 1, 12 |
| 2 | ⚠️ **Inscripción de la base en el Registro de la AAIP** | 1 |
| 3 | ⚠️ **Condiciones contractuales con cada proveedor de IA**: tipo de cuenta, compromiso de no entrenamiento y plazo de retención | 6.1 |
| 4 | Qué integraciones están efectivamente activas en producción (Google, OpenAI, Resend, Tavily, Maps, Telegram, medio de pago) | 6.1, 6.3 |
| 5 | ⚠️ **Resolver la contradicción entre el "todos tus datos" de la app y las excepciones reales de borrado** | 7.4 |
| 6 | Plazos de retención de logs, backups y documentos generados | 7.4 |
| 7 | Existencia y prueba de copias de seguridad antes de mencionarlas | 9.4 |
| 8 | Edad mínima | 10 |
| 9 | Fecha de publicación | Encabezado |
