---
title: "Anti-patterns — errores típicos del rubro AR que el chat debe frenar"
topic: "meta"
subtopic: "anti-patterns"
jurisdiction: "Argentina"
last_verified: "2026-05-14"
sources:
  - "./instrucciones-chat.md"
  - "./flows-por-intencion.md"
  - "./politica-datos.md"
keywords: [anti-patterns, errores comunes, guardrails, red flags, malas practicas, riesgos, equivocaciones, mistakes, traps, trampas, advertencias, criterio]
audience: ["chat"]
confidence: "alta"
priority: "obligatorio"
---

# Anti-patterns del rubro RE en Argentina

> **Para qué sirve este archivo.** Catálogo de equivocaciones recurrentes
> que comete la gente cuando proyecta, compra, construye o vende. Cada
> ítem describe el síntoma en la conversación, por qué es problema y
> cómo redirige el chat sin sonar paternalista.
>
> **Regla de uso.** Si la pregunta del usuario contiene un anti-pattern,
> el chat NO ejecuta la cuenta/recomendación pedida sin antes señalar
> el problema. Y siempre vuelve al criterio sano + archivo de soporte.

---

## Cómo leer cada entrada

Cada anti-pattern tiene:
1. **Síntoma** — cómo aparece en la pregunta del usuario.
2. **Por qué es problema** — daño concreto que produce.
3. **Redirección** — qué responde el chat (tono directo, no moralista).
4. **Fuente** — archivo de la KB donde está la versión correcta.

---

## 1. Compra de inmueble

### 1.1 "Compro con boleto y dejo la escritura para más adelante"
- **Síntoma**: usuario plantea pagar 50%+ contra boleto sin plazo cierto de escrituración o sin estudio de títulos previo.
- **Por qué es problema**: el boleto **no transmite dominio**. Si el vendedor muere, se concursa, embarga el bien o vende a un tercero de buena fe que escritura primero, perdés. La posesión sin escritura es **frágil**.
- **Redirección**: "Antes de firmar boleto: estudio de títulos + verificación de inhibiciones del vendedor + cláusula de escrituración con plazo y multa. La diferencia de costo es mínima frente al riesgo de quedarte sin escritura."
- **Fuente**: `02-normativa/contratos-boleto-clausulas-de-oro.md`, `12-suelo-y-dominio/cadena-dominial-trampas.md`.

### 1.2 "Pago el terreno en cash sin justificar"
- **Síntoma**: operación grande con USD billete sin documentar origen ni operatoria bancaria.
- **Por qué es problema**: a partir de cierto monto (UIF — sujeto obligado: escribano), el escribano **está obligado a reportar**. Si no podés justificar, no escriturás. Si escriturás bajo el agua, exposición a Ley 25.246 (lavado).
- **Redirección**: "Toda compra grande exige justificación de origen de fondos: ventas previas, ahorros bancarizados, herencia documentada. El escribano va a pedir DDJJ UIF. Si vas a operar en cash, hablá antes con escribano + contador para armar la trazabilidad."
- **Fuente**: `16-uif-blanqueo/sujetos-obligados.md`, `16-uif-blanqueo/operaciones-sospechosas.md`.

### 1.3 "Skipear la DD de dominio porque la vendedora es amiga / del barrio"
- **Síntoma**: confianza personal reemplaza verificación documental.
- **Por qué es problema**: vicios dominiales (gravámenes, sucesiones mal cerradas, cesiones no inscriptas, ex cónyuges) **viajan con el inmueble**. La confianza no neutraliza la inhibición.
- **Redirección**: "La DD dominial no se saltea por confianza. Cuesta poco, evita perder todo. El escribano de tu lado es el que la hace antes de que firmes."
- **Fuente**: `12-suelo-y-dominio/due-diligence-integral-protocolo.md`, `12-suelo-y-dominio/cadena-dominial-trampas.md`.

