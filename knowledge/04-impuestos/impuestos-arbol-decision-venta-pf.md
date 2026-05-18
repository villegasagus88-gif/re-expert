---
title: "Planning fiscal de venta de inmueble — árbol de decisión PF y PJ (AR)"
topic: "impuestos"
subtopic: "planning-venta"
jurisdiction: "Argentina"
last_verified: "2026-05-12"
sources:
  - "Ley 20.628 — Impuesto a las Ganancias (texto ordenado, arts. 2, 49, 79, 90 ter — cedular inmuebles 27.430, art. 26 exenciones)"
  - "Ley 23.905 — ITI (Impuesto a la Transferencia de Inmuebles, alícuota 1,5%)"
  - "Ley 23.349 — IVA (arts. 3, 4 — obra sobre inmueble propio, empresa constructora)"
  - "Ley 23.966 — Bienes Personales"
  - "Ley 27.430 — Reforma tributaria 2018 (cedular 15% inmuebles adquiridos desde 1/1/2018)"
  - "Ley 27.737 / 27.541 / 27.743 — modificaciones bienes personales y blanqueos"
  - "Resol. AFIP 2139/2006 + 4189-E/2018 (cedular)"
  - "Resol. AFIP sucesivas — COTI (Código de Oferta de Transferencia de Inmuebles)"
  - "Convenios para evitar doble imposición (CDI) vigentes"
  - "Ley 25.246 + Resol. UIF 21/2011 — sujeto obligado"
  - "Códigos fiscales provinciales — sellos e IIBB"
  - "Práctica profesional: estudios contables RE, escribanías"
keywords: [planning fiscal venta inmueble, impuestos venta inmueble argentina, arbol decision venta pf, vendedor persona fisica impuestos, vendedor sociedad impuestos, vendedor fideicomiso impuestos, vivienda unica exencion, vivienda unica reemplazo, ITI 1.5, impuesto transferencia inmuebles, cedular inmuebles 15, ley 27430, ganancias venta inmueble, inmueble adquirido desde 2018, habitualista inmobiliario, iva venta inmueble nuevo, iva obra propia, iva empresa constructora, sellos venta inmueble, sellos por jurisdiccion, IIBB venta inmueble, bienes personales inmueble, COTI afip, codigo oferta transferencia inmueble, retencion vendedor extranjero, beneficiario del exterior, CDI argentina, monotributista venta inmueble, sociedad vende inmueble, SRL venta inmueble, SAS venta inmueble, fideicomiso al costo venta, fideicomiso ordinario venta, dividendos fideicomiso, distribucion fiduciario, ganancias empresa, retencion ganancias 35, retencion ganancias empresa, plan moratoria afip inmuebles, escritura precio menor real, defraudacion fiscal inmueble, declarado vs real, UIF venta inmueble, sujeto obligado escribano, blanqueo inmueble, regularizacion impositiva, plazo prescripcion AFIP, prescripcion 5 anos 10 anos, optimizacion fiscal venta, condominio venta, sucesion impuestos inmueble, herencia inmueble impuestos, donacion inmueble impuestos, donacion vs venta]
audience: ["vendedor PF", "vendedor PJ", "contador RE", "abogado fiscal", "developer", "inversor", "escribano", "broker", "chat"]
confidence: "alta"
---

# Planning fiscal de venta de inmueble — árbol de decisión

## TL;DR
- **3 preguntas iniciales** definen el régimen: ¿quién vende? · ¿cuándo se adquirió? · ¿es habitualista?
- **PF no habitualista, inmueble pre-2018**: ITI 1,5% sobre escritura. Si era vivienda única → opción reemplazo (no ITI).
- **PF no habitualista, inmueble post 1/1/2018**: **cedular 15%** sobre ganancia (no ITI). Vivienda única-casa habitación exenta (art. 20 inc. o Ley 20.628).
- **PF habitualista**: Ganancias 3ra categoría + IVA si construyó + IIBB provincial.
- **Sociedad / fideicomiso ordinario**: Ganancias 35% (o tasa vigente) + IVA si obra propia + IIBB.
- **Fideicomiso al costo**: pass-through al fiduciante en construcción; al vender la unidad ya escriturada al fiduciante, régimen general PF/PJ del fiduciante.
- **Vendedor extranjero**: retención del 15% sobre ganancia o 17,5% sobre precio (presunción art. 13 LIG).
- Las **3 trampas** más comunes: subdeclarar precio en escritura, no obtener COTI, ignorar IIBB provincial del habitualista.

