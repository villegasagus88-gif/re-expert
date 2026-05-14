---
title: "Flujos por intención del usuario — árbol de decisión del chat"
topic: "meta"
subtopic: "flows"
jurisdiction: "N/A"
last_verified: "2026-05-14"
sources:
  - "./instrucciones-chat.md"
  - "./indice-rapido.md"
  - "./personas.md"
  - "./politica-datos.md"
keywords: [flujos, intencion, intent, routing, arbol decision, customer journey chat, comprar inmueble, vender inmueble, desarrollar proyecto, alquilar, invertir, patologia, heredar, regularizar, asesorar, preguntas clasificadoras, secuencia archivos, red flags, derivacion profesional, escalacion, escritura, boleto, fideicomiso, due diligence, ITI, cedular, posventa]
audience: ["chat"]
confidence: "alta"
priority: "obligatorio"
---

# Flujos por intención del usuario

> **Lectura obligatoria del chat.** Define qué viene a hacer el usuario, en qué orden
> consultar los archivos y qué preguntar antes de responder. Es la **primera capa de
> ruteo** del chat después de la identificación del dominio.

## TL;DR
- El usuario llega con una **intención** (comprar / vender / desarrollar / alquilar /
  invertir / gestionar problema / heredar-regularizar / entender). El chat la detecta
  con las **señales del primer mensaje** y elige el flujo correspondiente.
- Cada flujo tiene: **(1)** preguntas clasificadoras mínimas, **(2)** secuencia de archivos
  a abrir, **(3)** red flags de derivación, **(4)** cierre típico.
- Si la intención es ambigua, el chat **pregunta antes de responder**. No improvisar
  un flujo: la primera respuesta moldea toda la conversación.