### 1.4 "Acepto boleto preimpreso del vendedor sin revisar"
- **Síntoma**: el usuario firma lo que le pasa la inmobiliaria sin leerlo.
- **Por qué es problema**: cláusulas estándar suelen ser **pro-vendedor** (seña no es seña, escrituración en "plazo razonable", penalidad solo al comprador, etc.). Algunas son lisa y llanamente **abusivas** (Ley 24.240).
- **Redirección**: "Boleto sin revisar es un cheque en blanco. Mandalo a tu escribano antes de firmar. Banderas rojas típicas: seña convertida en arras del 1066 CCyCN sin aclarar, escrituración sin plazo, penalidades asimétricas."
- **Fuente**: `02-normativa/contratos-boleto-clausulas-de-oro.md`, `02-normativa/defensa-consumidor-aplicada-re.md`.

---

## 2. Compra de terreno para desarrollo

### 2.1 "El FOT lo veo cuando arranco el proyecto"
- **Síntoma**: usuario comprometido con la compra antes de verificar zonificación.
- **Por qué es problema**: parcela con FOT bajo o protegida (APH, distrito mixto, retiros) puede valer **30-50% menos** del precio que pagaste si pensabas hacer m² que la norma no permite.
- **Redirección**: "El FOT y los premios van ANTES del precio. Te paso a `00-fundamentos/analisis-factibilidad.md` para armar la factibilidad. Si ya firmaste reserva: cláusula de salida por incompatibilidad urbanística antes de boleto."
- **Fuente**: `00-fundamentos/analisis-factibilidad.md`, `02-normativa/codigo-urbanistico-caba.md`, `12-suelo-y-dominio/compra-terreno-due-diligence.md`.

### 2.2 "Suelo barato porque no tiene servicios — me lo gestiono después"
- **Síntoma**: factibilidad de cloacas / gas / pluviales no verificada.
- **Por qué es problema**: extensión de red puede costar **USD 100k-500k** o ser **imposible** en plazos del proyecto. AySA / Metrogas / Aguas Bonaerenses no garantizan plazos.
- **Redirección**: "Antes de comprar pedí factibilidades por escrito: cloacas, agua, gas, pluvial, eléctrica. Sin esos papeles, el ahorro del terreno se evapora."
- **Fuente**: `12-suelo-y-dominio/compra-terreno-due-diligence.md`, `13-arquitectura-ingenieria/instalaciones-prefactibilidades.md`.

### 2.3 "Compro con boleto y empiezo a proyectar"
- **Síntoma**: arranca planos, contratos con arquitecto, antes de escriturar.
- **Por qué es problema**: si la escrituración se cae (cualquier motivo), invertiste honorarios y plazos en un terreno que no es tuyo.
- **Redirección**: "Hasta la escritura, el terreno no es tuyo. La regla es: boleto con cláusulas blindadas + estudio de títulos + plazo de escritura cierto. Recién con escritura arranca el cronograma de proyecto."
- **Fuente**: `02-normativa/contratos-boleto-clausulas-de-oro.md`, `12-suelo-y-dominio/cadena-dominial-trampas.md`.

---

## 3. Estructuración (fideicomiso, sociedad)

### 3.1 "Fideicomiso al costo armado entre amigos sin escribano"
- **Síntoma**: contrato de fideicomiso firmado en privado, sin escritura pública para los inmuebles.
- **Por qué es problema**: si hay inmuebles, **necesitás escritura pública** (CCyCN art. 1669). Sin eso, el patrimonio no se separa, los acreedores personales del fiduciante pueden embargar, y AFIP no lo reconoce como sujeto separado.
- **Redirección**: "Fideicomiso con inmuebles → escritura pública sí o sí. Sin escribano, técnicamente no hay fideicomiso. Te paso patología típica: autocontratación, fiduciario sin idoneidad, falta de inscripción AFIP / IIBB."
- **Fuente**: `06-financiero/fideicomiso-construccion.md` (si existe), `02-normativa/ccyc-real-estate.md`, `_meta/glosario.md` — fideicomiso.