---

## 1. Las 6 preguntas iniciales (clasificador)

### 1.1 ¿Quién es el vendedor?
- PF residente AR.
- PF beneficiario del exterior.
- Sucesión indivisa.
- Sociedad (SA, SRL, SAS, sociedad de hecho).
- Fideicomiso (al costo, ordinario, financiero).
- Monotributista (en general, no es habilitante para volumen alto).
- Trust extranjero (caso especial complejo).

### 1.2 ¿Cuándo se adquirió el inmueble?
- **Antes de 1/1/2018**: régimen anterior aplicable a PF no habitualista → **ITI 1,5%**.
- **Desde 1/1/2018**: régimen cedular Ley 27.430 → **15% sobre ganancia** (PF no habitualista).
- **Inmueble construido por el vendedor**: fecha de afectación al patrimonio.
- **Inmueble por sucesión**: hereda fecha de adquisición del causante.
- **Inmueble por donación**: hereda fecha de adquisición del donante.

### 1.3 ¿Es habitualista?
- Habitualidad: AFIP la presume si hay frecuencia y propósito de lucro.
- Indicadores: > 1 venta por año, profesión vinculada (broker, developer, arquitecto), publicidad, modalidad empresarial, inscripción IIBB.
- Si habitualista: tributa **3ra categoría Ganancias** (no cedular) + IVA si construyó + IIBB.
- Riesgo de recategorización AFIP retroactiva (5 años prescripción + multas).

### 1.4 ¿Es vivienda única / casa habitación?
- Vivienda única (única propiedad): puede aplicar **régimen de reemplazo** (no paga ITI/cedular si reinvierte en plazo).
- Casa habitación (uso propio): exenta cedular (art. 20 inc. o Ley 20.628 + reglamentación).
- Si vivienda secundaria / inversión → no exenta.

### 1.5 ¿Hay construcción reciente por el vendedor?
- Si vendedor es "empresa constructora" (Ley 23.349 art. 4): venta de obra propia gravada con IVA.
- Empresa constructora: SA, SRL, SAS, también PF que ejecuta obra para vender (no para uso).
- Alícuota: 10,5% sobre venta de inmuebles destinados a vivienda (Ley 23.349 art. 28) o 21% según uso.
- Crédito fiscal: cómputo del IVA pagado en insumos.

### 1.6 ¿Hay residencia fiscal extranjera del vendedor?
- Beneficiario del exterior: retención escribano (Ley 20.628 art. 91 ss.).
- 15% sobre ganancia real (si se opta y se acredita) o 17,5% sobre precio (presunción art. 13).
- CDI (convenio doble imposición): puede reducir o cambiar atribución.

---

## 2. Mapa de impuestos — quién paga qué

### 2.1 Impuestos federales (a cargo del vendedor)

| Impuesto | Aplica a | Alícuota | Base |
|---|---|---|---|
| **ITI** (Ley 23.905) | PF no habitualista, inmueble pre-2018, sin opción reemplazo | 1,5% | Precio escritura |
| **Cedular inmuebles** (Ley 27.430) | PF no habitualista, inmueble post 1/1/2018 | 15% | Ganancia (precio - costo ajustado) |
| **Ganancias 3ra cat.** | Habitualista PF / sociedad / fideicomiso ordinario | Tasa progresiva PF / 35% PJ (verificar vigente) | Ganancia neta |
| **IVA** | Empresa constructora (obra propia) | 10,5% (vivienda) / 21% (otros) | Precio sin terreno (atribución) |
| **Bienes Personales** (anual) | Titular PF al 31/12 | Escala progresiva | Valuación fiscal |

