---
title: "PEP — Personas Expuestas Políticamente"
topic: "uif-blanqueo"
subtopic: "pep"
jurisdiction: "Nacional"
last_verified: "2026-05-11"
sources:
  - "Resoluciones UIF (varias) sobre PEP"
  - "Ley 25.246"
  - "GAFI — Recomendación 12"
keywords: [pep, persona expuesta politicamente, funcionario, alta autoridad, vinculo familiar, ddc reforzada, allegado, vinculo cercano, riesgo politico]
audience: ["sujeto obligado", "developer", "abogado", "chat"]
confidence: "alta"
---

# PEP — Personas Expuestas Políticamente

## TL;DR
- **PEP** = persona que ocupa o ha ocupado un cargo público o función relevante con poder de decisión o acceso a fondos.
- Incluye al **propio funcionario**, a sus **familiares cercanos** y **allegados** que se beneficien de su posición.
- Operar con un PEP exige **DDC reforzada** y mayor escrutinio.
- No significa que el PEP no pueda operar: significa que la verificación debe ser más profunda.

## 1. Definición

### 1.1 PEP nacional
Personas que ocupan o ocuparon, dentro de los últimos años (variable por norma vigente), cargos como:
- Presidente, vicepresidente.
- Ministros, secretarios, subsecretarios.
- Gobernadores, vicegobernadores, ministros provinciales.
- Intendentes, secretarios municipales.
- Legisladores nacionales y provinciales.
- Magistrados (jueces, fiscales).
- Cargos jerárquicos en las Fuerzas Armadas, Policía, Seguridad.
- Autoridades de organismos públicos descentralizados, BCRA, AFIP, ANSES, ANMAT, etc.
- Directores y altos ejecutivos de empresas públicas.
- Autoridades de partidos políticos.

### 1.2 PEP extranjero
- Autoridades análogas de otros países (presidentes, ministros, embajadores, jueces, militares de alto rango).

### 1.3 PEP de organismos internacionales
- Funcionarios de alta dirección de OEA, ONU, FMI, BID, OMS, etc.

### 1.4 Familiares cercanos del PEP
- Cónyuge / conviviente.
- Padres, hijos, hermanos.
- Cónyuges de los anteriores.
- (Definición exacta por norma vigente.)

### 1.5 Allegados / colaboradores cercanos
- Personas con vínculo personal o profesional estrecho:
  - Socios.
  - Apoderados.
  - Personas a quienes el PEP transfirió beneficios.

### 1.6 Plazo de permanencia
- Una persona conserva el carácter de PEP por un plazo después de dejar el cargo (típico: 2-5 años; verificar norma vigente).

## 2. Por qué importa para RE

- Operaciones inmobiliarias son históricamente un canal usado para ocultar origen ilícito de fondos vinculados a funciones públicas.
- La normativa AR y GAFI exigen escrutinio reforzado.
- Sanciones a sujetos obligados que omitan controles a un PEP son significativas.

## 3. Obligaciones reforzadas (DDC reforzada)

### 3.1 Aprobación por nivel directivo
- La operación con PEP requiere autorización del más alto nivel del sujeto obligado.

### 3.2 Origen de fondos detallado
- Documentación robusta del origen.
- Coherencia con ingresos declarados del PEP.
- Si los fondos no coinciden con remuneración pública conocida → bandera roja.

### 3.3 Monitoreo continuo
- No solo al inicio de la relación: durante toda la operación.

### 3.4 Información adicional sobre el propósito
- Por qué hace la operación, en qué se condice con su perfil.

### 3.5 ROS por defecto si hay incoherencias
- En operaciones con PEP, cualquier incoherencia menor amerita análisis detallado.

## 4. Cómo detectar al PEP

### 4.1 Autodeclaración
- Formulario / declaración jurada del cliente.
- "¿Es Ud. o algún familiar cercano una Persona Expuesta Políticamente?"

### 4.2 Listas oficiales
- AR no tiene una "lista pública oficial" universal, pero hay:
  - Listas internacionales (OFAC, ONU, UE — sanciones).
  - Listas comerciales (Refinitiv World-Check, LexisNexis, Dow Jones Risk).
- Sujeto obligado debe consultar.

### 4.3 Análisis de información pública
- Búsquedas en BORA, diarios oficiales.
- Información publicada por organismos.

## 5. Sanciones / OFAC y vínculos

- Más allá de PEP: hay personas / entidades en listas de sanciones internacionales (OFAC, ONU, UE).
- NO se puede operar con personas sancionadas (sin importar PEP).

## 6. Casos complejos

### 6.1 PEP que ya dejó el cargo
- Sigue siendo PEP por el plazo de permanencia post-cargo.

### 6.2 Familiar PEP que opera en su nombre
- DDC reforzada también.

### 6.3 Empresa de un PEP
- Beneficiario final PEP → controles a la empresa.

### 6.4 PEP socio en fideicomiso
- Todo el fideicomiso queda bajo escrutinio.

## 7. ¿Un PEP puede comprar / vender / invertir?

- **SÍ**, no está prohibido.
- PERO el sujeto obligado debe:
  - Identificarlo claramente.
  - Aplicar DDC reforzada.
  - Documentar exhaustivamente.
  - Reportar si hay sospecha.

## 8. Implicancias prácticas en RE

### 8.1 Para developers
- Si recibe inversor o comprador PEP → protocolo más exigente.
- Posibles demoras por DDC reforzada (planificar 30-60 días extras).
- Coordinar con escribano e inmobiliaria.

### 8.2 Para el PEP
- Operar bajo controles más exigentes.
- Documentar exhaustivamente origen.
- No tomar a mal la solicitud de información.

## 9. Errores comunes

- Cliente PEP que no declara → posterior detección genera problemas serios.
- Sujeto obligado que no consulta listas internacionales.
- Asumir que un PEP "menor" (por ejemplo, concejal) no aplica → puede aplicar.
- Olvidar al cónyuge / familiar cercano.
- No mantener monitoreo continuo durante la relación.

## 10. Reglas operativas para el chat

- **Estable:** definición, categorías, obligaciones reforzadas.
- **🔴 Volátil:** plazo de permanencia post-cargo, listas concretas → verificar UIF.
- **Sensible — derivar:** si la pregunta es operativa concreta con un PEP, derivar a abogado especialista.
- Tono: pep ≠ delincuente. Es un cliente con escrutinio reforzado.

## Ver también
- `./marco-uif.md`
- `./sujeto-obligado-escribanos.md`
- `./sujeto-obligado-inmobiliarias.md`
- `./kyc-y-origen-de-fondos.md`