### 3.2 "Mismo fiduciario y fiduciante (autocontratación)"
- **Síntoma**: developer que es fiduciante, fiduciario y beneficiario al mismo tiempo.
- **Por qué es problema**: prohibido por CCyCN art. 1673. El contrato es **nulo de nulidad absoluta**. Si hay conflicto, el negocio explota.
- **Redirección**: "Fiduciario y fiduciante no pueden ser la misma persona — art. 1673 CCyCN. Necesitás fiduciario tercero independiente (escribano, sociedad fiduciaria, profesional). Lo barato sale carísimo si después un fiduciante reclama."
- **Fuente**: `02-normativa/ccyc-real-estate.md` (arts. 1666-1707), patología de fideicomiso (ver `_meta/indice-rapido.md` → fideicomiso).

### 3.3 "Sociedad en negro: aportes y retiros sin documentar"
- **Síntoma**: socios meten plata sin actas, sin acuerdo escrito, sin clarificar gobierno.
- **Por qué es problema**: cuando hay éxito, **siempre hay pelea**. Sin documentación, juicio. Cuando hay fracaso, **siempre hay pelea**. Sin documentación, juicio.
- **Redirección**: "Antes del primer peso: contrato de socios / acta constitutiva con aportes, mayorías, salidas, valuación. Pongan plazo. Pongan cláusula de tag-along / drag-along. Sin esto no arranquen."
- **Fuente**: `10-estrategia/socios-y-gobierno.md` (si existe), `02-normativa/ccyc-real-estate.md`.

---

## 4. Construcción / obra

### 4.1 "Llave en mano con un único precio cerrado, sin desglose"
- **Síntoma**: contrato a precio total sin detallar materiales, calidades, marcas.
- **Por qué es problema**: el constructor termina entregando lo mínimo (calidad indistinta, marcas baratas). Si discutís, no tenés contractual concreta.
- **Redirección**: "Llave en mano sí, pero con **especificación técnica detallada** (calidades, marcas o equivalentes, niveles) + adendas firmadas. Sin spec, el constructor define hacia abajo."
- **Fuente**: `05-construccion/modalidades-contratacion.md`, `05-construccion/documentacion-obra.md`.

### 4.2 "Pago certificaciones sin verificar avance real"
- **Síntoma**: usuario paga lo que el constructor certifica sin medir en obra.
- **Por qué es problema**: certificación adelantada → constructor se queda con cash → desaparece cuando hay problema (insolvencia, mejor cliente, etc.). Estás financiando al constructor con tu plata.
- **Redirección**: "Certificación se mide contra avance verificado en obra (idealmente director de obra o PM externo). Si pagás en función de fechas o ítems no verificados, ya sos financista del constructor."
- **Fuente**: `05-construccion/certificacion-obra.md`, `14-costos-presupuesto/control-presupuestario.md`, `05-construccion/patologia-constructor-en-problemas.md`.

### 4.3 "El constructor tiene los obreros 'en negro' pero es más barato"
- **Síntoma**: presupuesto bajo porque MO sin aportes / sin libreta / sin ART.
- **Por qué es problema**: **solidaridad** del comitente (Ley 22.250 art. 32 + Ley 26.940). Cuando hay accidente o reclamo laboral, **el dueño de la obra paga**. Más caro, no más barato.
- **Redirección**: "Obra con MO en negro = el dueño paga el accidente (solidaridad Ley 22.250). Exigí libretas IERIC, F931, ART vigente. Si el constructor no las tiene, es subcontratista que va a desaparecer cuando reclamen."
- **Fuente**: `03-laboral/laboral-patologia-subcontratistas-y-fraude.md`, `03-laboral/solidaridad-art-30.md`, `03-laboral/uocra-cct.md`.

### 4.4 "Sin plan de inspección y ensayos, lo arreglamos al final"
- **Síntoma**: comitente sin PIE definido, recepción final como única instancia de control.
- **Por qué es problema**: vicios ocultos se hacen visibles cuando el constructor ya está liberado. Sin trazabilidad de ensayos (hormigón, instalaciones, prueba hidráulica), no podés probar nada.
- **Redirección**: "Plan de Inspección y Ensayos firmado al inicio, con hitos verificables. Sin PIE, los vicios ocultos los pagás vos."
- **Fuente**: `05-construccion/plan-inspeccion-ensayo.md`, `05-construccion/garantias-vicios-ruina.md`.

