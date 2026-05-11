---
title: "FAQ base — preguntas frecuentes del chat RE"
topic: "meta"
subtopic: "faq"
jurisdiction: "Argentina"
last_verified: "2026-05-11"
keywords: [faq, preguntas frecuentes, q&a, intent, respuestas tipo]
audience: ["chat", "tester", "qa"]
confidence: "alta"
---

# FAQ base

Set de preguntas frecuentes con respuesta de referencia y file/anchor de la KB. Sirve para:
- Validar que el chat responde alineado a la KB.
- Acelerar respuesta vía cache / few-shot.
- Detectar gaps de conocimiento.

Formato: **Q** → respuesta breve → archivo de soporte.

## Fundamentos

**Q: ¿Qué hace un developer inmobiliario?**
- A: Articula tierra, capital, equipo técnico y comercial para crear inmuebles que valen más que sus partes. Toma riesgo de plazo, costo y mercado.
- Fuente: `00-fundamentos/teoria-developer.md`

**Q: ¿Qué es triple impacto en RE?**
- A: Modelo que evalúa financiero + social + ambiental. Aplica a proyectos con certificaciones (LEED/EDGE), vivienda asequible, regeneración urbana.
- Fuente: `00-fundamentos/triple-impacto.md`

## Constitución y leyes

**Q: ¿Quién regula la actividad inmobiliaria?**
- A: Concurrencia: Nación (CCyCN, AFIP, BCRA, CNV, UIF, SSN), provincia (Códigos urbanísticos, ARBA, sellos) y municipio (habilitaciones, permisos).
- Fuente: `01-constitucion-y-leyes/concurrencia-nacion-provincias.md`

**Q: ¿Qué dice el CCyCN sobre boleto y escritura?**
- A: Boleto: contrato preparatorio (art. 1170-1171). Escritura: forma exigida (art. 1017). Posesión + buena fe protegen al comprador (1170).
- Fuente: `02-derecho-civil/boleto-y-escritura.md`

## Construcción

**Q: ¿Qué documentación necesito antes de empezar obra?**
- A: Plano municipal aprobado + permiso de obra + Aviso de Obra ART + Programa de Seguridad aprobado + responsable matriculado + alta de trabajadores + seguros (TRC + RC + caución).
- Fuente: `05-construccion/permisos-y-habilitaciones.md` + `18-seguros/art-decreto-911.md`

**Q: ¿Por administración o ajuste alzado?**
- A: Administración: developer asume riesgo de costos, mejor visibilidad. Ajuste alzado: constructora asume riesgo, prima más alta. Híbrido GMP en obras grandes.
- Fuente: `05-construccion/modalidades-contratacion.md`

## Financiero

**Q: ¿Cómo se reparten ganancias entre developer e inversores?**
- A: Waterfall típico: devolución de capital → preferred return 8-12% → catch-up → split 80/20 (inversores/developer).
- Fuente: `06-financiero/waterfall-inversores.md`

**Q: ¿Conviene hipoteca UVA?**
- A: Depende del salario nominal vs inflación + capacidad de soportar volatilidad. En contexto de salarios indexados es viable; con salarios atrasados es riesgoso.
- Fuente: `06-financiero/hipoteca-uva.md`

## Comercial

**Q: ¿Qué CRM uso para inmobiliaria?**
- A: Tokko (líder AR), HubSpot, Pipedrive. Integrar con ZonaProp + Argenprop + portales + WhatsApp Business API.
- Fuente: `07-comercial/crm-stack-tecnologico.md`

**Q: ¿Cuánto invertir en marketing digital?**
- A: 2-5% del precio de la unidad como benchmark. Mix Meta Ads + Google Ads + SEO + portales según target.
- Fuente: `07-comercial/marketing-digital.md`

## Macro