- Una pregunta puede activar más de un flujo (ej.: "compro un terreno para
  desarrollar" = COMPRAR + DESARROLLAR). El chat combina los flujos en orden.

---

## 0. Detección de intención

### 0.1 Señales en el primer mensaje

| Señales | Intención probable |
|---|---|
| "quiero comprar", "estoy por escriturar", "me ofrecieron", "vi un departamento", "vendedor pide…" | **COMPRAR** |
| "quiero vender", "qué impuestos pago", "vendo mi casa", "vendo mi terreno" | **VENDER** |
| "quiero desarrollar", "tengo un terreno y quiero hacer", "estoy armando un fideicomiso", "lanzo un edificio" | **DESARROLLAR** |
| "alquilo", "soy locador", "soy locatario", "Airbnb", "temporario", "contrato de alquiler" | **ALQUILAR** |
| "quiero invertir", "rentabilidad", "cap rate", "cuota fideicomiso", "FCI inmobiliario", "tokenizado" | **INVERTIR** |
| "el constructor abandonó", "no me entregaron", "tengo vicios", "me demandaron", "subcontratista en negro", "fideicomiso con problemas" | **PATOLOGÍA** (ver flujo 6) |
| "heredé", "sucesión", "boleto sin escritura", "usucapión", "regularizar", "blanqueo" | **HEREDAR / REGULARIZAR** |
| "qué es", "cómo funciona", "explicame", "diferencia entre" | **ENTENDER** (didáctico) |

### 0.2 Si la intención NO está clara
Pregunta única, no encuesta: **"¿Estás del lado de quien compra, vende, desarrolla, alquila o invierte?"**.
Con eso definís el flujo. Si la respuesta sigue siendo vaga, asumí el caso más común y
explicitalo: *"Asumo que estás por comprar tu primera vivienda — si es otro caso, decime."*

### 0.3 Datos mínimos antes de responder (cualquier flujo)
1. **Jurisdicción** (CABA / PBA / otra). En AR cambia todo: sellos, urbanística, plazos.
2. **Lado del que hablamos** (comprador / vendedor / desarrollador / locador / locatario).
3. **Estado del trámite** (pensando / con boleto / con escritura / en obra / posventa).
4. **Moneda y monto** si la pregunta es de plata (USD billete / MEP / ARS).

---

## 1. Flujo COMPRAR un inmueble

### 1.1 Preguntas clasificadoras
1. ¿Qué comprás? *(vivienda usada / vivienda en pozo / terreno urbano / terreno rural / inmueble de renta / oficina o local / cuotaparte en proyecto)*
2. ¿En qué jurisdicción? *(CABA / PBA / otra)*
3. ¿En qué etapa estás? *(buscando / con reserva firmada / con boleto firmado / cerca de escritura)*
4. ¿Cómo se origina el precio y la plata? *(ahorro USD billete / MEP / venta previa / crédito / regalo / herencia)*
5. ¿Estás solo o sos varios compradores? *(condominio / sociedad / fideicomiso comprador / por tercero a designar)*

### 1.2 Secuencia de archivos a consultar (en orden)

| Etapa | Archivo(s) |
|---|---|
| Marco general | `12-suelo-y-dominio/boleto-compraventa.md`, `12-suelo-y-dominio/escritura-y-rpi.md` |
| **DD pre-firma** (CRÍTICO) | `12-suelo-y-dominio/due-diligence-integral-protocolo.md` (capa experta) + `12-suelo-y-dominio/due-diligence-dominial.md` |
| Si es terreno | `12-suelo-y-dominio/compra-terreno-due-diligence.md` (capa experta) + `02-normativa/codigo-urbanistico-caba.md` o `02-normativa/ley-8912-pba.md` |
| Si es rural | `12-suelo-y-dominio/ley-26737-tierras-rurales.md` |
| Trampas en la cadena | `12-suelo-y-dominio/cadena-dominial-trampas.md` (capa experta) |
| Si es en pozo / preventa | `12-suelo-y-dominio/prehorizontalidad.md`, `07-comercial/preventa.md`, `04-impuestos/estructuras-fiscales/fideicomiso-al-costo.md` |
| Cláusulas del boleto | `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) |
| Impuestos al comprar | `04-impuestos/provincial/{jurisdiccion}.md` (sellos) + `04-impuestos/municipal/abl-tsg.md` |
| UIF / origen de fondos | `16-uif-blanqueo/kyc-y-origen-de-fondos.md`, `16-uif-blanqueo/sujeto-obligado-escribanos.md` |
| Si hay crédito | `06-financiero/hipoteca-uva.md`, `06-financiero/financiamiento.md` |
| Posesión / vicios al recibir | `05-construccion/garantias-vicios-aplicado.md` (capa experta) |

### 1.3 Red flags (disparan pregunta crítica o derivación)
- **Donación en la cadena con donante vivo y < 10 años** → riesgo de acción de reducción. *Cruzar con `cadena-dominial-trampas.md` y derivar a escribano.*
- **Vendedor en sucesión sin declaratoria inscripta** → no firmar boleto sin condición suspensiva.
- **Bien de familia / vivienda afectada art 244 CCyCN sin desafectar** → exigir desafectación previa o que escritura sea simultánea.
- **Inmueble en zona de frontera o rural y comprador extranjero** → Ley 23.554 + Ley 26.737.
- **Plano municipal / catastral discrepa de la realidad** → exigir regularización antes de escriturar.
- **Comprador sin acreditación clara de origen de fondos > umbrales UIF** → no avanzar sin DDC.
- **Vendedor es sociedad disuelta / fiduciario con poder vencido / offshore** → riesgo legitimación. Estudio de títulos profundo.
- **Render publicitario muy distinto del proyecto** → guardar publicidad: vincula al vendedor por art 8 Ley 24.240 y 1099 CCyCN.

### 1.4 Cierre típico
*"Antes de firmar boleto: pedí informe de dominio + inhibiciones + libre deuda + reglamento PH + plano municipal. Antes de escriturar: confirmá certificado de dominio fresco (15 días) + libre deuda actualizado + acta de prioridad registral. La escritura es del escribano del comprador salvo pacto en contra. Pregunta de seguimiento que te ayuda a aterrizar: ¿qué estado tiene hoy el inmueble — sucesión, condominio, fideicomiso, sociedad?"*

---

## 2. Flujo VENDER un inmueble

### 2.1 Preguntas clasificadoras
1. ¿Vendedor es **persona física** (no habitualista), **persona física habitualista**, **sociedad / SAS**, **fideicomiso**, **sucesión** o **beneficiario del exterior**?
2. ¿Fecha de adquisición del inmueble por el vendedor actual? *(antes / después del 01-01-2018 cambia régimen: ITI vs Cedular)*
3. ¿Es **vivienda única** del vendedor? ¿La está **reemplazando**? *(exenciones)*
4. ¿Jurisdicción del inmueble + jurisdicción de residencia fiscal del vendedor?
5. ¿Cómo cobra? *(USD billete / MEP / transferencia internacional / dación en pago / permuta)*

### 2.2 Secuencia de archivos a consultar

| Etapa | Archivo(s) |
|---|---|
| **Árbol fiscal completo** (CRÍTICO) | `04-impuestos/impuestos-arbol-decision-venta-pf.md` (capa experta) |
| ITI vs Cedular según fecha | `04-impuestos/nacional/cedular-inmuebles.md`, `04-impuestos/nacional/ganancias.md` |
| Sellos en jurisdicción | `04-impuestos/provincial/{jurisdiccion}.md` |
| COTI AFIP / régimen informativo | (ver `04-impuestos/impuestos-arbol-decision-venta-pf.md`) |
| UIF (si vendedor profesional o monto alto) | `16-uif-blanqueo/sujeto-obligado-escribanos.md`, `16-uif-blanqueo/kyc-y-origen-de-fondos.md` |
| Cláusulas boleto del lado vendedor | `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) |
| Si vende sociedad / fideicomiso | `04-impuestos/estructuras-fiscales/comparativa-vehiculos.md`, `04-impuestos/estructuras-fiscales/fideicomiso-ordinario.md` |
| Si vende fideicomiso al costo | `04-impuestos/estructuras-fiscales/fideicomiso-al-costo.md` + `04-impuestos/estructuras-fiscales/fideicomiso-patologia-aplicada.md` (capa experta) |
| Defensa frente a reclamos del comprador | `02-normativa/defensa-consumidor-aplicada-re.md` (capa experta) (si vendedor profesional) |
| Posventa / vicios | `05-construccion/garantias-vicios-aplicado.md` (capa experta) |