---

## 5. Análisis financiero

### 5.1 "Cap rate bruto = rentabilidad real"
- **Síntoma**: usuario calcula `alquiler anual / precio compra` y declara la rentabilidad del proyecto.
- **Por qué es problema**: omite expensas extraordinarias, ABL, ARBA / inmobiliario, seguro, vacancia, comisión renovación, mantenimiento, ITI/Ganancias a la venta. Rentabilidad **neta real** suele ser 40-60% del bruto.
- **Redirección**: "Cap rate bruto te miente. Pasalo a neto: descontá ABL, expensas extraordinarias, seguro, **vacancia 1 mes/año**, comisión, mantenimiento (1-2% del valor). El neto te queda en CABA típicamente 3.5-4.5% en USD."
- **Fuente**: `06-financiero/metricas-developer.md`, `06-financiero/sensibilidad.md`.

### 5.2 "TIR del proyecto sin contemplar plazo de comercialización"
- **Síntoma**: TIR calculada como si vendieras la última unidad el día de la habilitación.
- **Por qué es problema**: comercialización en proyectos AR demora **12-36 meses post-habilitación**. Si tu modelo no tiene vacancia comercial + costos de mantenimiento del stock, la TIR está inflada.
- **Redirección**: "Modelo la curva de venta real: 30% en pozo, 30% en obra, 40% post-habilitación con cola de 18-30 meses. Costos de stock (expensas, ABL, financieros) durante esa cola. Esa es la TIR honesta."
- **Fuente**: `06-financiero/tir-van.md`, `06-financiero/cashflow-real-estate.md`, `06-financiero/sensibilidad.md`.

### 5.3 "Apalancamiento UVA porque la cuota me da hoy"
- **Síntoma**: usuario evalúa hipoteca UVA mirando cuota inicial vs ingreso actual.
- **Por qué es problema**: UVA ajusta por CER (≈ IPC). Si la inflación supera al ajuste salarial (caso AR 2022-2024), la cuota crece más rápido que el sueldo y la **relación cuota/ingreso explota**.
- **Redirección**: "UVA solo cierra si tu ingreso ajusta al ritmo del CER o más. Si tu ingreso está en USD o paritarias por debajo de inflación, modelá la cuota a 5 años con CER +2% y revisá relación cuota/ingreso. Hoy debe quedar < 25% para tolerar el peor escenario."
- **Fuente**: `06-financiero/hipoteca-uva.md`, `06-financiero/sensibilidad.md`.

### 5.4 "Comparar USD MEP de hoy con USD MEP de hace 3 años para medir rentabilidad"
- **Síntoma**: usuario mide ganancia en USD nominales sin descontar inflación USD.
- **Por qué es problema**: inflación USD acumulada 2021-2024 ≈ 17-19%. Una propiedad que pasó de USD 100k a USD 110k **en términos reales valió menos**.
- **Redirección**: "USD también pierde poder de compra. Descontá inflación USD para medir rentabilidad real. Si comparás 3+ años, sumá CPI USD acumulado (FRED / BLS). Más prolijo: medir en USD constantes del año base."
- **Fuente**: `08-macro-argentina/contexto-inflacion-fx.md`, `06-financiero/metricas-developer.md`.

---

## 6. Fiscal / impositivo

### 6.1 "Vendo y compro el mismo año para no pagar Ganancias — sin formalizar"
- **Síntoma**: usuario sabe que existe el reemplazo de vivienda pero no piensa hacer trámite.
- **Por qué es problema**: el reemplazo (art. 26 LIG / antiguo art. 67) **requiere opción ejercida** y plazos. Sin formalismo, AFIP cobra Ganancias al 15% sobre la diferencia real.
- **Redirección**: "Reemplazo no es automático. Hay que ejercer la opción y cumplir plazos (1 año previo o 1 posterior). Si no formalizás, pagás Ganancias. Pasá por contador antes de la venta."
- **Fuente**: `04-impuestos/ganancias-personas-humanas.md` (si existe), `04-impuestos/impuestos-arbol-decision-venta-pf.md`.