### 2.2 Impuestos provinciales

| Impuesto | Aplica a | Alícuota típica | Quién paga |
|---|---|---|---|
| **Sellos** | Toda escritura de venta | 1,2% – 3,5% según jurisdicción | 50/50 vendedor-comprador (típico, varía) |
| **IIBB** | Habitualista | 1,5% – 6% según provincia | Vendedor |

> Ver `./provincial/_overview.md` y archivos por provincia.

### 2.3 Impuestos municipales

| Concepto | Aplica a | Notas |
|---|---|---|
| **Plusvalía urbana** | Algunas jurisdicciones (CABA Ley 6062, BA varios partidos) | Captación de mayor valor por cambio normativo |
| **Tasas de registro** | Todas | Bajo monto |

> Ver `./municipal/contribuciones-y-plusvalia.md`.

### 2.4 Costos del trámite (no son impuestos pero entran al costo)

| Concepto | Monto típico |
|---|---|
| Honorarios escribano | 1,5% – 2,5% del precio (varía colegio) |
| Aporte previsional escribano | 1,5% – 2% sobre honorarios |
| Honorarios broker | 3% – 4% + IVA cada parte (varía) |
| Honorarios contador (planning previo) | Variable según operación |
| Certificados (dominio, catastral, libre deuda) | Bajos en suma pero múltiples |

---

## 3. Árbol PF no habitualista — paso a paso

### 3.1 ¿Inmueble adquirido antes del 1/1/2018?
**Sí** → régimen ITI 1,5% sobre precio escritura.

- ¿Es vivienda única?
  - **Sí** + va a comprar otra vivienda → opción **reemplazo** (sin pago de ITI si reinvierte en 1 año antes o después).
  - **No** → ITI pleno 1,5% sobre precio.

**No (post 1/1/2018)** → régimen **cedular 15%**.

- ¿Es casa habitación de uso propio?
  - **Sí** + única vivienda → exenta (art. 20 inc. o Ley 20.628).
  - **No** → cedular 15% sobre ganancia.

### 3.2 Cálculo cedular 15%
- Ganancia = precio venta - (costo de adquisición ajustado + mejoras documentadas + gastos de venta).
- Costo ajustado: actualización por IPC desde fecha adquisición (Ley 27.430 + Decreto 1170/2018).
- Mejoras: requieren factura + plano municipal aprobado.
- Gastos de venta: comisión, escritura, sellos parte vendedor.
- Resultado × 15% = impuesto.
- Se paga por DDJJ anual (período fiscal de la operación).
- Retención del escribano si vendedor lo solicita (anticipo).

### 3.3 Régimen reemplazo (ITI pre-2018)
- Aplica solo si **vivienda única** y compra otra **vivienda** dentro del año (antes o después de la venta).
- Solicitud antes de la escritura.
- AFIP otorga certificado de no retención.
- Si no compra en el año → debe ingresar el ITI con intereses.

### 3.4 Errores típicos PF no habitualista
- Pensar que toda venta paga ITI (cuando el inmueble es post-2018 paga cedular).
- No solicitar reemplazo a tiempo (debe ser previo).
- No documentar el costo de adquisición → AFIP toma valor mínimo.
- No documentar mejoras con factura y plano → no son deducibles.
- Vender en USD sin declarar conversión → riesgo blanqueo + UIF.
- Subdeclarar el precio en escritura ("la diferencia se paga aparte") → defraudación fiscal, riesgo penal + base imponible futura.

---

## 4. Árbol PF habitualista

### 4.1 Cuándo te recategorizan
- > 1 venta por año con propósito de lucro.
- Compra y venta sistemática de inmuebles.
- Combinación con otra actividad RE (constructor, broker, desarrollador).
- AFIP usa: cantidad, frecuencia, profesión, modalidad empresarial, publicidad, financiamiento.