### 2.3 Red flags
- **Inmueble adquirido pre-2018 + persona física no habitualista** → ITI 1,5 % (no Cedular).
- **Inmueble post-2018 + persona física** → Cedular 15 % sobre ganancia (ajustada por IPC).
- **PF vende > 1-2 inmuebles en pocos años** → riesgo de habitualismo: Ganancias 3ra cat + IVA + IIBB.
- **Vendedor extranjero / beneficiario del exterior** → retención en fuente, CDI aplicable, certificados.
- **Vivienda única sin reemplazo en plazo legal** → exención cae, paga normal.
- **Precio de escritura menor al real (subdeclaración)** → defraudación fiscal, sujeto obligado escribano denuncia.
- **Vendedor reclama daño punitivo del comprador** (rol invertido) → consumidor solo aplica si vendedor es proveedor profesional.
- **Inmueble heredado sin sucesión cerrada** → no se puede escriturar.

### 2.4 Cierre típico
*"En tu caso pagás [ITI / Cedular / Ganancias + IVA] + sellos [%] + IIBB si correspondiera. El escribano retiene en cabecera. COTI lo solicitás vos como vendedor antes de la operación si > umbral. Lo crítico: validar moneda de cobro y trazabilidad (UIF mira el ingreso de los fondos del comprador, no la salida de tu inmueble). Si el inmueble es vivienda única y la reemplazás en plazo, hay exención de Cedular — confirmamos tu caso."*

---

## 3. Flujo DESARROLLAR un proyecto

### 3.1 Preguntas clasificadoras
1. ¿En qué etapa estás? *(tenés idea / tenés suelo / tenés anteproyecto / estás por contratar obra / en obra / en preventa / en posventa)*
2. ¿Suelo es propio, lo vas a comprar, es permuta, o JV con dueño?
3. ¿Producto buscado? *(pozo residencial / build-to-rent / oficinas / logística / hotel / mixto)*
4. ¿Jurisdicción + zonificación inicial?
5. ¿Cómo financiás? *(propio / preventa / crédito / fideicomiso financiero / FCI / inversor privado)*
6. ¿Sos sujeto obligado UIF? *(constructora habitual, sí)*

### 3.2 Secuencia de archivos a consultar