### 6.2 "ITI lo paga el comprador" / "Sellos los paga el vendedor"
- **Síntoma**: confusión sobre quién paga cada impuesto.
- **Por qué es problema**: terminás cerrando precios sin contemplar 5-9% de costos de transacción que aparecen al escriturar.
- **Redirección**: "Por defecto: **ITI vendedor 1.5%** (o exento si reemplazo), **sellos** en CABA generalmente **50/50** (con exenciones vivienda única), **escritura comprador 2-3%**, **comisión** ambas partes. Confirmá con escribano antes de cerrar."
- **Fuente**: `04-impuestos/costos-transaccion.md` (si existe), `02-normativa/codigo-urbanistico-caba.md`.

### 6.3 "Como soy persona física no pago IVA en la venta"
- **Síntoma**: usuario que loteó o construyó para vender supone exención IVA por ser PF.
- **Por qué es problema**: la **habitualidad** te convierte en sujeto IVA aunque seas PF. Vender 3-5 unidades / lotear / construir para vender = sujeto IVA + Ganancias 3ra categoría.
- **Redirección**: "Habitualidad te empresarializa aunque seas PF. 3+ ventas en años contiguos / loteo / construcción para vender = IVA 10.5% (vivienda) o 21% (resto) + Ganancias 3ra. Estructura impositiva antes de arrancar."
- **Fuente**: `04-impuestos/iva-construccion-venta.md` (si existe), `04-impuestos/impuestos-arbol-decision-venta-pf.md`.

---

## 7. Comercialización / corretaje

### 7.1 "Una exclusiva con el corredor que me cobra menos"
- **Síntoma**: elegir corredor por comisión más baja sin evaluar capacidad de venta.
- **Por qué es problema**: corredor barato suele significar **menos inversión en marketing**, menos red, menos tiempo dedicado. Diferencia de 0.5-1% se compensa rápido con 30-60 días extra de exposición + descuento por urgencia al final.
- **Redirección**: "Comisión es el último filtro, no el primero. Mirá: ventas comparables en los últimos 12 meses en tu zona, inversión en marketing, red activa, qué herramientas usa. Después negociás la comisión."
- **Fuente**: `07-comercial/corretaje-comisiones.md` (si existe), `07-comercial/exclusividad-vs-abierto.md`.

### 7.2 "Listo en 4 portales y espero"
- **Síntoma**: estrategia de comercialización = pegar avisos.
- **Por qué es problema**: en mercados ilíquidos AR, lo que mueve es **base de datos del corredor + marketing dirigido + relaciones**. Portal por sí solo es 30-40% del lead flow.
- **Redirección**: "Portales son canal, no estrategia. Sumá: marketing dirigido (Meta/Google con segmentación), open houses, base de datos del corredor, contactos directos con inversores institucionales si el ticket lo amerita."
- **Fuente**: `07-comercial/marketing-real-estate.md`, `15-tecnologia-proptech/panorama-proptech-ar.md`.

### 7.3 "Precio publicado igual a precio objetivo"
- **Síntoma**: usuario pretende vender al 100% del precio publicado.
- **Por qué es problema**: en AR el **descuento de cierre** promedio es 8-15% sobre publicado. Si tu objetivo es USD 200k, publicar a USD 200k = 90% de probabilidad de cerrar en USD 170-185k.
- **Redirección**: "Precio publicado = objetivo + 10-15% de colchón de negociación. Si tu mínimo es USD 200k, publicá USD 220-230k. Confirmá rango con ventas comparables últimos 6 meses en tu zona."
- **Fuente**: `11-tasacion/metodos-valuacion.md`, `07-comercial/pricing-estrategia.md`.

---

## 8. Alquiler

### 8.1 "Pongo cláusula de ajuste mensual sin definir índice"
- **Síntoma**: contrato post-DNU 70/2023 sin índice de ajuste claro.
- **Por qué es problema**: si no hay índice pactado, la actualización es **inejecutable**. Terminás judicializando.
- **Redirección**: "Post-DNU 70/2023 hay libertad, pero **el índice tiene que estar definido**: IPC INDEC nacional, IPC GBA, IPC CABA, o combinación. Periodicidad clara. Topes si los hay. Sin esto, no podés ajustar legalmente."
- **Fuente**: `02-normativa/regimen-alquileres.md`.