### 4.2 Régimen aplicable
- **Ganancias 3ra categoría** sobre ganancia neta (no cedular).
- Alícuota: escala progresiva PF (puede llegar a 35% si supera tope superior).
- **IVA si construyó** y vende como empresa constructora (Ley 23.349 art. 4).
- **IIBB** provincial (inscripción obligatoria).
- **Monotributo** generalmente no aplica para volumen RE (cualquier venta de inmueble suele exceder tope).

### 4.3 Defensa de la calificación
- Vender < 1 inmueble por año.
- No tener inscripción IIBB inmobiliaria.
- Documentar uso del inmueble (alquilado, no en stock para venta).
- Período de tenencia largo (años) entre operaciones.

### 4.4 Si AFIP recategoriza
- Ajuste retroactivo hasta 5 años (prescripción ordinaria) o 10 años (si no presentaste DDJJ).
- Multa por omisión: 100-200% del impuesto omitido.
- Multa por defraudación: 2-6 veces el monto + denuncia penal Ley 24.769 / Ley Penal Tributaria.

---

## 5. Sociedad vendedora (SA, SRL, SAS)

### 5.1 Impuestos
- **Ganancias 3ra categoría**: alícuota PJ vigente (verificar — históricamente 35%, post 27.430 esquema progresivo con dividendos).
- **IVA**: si la sociedad es empresa constructora o el inmueble entra al giro habitual.
- **IIBB**: alta probabilidad de inscripción y pago.
- **Sellos**: 50/50 o según pacto.
- **Bienes Personales** sustituto del responsable (sobre participación de accionistas).

### 5.2 Distribución del resultado
- Después del 35% de gan. PJ, distribución como dividendos paga adicional 7-13% (régimen vigente al momento, verificar).
- Si sociedad mantiene el resultado: queda en patrimonio societario (paga bienes personales sustituto).

### 5.3 Planning
- Decidir momento de venta según resultado acumulado y dividendos.
- Si sociedad tiene quebrantos acumulados: compensar contra ganancia de venta.
- Reorganización societaria (fusión, escisión) puede diferir impuestos (art. 77-78 LIG) si cumple requisitos.

### 5.4 Trampas
- Sociedad inactiva que vende su único activo → riesgo de recalificación como liquidación con consecuencias adicionales.
- Vender a precio "favor" a relacionados → AFIP impugna por valor de mercado (art. 14 LIG).
- Pagar dividendos disfrazados de honorarios o préstamos → recategorización + multa.

---

## 6. Fideicomiso vendedor

### 6.1 Fideicomiso al costo (no es contribuyente del impuesto en general)
- El fideicomiso al costo **pass-through**: el resultado se atribuye al fiduciante-beneficiario.
- Si fiduciante adjudica unidad → no es venta tributable, es adjudicación al costo.
- Si fiduciante luego vende la unidad adjudicada → tributa según su perfil (PF cedular/habitualista o PJ).
- IVA en construcción: el fideicomiso suele ser sujeto IVA y traslada el crédito al fiduciante al adjudicar.

### 6.2 Fideicomiso ordinario (no al costo)
- Es **contribuyente directo** de Ganancias (35% típico).
- Distribución a beneficiarios: similar a dividendos.
- IVA si construye y vende.
- IIBB provincial.

### 6.3 Fideicomiso financiero (oferta pública)
- Régimen especial (Ley 24.083 + Ley 26.831).
- Beneficios fiscales en ciertos casos (exenciones a inversores en VRD/CP bajo CNV).
- Ver `../17-cnv-bcra/sto-inmobiliarios.md` y archivos CNV.

### 6.4 Tratamiento de la adjudicación al costo
- No es transferencia onerosa para el fiduciante adjudicatario.
- Costo de adquisición del fiduciante = aporte realizado.
- Si luego vende, calcula ganancia desde ese costo.
- Sellos provincial: en algunas jurisdicciones se aplica al boleto + adjudicación, en otras solo a la escritura.

> Ver `./estructuras-fiscales/fideicomiso-al-costo.md`, `./estructuras-fiscales/fideicomiso-ordinario.md`, `./estructuras-fiscales/fideicomiso-financiero.md`.

---

## 7. Vendedor extranjero (beneficiario del exterior)