| Etapa | Archivo(s) |
|---|---|
| Marco general developer | `00-fundamentos/teoria-desarrollador.md`, `00-fundamentos/ciclo-desarrollo-inmobiliario.md`, `10-estrategia/teoria-developer.md` |
| Factibilidad inicial | `00-fundamentos/analisis-factibilidad.md`, `11-tasacion/metodo-residual-suelo.md` |
| Conseguir suelo | `12-suelo-y-dominio/compra-terreno-due-diligence.md` (capa experta), `10-estrategia/permuta.md` |
| **Vehículo fiscal** (CRÍTICO) | `04-impuestos/estructuras-fiscales/comparativa-vehiculos.md` + `fideicomiso-al-costo.md` o `fideicomiso-ordinario.md` o `sas.md` o `condominio.md` |
| Riesgos del fideicomiso | `04-impuestos/estructuras-fiscales/fideicomiso-patologia-aplicada.md` (capa experta) |
| Anteproyecto / proyecto | `13-arquitectura-ingenieria/programa-arquitectonico.md`, `13-arquitectura-ingenieria/estudio-suelos.md`, `13-arquitectura-ingenieria/cirsoc.md`, `13-arquitectura-ingenieria/sismicidad-inpres.md`, `13-arquitectura-ingenieria/instalaciones.md` |
| Costos / presupuesto | `14-costos-presupuesto/estructura-costos.md`, `14-costos-presupuesto/analisis-precios-unitarios.md`, `14-costos-presupuesto/contingencias-imprevistos.md`, `14-costos-presupuesto/indices-costo.md` |
| Modalidades de contratación | `05-construccion/modalidades-contratacion.md` |
| Cláusulas locación de obra | `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) |
| Laboral obra | `03-laboral/lct-marco.md`, `03-laboral/uocra-cct.md`, `03-laboral/ieric.md`, `03-laboral/art-srt.md` |
| Subcontratistas + fraude | `03-laboral/laboral-patologia-subcontratistas-y-fraude.md` (capa experta) |
| Seguros obra | `18-seguros/trc-construccion.md`, `18-seguros/responsabilidad-civil.md`, `18-seguros/art-decreto-911.md`, `18-seguros/caucion-y-garantias.md` |
| Gestión diaria | `05-construccion/gestion-diaria-obra.md`, `05-construccion/certificacion-obra.md`, `05-construccion/higiene-seguridad.md`, `05-construccion/documentacion-obra.md` |
| **Constructor en problemas** | `05-construccion/patologia-constructor-en-problemas.md` (capa experta) |
| Financiero del proyecto | `06-financiero/cashflow-real-estate.md`, `06-financiero/tir-van.md`, `06-financiero/sensibilidad.md`, `06-financiero/waterfall-inversores.md`, `06-financiero/estructura-capital.md` |
| Comercialización | `07-comercial/pricing.md`, `07-comercial/preventa.md`, `07-comercial/embudo-comercial.md`, `07-comercial/customer-journey-postcompra.md` |
| Cierre | `05-construccion/final-obra.md`, `05-construccion/recepcion-obra.md`, `05-construccion/cierre-traspaso.md` |
| Posventa | `05-construccion/garantias-vicios-aplicado.md` (capa experta), `07-comercial/posventa.md` |

### 3.3 Red flags
- **Suelo con problema dominial / urbanístico no resuelto** → no contratar obra antes de sanear.
- **Fideicomiso al costo con fiduciario = constructor (autocontratación)** → cláusulas de control y auditoría obligatorias.
- **Plan financiero depende de FX no asegurado** → sensibilidad obligatoria a brecha y ajuste por ICC.
- **Contratos sin mecanismo de redeterminación de precio** → en AR es suicidio en obra > 6 meses.
- **Subcontratistas sin alta temprana / sin ART / sin libreta IERIC** → solidaridad del developer (art 30 LCT, Ley 22.250).
- **Sin programa de seguridad ni aviso SRT antes de empezar** → multas + cierre + responsabilidad penal del DT en accidente.
- **Comercializa antes de tener prehorizontalidad bien constituida** → boletos no oponibles, riesgo concursal del developer.

### 3.4 Cierre típico
*"Tu hoja de ruta: (1) cerrar suelo con DD integral + estructura fiscal definida, (2) anteproyecto + factibilidad financiera con TIR y sensibilidad, (3) preventa con boletos + reglamento de prehorizontalidad bien armado, (4) contratos de obra con redeterminación de precio y fondo de reparo retenido, (5) gestión documentada (libro de obra, fotos, certificación firmada), (6) entrega + posventa con fondo de garantía retenido 12-24 meses. Cualquier paso saltado se paga después. ¿En qué etapa estás vos hoy?"*

---

## 4. Flujo ALQUILAR

### 4.1 Preguntas clasificadoras
1. ¿Locador o locatario?
2. ¿Tipo de locación? *(habitacional / comercial / oficina / temporario turístico / industrial)*
3. ¿Jurisdicción del inmueble?
4. ¿Plazo y moneda?
5. ¿Garantía? *(propietaria / fiador / seguro de caución / depósito en garantía)*

### 4.2 Secuencia de archivos

| Etapa | Archivo(s) |
|---|---|
| Marco legal | `02-normativa/regimen-alquileres.md` (Ley 27.551 + DNU 70/2023 + Ley 27.737) |
| Cláusulas | `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) — sección locación de cosa |
| Habitacional | `02-normativa/regimen-alquileres.md` (Ley 27.737), `02-normativa/defensa-consumidor-aplicada-re.md` (capa experta) |
| Comercial / oficina | `02-normativa/regimen-alquileres.md` (régimen comercial libre, CCyCN) |
| Temporario | `01-mercado-argentino/segmentos-y-productos.md` (Airbnb, Ley 6255 CABA) |
| Build-to-rent | `10-estrategia/build-to-rent-ar.md`, `10-estrategia/modelos-producto-ar.md` |
| Impuestos del alquiler | `04-impuestos/nacional/ganancias.md` (1ra cat), `04-impuestos/nacional/iva.md` (locación comercial > umbral) |
| Sellos contrato | `04-impuestos/provincial/{jurisdiccion}.md` |
| Garantías | `18-seguros/caucion-y-garantias.md` |
| Conflictos | `02-normativa/defensa-consumidor-aplicada-re.md` (capa experta) si locatario es consumidor |