### 8.2 "Garantía propietaria con familiar sin verificar libre deuda"
- **Síntoma**: locador acepta garantía sin pedir título + inhibiciones.
- **Por qué es problema**: garante con embargos / inhibiciones = garantía inejecutable. Cuando llega el desalojo, no podés cobrar nada.
- **Redirección**: "Garantía propietaria sirve si está **libre de gravámenes**. Pedí título + inhibiciones del garante. Si está embargado, no sirve aunque sea familiar."
- **Fuente**: `02-normativa/regimen-alquileres.md`, `12-suelo-y-dominio/cadena-dominial-trampas.md`.

---

## 9. Salida / venta

### 9.1 "Vendo cuando el mercado mejore"
- **Síntoma**: usuario sin criterio de salida, decide por intuición/timing.
- **Por qué es problema**: el "mercado mejor" no llega o llega tarde. Mientras tanto, costos de tenencia (ABL, expensas, oportunidad) erosionan retorno. Más cerca de la realidad: vender al precio que el mercado paga **hoy**, con descuento de tiempo.
- **Redirección**: "Definí el criterio antes: precio mínimo aceptable + plazo máximo de exposición. Si en X meses no alcanzaste el mínimo, **bajás precio o cambiás estrategia** (alquilar, refinanciar, asociarte). 'Esperar el mercado' es no decidir."
- **Fuente**: `10-estrategia/exit-strategy.md` (si existe), `_meta/flows-por-intencion.md` — flujo VENDER.

### 9.2 "Refinancio a esperar tiempos mejores"
- **Síntoma**: project sponsor recurre a deuda para sostener un proyecto que no cierra.
- **Por qué es problema**: deuda compra tiempo pero **no resuelve la economía**. Si el unit economics está roto, más deuda lo agranda.
- **Redirección**: "Refinanciar tiene sentido si el negocio cierra y el problema es **calce**. Si el problema es **margen** o **precio de venta**, refinanciar agranda el agujero. Antes de tomar más deuda: pasar el modelo por una sensibilidad real (precio −10%, plazo +6m)."
- **Fuente**: `06-financiero/sensibilidad.md`, `06-financiero/financiamiento.md`, `10-estrategia/exit-strategy.md`.

---

## 10. Anti-patterns transversales del usuario hablando con el chat

### 10.1 "Decime cuánto va a estar el dólar en 6 meses"
- **Redirección**: dato volátil + predictivo, fuera del scope del chat. Ver `_meta/politica-datos.md` y `_meta/instrucciones-chat.md` regla 7.

### 10.2 "Confirmame que me conviene comprar / vender / invertir"
- **Redirección**: el chat **no toma decisiones de inversión por el usuario**. Educa, calcula, compara, anticipa. La decisión queda en la persona. Ver `_meta/instrucciones-chat.md` sección 10.

### 10.3 "Hazme la escritura / firmalo vos"
- **Redirección**: el chat no reemplaza al escribano. Deriva siempre que la decisión sea legal/fiscal puntual.

### 10.4 Usuario que omite jurisdicción ("¿cuál es la alícuota de sellos?")
- **Redirección**: preguntar CABA o PBA antes de responder. Reglas del federalismo impositivo argentino → las alícuotas varían por provincia.

---

## Para el equipo: cómo crecer este catálogo

- Cada vez que un usuario plantea un anti-pattern nuevo, agregarlo acá con el formato `síntoma / problema / redirección / fuente`.
- Cuando un anti-pattern se vuelve frecuente, considerar generar un archivo aplicado dedicado (como ya pasó con `defensa-consumidor-aplicada-re.md`, `cadena-dominial-trampas.md`, etc.).
- Cruce con `flows-por-intencion.md`: cada flujo debería incluir 2-3 anti-patterns que el chat debe detectar como red flags al inicio.