### 7.1 Régimen aplicable
- Retención del escribano al momento de escriturar.
- Base: ganancia real (si se acredita) o presunta (art. 13 LIG = 50% del precio).
- Alícuota: 35% sobre ganancia real (= 15% sobre precio) o 17,5% sobre presunción.
- Sin DDJJ adicional si la retención es definitiva.

### 7.2 CDI (convenio doble imposición)
- AR tiene CDI con muchos países (Brasil, Alemania, España, Italia, EEUU, Canadá, Chile, Suiza, etc.).
- Algunos CDI eximen o reducen la retención.
- Otros redistribuyen: tributa solo país de residencia.
- Requiere certificado de residencia fiscal del país parte.

### 7.3 UIF reforzada
- Vendedor extranjero = sujeto de mayor escrutinio.
- Documentación de origen de fondos.
- Si PEP extranjero → reporte obligatorio.

---

## 8. Sellos provinciales — quick reference

| Jurisdicción | Alícuota típica venta inmueble | Notas |
|---|---|---|
| CABA | 3,5% | Vivienda única hasta cierto monto: alícuotas reducidas |
| PBA | 1,2% – 3,6% | Escalonado; vivienda única reducción |
| Córdoba | 1,5% – 4% | Varía por valor y destino |
| Santa Fe | 1% – 3% | Varía por valor |
| Mendoza | 1,5% – 4% | Reducciones por vivienda única |
| Otras | 1,2% – 3,5% | Verificar Código Fiscal vigente |

- **Quién paga**: práctica general 50/50, pero el Código Fiscal de cada provincia tiene la responsabilidad solidaria.
- **Boleto**: en algunas provincias también paga sello (anticipo o complementario).
- **Cesión de boleto**: en general paga sello.
- **Adjudicación fideicomiso**: tratamiento provincial variable.

> Ver `./provincial/[provincia].md` para detalle.

---

## 9. IIBB provincial — habitualistas

### 9.1 Cuándo aplica
- Vendedor habitualista (PF o PJ).
- Sociedad cuyo objeto incluye RE.
- Constructor/desarrollador que vende.
- Broker (sobre comisión, no sobre precio).

### 9.2 Alícuotas típicas
- 1,5% – 6% sobre base imponible.
- Convenio Multilateral si actividad en varias jurisdicciones.
- Algunas provincias diferencian construcción (más bajo) de comercialización (más alto).

### 9.3 Trampas
- PF que vende > 1 inmueble por año y no se inscribió IIBB → ajuste retroactivo + multa.
- Convenio Multilateral mal liquidado → ajustes interjurisdiccionales.

---

## 10. COTI — Código de Oferta de Transferencia de Inmuebles

### 10.1 Qué es
- Obligación AFIP (Resol. AFIP 2371/2007 y modif.).
- El **comercializador** (broker, vendedor directo) debe obtener COTI antes de ofrecer.
- Sirve para que AFIP rastree la operación desde la oferta.

### 10.2 Quién lo solicita
- Propietario PF / PJ que pone en venta directamente.
- Broker que recibe el mandato.
- Necesario antes de publicar (en serio, AFIP cruza con portales).

### 10.3 Sin COTI
- Escribano puede negarse a escriturar.
- Multas formales.
- Riesgo de ROS UIF.

---

## 11. Operaciones que NO se deben hacer

### 11.1 Subdeclarar precio en escritura
- Defraudación fiscal (Ley Penal Tributaria — Ley 27.430 modif.).
- Riesgo penal con monto significativo.
- Base imponible futura del comprador queda baja (problema al revender).
- Plata "no declarada" no se puede mostrar después (UIF + AFIP).
- Si el comprador se ve descubierto, en general delata al vendedor.

### 11.2 Pagar en efectivo > umbrales UIF
- Sujeto obligado (escribano, broker) tiene ROS prácticamente obligatorio.
- Bloqueo de la operación.
- Antecedente UIF para futuras operaciones.