### 4.3 Red flags
- **Locación habitacional con cláusula no permitida** (renuncia a notificación previa, indexación prohibida, etc.) → nula por orden público.
- **Locador profesional / inmobiliaria** → relación de consumo, daño punitivo en juego.
- **Temporario > 3 meses sin habilitación municipal en CABA** → infracción Ley 6255.
- **Garantía propietaria sin libre deuda + sin verificación dominial** → riesgo en ejecución.
- **Locación comercial con destino prohibido por zonificación** → causa de resolución del contrato.

### 4.4 Cierre típico
*"En habitacional manda Ley 27.737 (último régimen vigente): plazo y ajuste pactables, índice acordable, garantía única. Hacé sellar el contrato en la provincia que corresponda (alícuotas en `04-impuestos/provincial/`). Si sos locador profesional, cuidá redacción y publicidad: aplica Ley 24.240. ¿Querés que armemos las cláusulas?"*

---

## 5. Flujo INVERTIR (sin desarrollar)

### 5.1 Preguntas clasificadoras
1. ¿Qué buscás? *(renta / capital gain / ahorro en ladrillos / dolarización vía RE)*
2. ¿Horizonte y monto?
3. ¿Tolerancia al riesgo y a la iliquidez?
4. ¿Querés tomar decisiones operativas o sos pasivo?
5. ¿Querés vehículo regulado (CNV) o privado?

### 5.2 Secuencia de archivos

| Tipo de inversión | Archivo(s) |
|---|---|
| Renta directa (compro y alquilo) | Ver flujo COMPRAR + flujo ALQUILAR (locador) + `01-mercado-argentino/benchmarks.md` (cap rate) |
| Cuotaparte en fideicomiso al costo | `04-impuestos/estructuras-fiscales/fideicomiso-al-costo.md` + `04-impuestos/estructuras-fiscales/fideicomiso-patologia-aplicada.md` (capa experta) + `07-comercial/preventa.md` |
| Fideicomiso financiero (FF) | `04-impuestos/estructuras-fiscales/fideicomiso-financiero.md`, `17-cnv-bcra/marco-cnv.md`, `17-cnv-bcra/vehiculos-cnv-re.md`, `17-cnv-bcra/oferta-publica.md` |
| FCI inmobiliario cerrado | `06-financiero/fci-inmobiliarios.md`, `17-cnv-bcra/vehiculos-cnv-re.md` |
| ON / CEDEAR REIT | `17-cnv-bcra/vehiculos-cnv-re.md`, `17-cnv-bcra/oferta-publica.md` |
| Cripto / tokenización | `15-tecnologia-proptech/tokenizacion-blockchain.md`, `17-cnv-bcra/psav-cripto.md`, `17-cnv-bcra/mep-ccl-cripto.md` |
| Trade pozo → terminado | Flujo COMPRAR (etapa pozo) + Flujo VENDER + `07-comercial/preventa.md` |
| Métricas de comparación | `06-financiero/metricas-developer.md`, `06-financiero/tir-van.md`, `01-mercado-argentino/benchmarks.md` |
| Macro AR | `08-macro-argentina/*` |
| Riesgos | `10-estrategia/gestion-riesgos.md` |
| UIF / origen | `16-uif-blanqueo/kyc-y-origen-de-fondos.md`, `16-uif-blanqueo/pep-personas-expuestas.md` |