**Q: ¿Cómo afecta el cepo a comprador extranjero?**
- A: Ingresan USD por MULC al tipo oficial, brecha con MEP/CCL. Alternativa: USD billete declarado. Análisis caso a caso.
- Fuente: `17-cnv-bcra/cepo-cambiario.md`

**Q: ¿Es seguro cobrar en USDT?**
- A: Sí con PSAV registrado + KYC + UIF + asesor. Documentar origen + hash + conversión a USD/ARS para devengar.
- Fuente: `17-cnv-bcra/psav-cripto.md`

## Tributario

**Q: ¿Quién paga IVA en venta de vivienda nueva?**
- A: Constructor / developer paga IVA 10,5% sobre obra. Crédito fiscal por compras. Comprador no es contribuyente directo.
- Fuente: `10-tributario-nacional/iva-en-re.md` (si existe)

**Q: ¿Bienes Personales sobre el inmueble?**
- A: Persona humana sobre valor fiscal vs alícuota progresiva. Sociedad: responsable sustituto. Análisis con contador.
- Fuente: `10-tributario-nacional/bienes-personales.md` (si existe)

## Costos y presupuesto

**Q: ¿Qué contingencia presupuestar?**
- A: 5-15% según etapa: 15% en anteproyecto, 10% proyecto ejecutivo, 5% durante obra. En AR sube por inflación + FX.
- Fuente: `14-costos-presupuesto/contingencias-imprevistos.md`

**Q: ¿Qué índice de redeterminación uso?**
- A: ICC INDEC + CAC + UVA + USD según contrato. Polinómica típica en obras públicas.
- Fuente: `14-costos-presupuesto/indices-costo.md`

## Seguros

**Q: ¿Qué seguros necesito en obra?**
- A: Mínimo: TRC + RC + ART + caución cumplimiento del constructor. Opcionales: RC profesional + vicios redhibitorios + sismo (zonas).
- Fuente: `18-seguros/README.md`

**Q: ¿Qué cubre y qué no cubre el TRC?**
- A: Cubre: daños materiales a la obra (incendio, robo, daños accidentales, fenómenos). NO cubre: vicios proyecto, lucro cesante, daños a terceros (eso es RC).
- Fuente: `18-seguros/trc-construccion.md`

## UIF / KYC

**Q: ¿Soy sujeto obligado UIF como inmobiliaria?**
- A: Sí (Res. UIF 28/2018). Debes hacer DDC + ROS + reportes + capacitar.
- Fuente: `16-uif-blanqueo/sujeto-obligado-inmobiliarias.md`

**Q: ¿Origen de fondos del comprador?**
- A: Documentar siempre: extracto bancario + declaración jurada + contraparte + factura/escritura previa. Mayor exigencia con > USD 30k aprox.
- Fuente: `16-uif-blanqueo/kyc-y-origen-de-fondos.md`

## CNV / mercado de capitales

**Q: ¿Qué es un fideicomiso financiero en RE?**
- A: Vehículo CNV para securitizar flujos de un proyecto. Emite VDF (deuda) + CP (equity). Para proyectos > USD 5-10M.
- Fuente: `17-cnv-bcra/vehiculos-cnv-re.md`

## Tecnología

**Q: ¿La IA puede tasar inmuebles?**
- A: Sí, AVM (Automated Valuation Model) es estándar internacional. En AR todavía emergente, con sesgo por falta de datos.
- Fuente: `15-tecnologia-proptech/ia-en-real-estate.md`

## Reglas operativas para el chat

- Usar este FAQ como guía de tono y referencia rápida.
- Cada Q tiene archivo de soporte: si la respuesta requiere más profundidad, leer el archivo de soporte primero.
- Si la pregunta no está aquí pero está cubierta en la KB → responder desde la KB y proponer añadir al FAQ.
- Si la pregunta no está cubierta → declarar el gap y redirigir.

## Ver también
- `./indice-rapido.md`
- `./instrucciones-chat.md`
- `./glosario.md`
- `./fuentes-oficiales.md`