### 11.3 Vender desde monotributo categorías bajas
- Monotributo no es compatible con volumen RE en general.
- AFIP recategoriza retroactivo.
- Pierde el monotributo (exclusión).

### 11.4 Vender sociedad con activo único sin planning
- Riesgo de recalificación como liquidación.
- Carga fiscal mayor que en venta del inmueble + dividendo organizado.
- Decisión clave: vender el inmueble o vender las acciones (cada uno tiene tratamiento diferente).

### 11.5 Cesión de boleto en cadena para "blanquear"
- Cada cesión paga sellos y deja huella.
- AFIP detecta cesiones múltiples + UIF.
- No es un mecanismo válido de optimización.

---

## 12. Estructuras de optimización (legales)

### 12.1 Régimen de reemplazo (vivienda única)
- ITI: aplica si pre-2018.
- Cedular: aplica si post-2018 y vivienda única destinada a uso propio + reemplazo.
- Plazo: 1 año antes o después.
- Trámite previo o post (según régimen).

### 12.2 Sucesión y planning generacional
- Donación con reserva de usufructo: transmite valor a herederos diferido.
- Costo: impuesto a la transmisión gratuita (algunas provincias) + bienes personales.
- Diferimiento de plusvalía futura del heredero.

### 12.3 Sociedad familiar / fideicomiso de planificación
- Vehículo para gestionar y vender progresivamente.
- Costo fiscal corriente vs beneficio sucesorio.
- Análisis caso por caso.

### 12.4 Reinversión productiva
- Si vendedor PF habitualista: ciertos quebrantos compensables con otros ingresos cedulares (limitado).
- Si sociedad: quebrantos acumulados 5 años para compensar (LIG).

### 12.5 Reorganización societaria
- Fusión / escisión: pueden diferir impuestos si cumple Ley 19.550 + LIG art. 77-78.
- Requisitos formales y de continuidad.

---

## 13. Cronograma fiscal típico de una venta

| Momento | Acción fiscal |
|---|---|
| Pre-oferta | COTI + planning fiscal + clasificación |
| Boleto | Sellos al boleto (jurisdicciones que aplican) |
| Pre-escritura | Cálculo retención escribano + certificados libre deuda |
| Escritura | Pago ITI o cedular (anticipo escribano) + sellos + honorarios |
| Mes siguiente | F931 si empleador, IIBB del mes si habitualista |
| Cierre fiscal anual | DDJJ Ganancias / cedular / bienes personales con la operación incluida |
| Hasta 5 años post | Riesgo de inspección AFIP (prescripción) |
| Hasta 10 años post | Riesgo si no se presentó DDJJ |

---

## 14. Errores frecuentes y consecuencias

| Error | Consecuencia |
|---|---|
| Subdeclarar precio | Multa + denuncia penal + UIF |
| No solicitar COTI | Bloqueo escritura + multa formal |
| No obtener certificado de no retención si reemplazo | Pagar ITI + recuperar después |
| Confundir ITI con cedular | Cálculo erróneo, ajuste posterior |
| No documentar mejoras / costo | AFIP toma valor mínimo |
| Habitualista no inscripto IIBB | Ajuste retroactivo + multa |
| Sociedad vende activo único sin planning | Mayor carga fiscal evitable |
| Vendedor extranjero sin retención | Escribano responsable, ROS UIF |
| Ignorar plusvalía urbana (CABA) | Reclamo municipal post escritura |
| Pagar parcial en efectivo > umbral UIF | ROS + bloqueo |
| No conservar comprobantes 10 años | Sin defensa ante AFIP |
| Asumir CDI sin certificado de residencia | Retención completa |

---

## 15. Preguntas clave (al cliente vendedor)

- ¿Es tu única vivienda?
- ¿Vas a comprar otra en 1 año?
- ¿Cuándo y cómo adquiriste el inmueble? (escritura, costo, mejoras documentadas)
- ¿Estás inscripto en algún régimen relacionado (IIBB, IVA, monotributo)?
- ¿Cuántas operaciones de venta hiciste en los últimos 5 años?
- ¿Hay sociedad o fideicomiso titular?
- ¿Hay residencia fiscal extranjera?
- ¿Cómo querés cobrar (USD, ARS, en cuánto tiempo)?
- ¿Tenés origen de fondos para mostrar si AFIP pregunta cómo lo compraste?