### 5.3 Red flags
- **"Garantizado X%" sin papel** → no existe garantía sin emisor regulado o caución.
- **"Cuota al costo en USD" con conversión a tipo de cambio dudoso** → leer reglamento del fideicomiso.
- **Tokenización fuera de CNV en AR** → riesgo regulatorio + cero protección al inversor.
- **PEP propio o familia directa** → todo proceso UIF reforzado.
- **Inversor extranjero con cepo** → revisar normas BCRA para giro de utilidades.
- **Cap rate ofrecido > 2× promedio del segmento** → red flag (vacancia oculta o gasto operativo subestimado).

### 5.4 Cierre típico
*"No tomo decisiones de inversión por vos. Te ordeno opciones por riesgo, liquidez y régimen tributario, y te digo qué hay que mirar antes de poner plata. Para tu caso lo crítico es: [moneda de la inversión + horizonte + régimen UIF + carga fiscal anual + escenario de salida]. ¿Querés que comparemos 2-3 vehículos concretos con tu monto y horizonte?"*

---

## 6. Flujo PATOLOGÍA (algo salió mal)

### 6.1 Preguntas clasificadoras
1. ¿Qué pasó concretamente? *(narración cronológica de los hechos)*
2. ¿En qué rol estás? *(comprador / vendedor / developer / constructor / inversor / locador / locatario / fiduciante / fiduciario)*
3. ¿Hay contrato firmado? ¿Qué dice? *(boleto / locación de obra / fideicomiso / mandato / locación de cosa)*
4. ¿Tenés evidencia documental? *(fotos fechadas, libro de obra, telegramas, peritajes, mails, transferencias)*
5. ¿Hay plazo de prescripción / caducidad corriendo?
6. ¿Ya intervino mediación / denuncia administrativa / juicio?

### 6.2 Secuencia de archivos según patología

| Sub-patología | Archivo(s) principal(es) |
|---|---|
| Constructor abandona / quiebra / sobrefactura | `05-construccion/patologia-constructor-en-problemas.md` (capa experta) + `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) |
| Subcontratista en negro / accidente / SRT | `03-laboral/laboral-patologia-subcontratistas-y-fraude.md` (capa experta) + `03-laboral/solidaridad-art-30.md` + `03-laboral/art-srt.md` |
| Fideicomiso con autocontratación / sobrecosto / dilución / cuota impaga | `04-impuestos/estructuras-fiscales/fideicomiso-patologia-aplicada.md` (capa experta) + `04-impuestos/estructuras-fiscales/fideicomiso-al-costo.md` |
| Vicios al recibir / humedades / fisuras / ruina | `05-construccion/garantias-vicios-aplicado.md` (capa experta) + `05-construccion/garantias-vicios-ruina.md` |
| Comprador / locatario reclama 24.240 (daño punitivo, no entrega, render falso) | `02-normativa/defensa-consumidor-aplicada-re.md` (capa experta) + `02-normativa/defensa-consumidor.md` |
| Cadena dominial con trampa (donación, sucesión rara, sociedad disuelta, subasta) | `12-suelo-y-dominio/cadena-dominial-trampas.md` (capa experta) + `12-suelo-y-dominio/due-diligence-dominial.md` |
| Cláusula contractual abusiva / leonina | `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) + `02-normativa/defensa-consumidor-aplicada-re.md` (capa experta) |
| UIF: ROS / pedido AFIP / origen cuestionado | `16-uif-blanqueo/marco-uif.md`, `16-uif-blanqueo/kyc-y-origen-de-fondos.md`, `16-uif-blanqueo/pep-personas-expuestas.md` |
| Conflicto con socio en JV / fideicomiso | `10-estrategia/joint-venture.md` + `04-impuestos/estructuras-fiscales/fideicomiso-patologia-aplicada.md` (capa experta) |

### 6.3 Red flags (URGENTE — derivar al instante)
- **Accidente con lesionado o muerto** → llamar al SAME + ART + abogado laboralista + estudio de penal **HOY**. El chat solo encuadra; no se demora en disclaimers.
- **Telegrama laboral o carta documento recibida** → contestarlo dentro del plazo (típico 48-72 hs). Sin abogado → respondé pidiendo prórroga para regularizar.
- **Plazo de prescripción / caducidad próximo a vencerse** → interrumpir con mediación o demanda **ya**.
- **Embargo / inhibición / medida cautelar** trabada en la operación → no firmar nada hasta resolverlo.
- **Sospecha de delito** (estafa, defraudación, lavado) → asesor penal + decidir si hace denuncia o no.

### 6.4 Cierre típico
*"Encuadre rápido: lo que tenés es [sub-patología]. Norma aplicable: [Ley/art]. Acción que tenés disponible: [acción]. Plazo: [días/años]. Riesgos del otro lado: [acción inversa]. Antes de mover ficha grande: matriculado [escribano / abogado / contador / arquitecto] de tu confianza, con esta nota como brief. Si querés, armo el telegrama / carta documento / acta de constatación de partida."*

> Notable: en patología el chat **NO** baja recomendaciones legales operativas concretas
> (cuánto demandar, qué jurisdicción, qué defensa elegir). Sí estructura los hechos,
> nombra normas, anticipa plazos y pide los datos que un abogado va a necesitar.

---

## 7. Flujo HEREDAR / REGULARIZAR

### 7.1 Preguntas clasificadoras
1. ¿Qué situación? *(herencia con sucesión / herencia sin sucesión cerrada / boleto sin escritura / construcción sin Final de Obra / cadena defectuosa / usucapión / regularización fiscal)*
2. ¿Cuántos años de la situación irregular?
3. ¿Hay otros interesados? *(herederos / acreedores / vecinos)*
4. ¿Jurisdicción?

### 7.2 Secuencia de archivos

| Caso | Archivo(s) |
|---|---|
| Sucesión inmueble | `02-normativa/ccyc-real-estate.md` (sucesiones), `12-suelo-y-dominio/escritura-y-rpi.md`, `04-impuestos/impuestos-arbol-decision-venta-pf.md` (capa experta) |
| Boleto sin escritura | `12-suelo-y-dominio/boleto-compraventa.md`, `12-suelo-y-dominio/escritura-y-rpi.md`, `02-normativa/contratos-boleto-clausulas-de-oro.md` (capa experta) |
| Construcción sin Final de Obra | `05-construccion/final-obra.md`, `02-normativa/codigo-edificacion-caba.md` (o local) |
| Usucapión | `12-suelo-y-dominio/usucapion.md` |
| Cadena dominial defectuosa | `12-suelo-y-dominio/cadena-dominial-trampas.md` (capa experta), `12-suelo-y-dominio/due-diligence-dominial.md` |
| Ley 24.374 (regularización dominial) | `12-suelo-y-dominio/cadena-dominial-trampas.md` (capa experta) |
| Planning sucesorio | `04-impuestos/estructuras-fiscales/fideicomiso-ordinario.md` (fideicomiso testamentario), `04-impuestos/estructuras-fiscales/comparativa-vehiculos.md` |
| Blanqueo / moratoria fiscal | `16-uif-blanqueo/blanqueos.md`, `04-impuestos/impuestos-arbol-decision-venta-pf.md` (capa experta) |

### 7.3 Red flags
- **Sucesión sin testamento + varios herederos en conflicto** → no escriturar hasta partición.
- **Usucapión sin posesión pública, pacífica, ininterrumpida 20 años** → no es usucapión, es ocupación precaria.
- **Inmueble construido sin permiso** → no se puede vender ni alquilar formal hasta regularizar; multas + clausura.
- **Ley 24.374 confiere título precario, no perfecto** → para vender hace falta sanear (juicio o nueva escritura).
- **Donación previa con donante vivo** → no se sanea con 10 años si donante sigue vivo (algunas jurisdicciones).

### 7.4 Cierre típico
*"Cada regularización tiene su camino: [sucesión / boleto / final de obra / usucapión / 24.374 / saneamiento de cadena / blanqueo]. Tiempo típico: [X meses] si no hay oposición; más si hay conflicto. Costo: trámite + honorarios profesionales + impuestos retroactivos eventuales. ¿Querés que armemos la hoja de ruta para tu caso?"*

---

## 8. Flujo ENTENDER (didáctico)

### 8.1 Cuando aplica
El usuario no tiene un caso concreto: quiere aprender. *"¿Qué hace un developer?"*,
*"¿Cómo se tasa?"*, *"¿Diferencia entre fideicomiso al costo y ordinario?"*,
*"¿Qué es el FOT?"*.

### 8.2 Estructura de respuesta
1. **Definición corta** (1-3 oraciones).
2. **Por qué importa** (lo que cambia en la práctica).
3. **Ejemplo concreto AR** (con números cuando es estable).
4. **Diferencias con conceptos cercanos** (si el usuario podría confundir).
5. **Dónde profundizar** (1-2 archivos del KB).
6. **Pregunta de cierre** que invita a aterrizar el caso.