---

## 16. Cuándo escalar al contador / abogado fiscal

| Situación | Asesor |
|---|---|
| Operación > USD 500k o complejidad | Contador RE + abogado fiscal |
| Posible habitualidad | Contador + abogado tributario |
| Vendedor extranjero | Abogado tributario internacional |
| Sociedad vendedora con quebrantos / dividendos | Contador societario |
| Fideicomiso vendedor | Contador especialista fideicomisos |
| Régimen de reemplazo | Contador + escribano coordinados |
| Operación con PEP | Compliance UIF + abogado tributario |
| Discusión con AFIP (inspección, ajuste) | Abogado tributario litigante |
| Reorganización societaria asociada | Abogado tributario + societario |
| Plusvalía urbana | Abogado urbanístico + tributario |

---

## 17. Resumen ejecutivo

- **PF no habitualista**: la pregunta clave es **cuándo se adquirió** el inmueble. Pre-2018 = ITI 1,5%. Post-2018 = cedular 15%.
- **Vivienda única** abre vías de exención (reemplazo o art. 20 inc. o).
- **Habitualista** = Ganancias 3ra cat + IVA si construye + IIBB. Cuidado con la recalificación retroactiva.
- **Sociedad** = 35% gan + IVA si aplica + sellos + IIBB. Distribución posterior agrega capa.
- **Fideicomiso al costo** = pass-through; el resultado fiscal lo tiene el fiduciante adjudicatario.
- **Extranjero** = retención escribano 15%/17,5%; CDI puede modificar.
- **No subdeclarar nunca**. No vale la pena el riesgo penal + UIF + base baja futura.
- **COTI obligatorio** antes de ofrecer.
- **5 años de prescripción AFIP** (10 si no presentaste DDJJ).
- **Planning previo** ahorra siempre más que el costo del contador.

---

## 18. Reglas operativas para el chat

- **Estable y respondible:** estructura del árbol de decisión, marcos por perfil (PF/habitualista/PJ/fideicomiso/extranjero), ITI vs cedular, IVA en obra propia, COTI, errores frecuentes, preguntas clasificadoras.
- **🔴 Volátil — validar antes de citar:** alícuotas concretas (ganancias PJ, dividendos, sellos por provincia, IIBB, retenciones), topes vivienda única vigentes, escalas Bienes Personales, moratorias/blanqueos abiertos, modificaciones post Ley 27.743, CDI específicos.
- **Si el usuario pregunta "¿cuánto pago?":** pedir primero las 6 preguntas clasificadoras y ubicar el régimen.
- **Si la operación es > USD 500k o tiene sociedad/fideicomiso/extranjero:** advertir escalación a asesor.
- **Nunca sugerir** subdeclaración, pago en efectivo > umbrales, esquemas de evasión.
- **Tono:** contador RE que ya planeó muchas operaciones. Operativo, no academicista. Citar alícuotas con advertencia de validar fecha.

---

**Ver también:**
- `./nacional/ganancias.md`
- `./nacional/iva.md`
- `./nacional/cedular-inmuebles.md`
- `./nacional/bienes-personales.md`
- `./nacional/monotributo.md`
- `./provincial/_overview.md`
- `./municipal/contribuciones-y-plusvalia.md`
- `./estructuras-fiscales/comparativa-vehiculos.md`
- `./estructuras-fiscales/fideicomiso-al-costo.md`
- `./estructuras-fiscales/fideicomiso-ordinario.md`
- `./estructuras-fiscales/fideicomiso-financiero.md`
- `./estructuras-fiscales/sas.md`
- `./estructuras-fiscales/condominio.md`
- `../12-suelo-y-dominio/due-diligence-integral-protocolo.md`
- `../02-normativa/contratos-boleto-clausulas-de-oro.md`
- `../17-cnv-bcra/` (UIF, instrumentos)