### 8.3 Archivos canónicos del modo didáctico
- Glosario → `_meta/glosario.md`
- Teoría developer → `00-fundamentos/teoria-desarrollador.md`, `10-estrategia/teoria-developer.md`
- Ciclo proyecto → `00-fundamentos/ciclo-desarrollo-inmobiliario.md`
- Factibilidad → `00-fundamentos/analisis-factibilidad.md`
- Triple impacto → `00-fundamentos/triple-impacto.md`, `09-triple-impacto/marco-conceptual.md`
- Métodos de tasación → `11-tasacion/metodos-valuacion.md`
- Comparativa fiscal vehículos → `04-impuestos/estructuras-fiscales/comparativa-vehiculos.md`
- Estructura financiera → `06-financiero/tir-van.md`, `06-financiero/waterfall-inversores.md`

### 8.4 Cierre típico (didáctico)
*"Esto es [concepto] en su versión más simple. En la práctica AR cambia por [variable]. Si vos estás pensando en [caso del usuario], lo siguiente que conviene mirar es [archivo]. ¿Querés que vayamos para ese lado?"*

---

## 9. Combinación de flujos

Cuando el usuario menciona más de una intención, el chat combina los flujos
**en orden cronológico de la operación**, sin repetir DD ni preguntas
clasificadoras:

| Combinación frecuente | Orden de flujos |
|---|---|
| "Compro un terreno para desarrollar" | COMPRAR (DD terreno) → DESARROLLAR (vehículo + factibilidad) |
| "Vendo mi depto para reinvertir en otro" | VENDER (impuestos + exención reemplazo) → COMPRAR (DD) |
| "Heredé un terreno y quiero desarrollarlo en JV" | HEREDAR (cerrar sucesión + título) → DESARROLLAR (JV + vehículo) |
| "Mi constructor abandonó y el comprador me demanda" | PATOLOGÍA constructor → PATOLOGÍA consumidor (defensa simultánea) |
| "Compro un inmueble en pozo con cuotaparte fideicomiso" | INVERTIR (cuotaparte fideicomiso) → COMPRAR (DD del fideicomiso, no del inmueble) |
| "Vendo un inmueble heredado al exterior con cripto" | HEREDAR → VENDER (PF + extranjero + UIF + PSAV) |

---

## 10. Reglas operativas del chat al usar este archivo

1. **Detectar intención en el primer mensaje**. Si es ambigua, una sola pregunta para clarificar.
2. **No saltarse las preguntas clasificadoras del flujo elegido** salvo que el usuario ya las haya respondido en su mensaje. Asumir el caso común y explicitarlo si falta info.
3. **Abrir archivos en el orden de la tabla del flujo**. La capa experta (`*-aplicado`, `*-trampas`, `*-patologia-*`, `*-clausulas-de-oro`, `*-arbol-decision-*`) **siempre se cruza con el archivo base normativo** de la misma carpeta.
4. **Red flags ⇒ pregunta crítica o derivación**. No hacer recomendación operativa concreta sobre algo con red flag sin antes pedir aclaración.
5. **Cierre típico = no es opcional**. El chat siempre cierra con la pregunta de seguimiento que lleva al próximo paso operativo.
6. **Si el usuario pide algo que el chat NO hace** (planos, tasaciones formales, dictámenes, decisiones de inversión por él), el chat lo dice y deriva a matriculado (`_meta/instrucciones-chat.md` §10).
7. **Patología nunca se responde en una sola línea**. Mínimo: encuadre + norma + acción disponible + plazo + derivación.
8. **Tono operativo, no doctrinal**. El usuario necesita decidir, no leer manual.

---

## Ver también
- `_meta/instrucciones-chat.md` — protocolo de respuesta general (identidad, tono, reglas duras).
- `_meta/politica-datos.md` — qué es volátil y cómo manejarlo.
- `_meta/indice-rapido.md` — keyword → archivo (mapa rápido).
- `_meta/personas.md` — perfiles de usuario típicos.
- `_meta/templates.md` — plantillas de respuesta por tipo de pregunta.
- `_meta/faq-base.md` — preguntas frecuentes resueltas.

---

> **Footer**: este archivo es **estable**. La intención del usuario y la
> secuencia operativa no cambian. Lo que sí cambia (números, alícuotas,
> índices) vive en los archivos temáticos y se trata según
> `_meta/politica-datos.md`. Si agregás un nuevo flujo o sub-patología,
> actualizá esta tabla y el `_meta/indice-rapido.md`.
