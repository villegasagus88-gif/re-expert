"""
Genera la versión PUBLICABLE de los documentos legales.

    python scripts/publicar_legales.py

Lee `legal/*.md` (la versión de trabajo, con anotaciones internas) y escribe
`frontend/legal/*.md` (lo que ve el usuario).

Por qué hace falta un conversor y no se sirve el `.md` directo
─────────────────────────────────────────────────────────────
Los documentos de `legal/` tienen tres cosas que NO pueden ir al usuario:

1. **Notas editoriales nuestras** — los bloques `[REVISIÓN LEGAL]` y
   `[LÍMITE LEGAL]`. Son el registro de qué quisimos lograr y hasta dónde llega
   la ley. Publicarlos sería mostrarle a la contraparte exactamente dónde están
   nuestras cláusulas más débiles ("Qué quisimos: que no hubiera reembolsos en
   ningún caso...").
2. **El anexo de marcadores** — la tabla de pendientes internos.
3. **El encabezado de BORRADOR**.

Y tienen datos que dependen del titular. Esos NO se borran: se convierten en
tokens `{{titular}}`, `{{cuit}}`, `{{domicilio}}`, `{{email}}`, `{{sitio}}`,
`{{vigenciaDesde}}`, que `frontend/legal.js` reemplaza en el navegador con lo
que haya en `legal-config.js`. Así el documento se puede leer completo desde
hoy, y el día que se carguen los datos queda cerrado sin tocar el texto.

Lo que sí se resuelve acá, porque el dato lo sabemos del propio código:
precio, duración del trial, ciclo de facturación y edad mínima.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "legal"
DESTINO = RAIZ / "frontend" / "legal"

DOCS = [
    "terminos-y-condiciones.md",
    "politica-de-privacidad.md",
    "politica-de-cookies.md",
]

# Marcadores que identifican una nota interna. Un blockquote que contenga
# cualquiera de estos se elimina entero.
INTERNOS = ("[REVISIÓN LEGAL]", "[LÍMITE LEGAL]", "[CONFIRMAR CON TITULAR]")

# Datos que salen del código, no del titular: se resuelven acá.
# (patrón, reemplazo)
CONOCIDOS: list[tuple[str, str]] = [
    (r"\[CONFIRMAR CON TITULAR — se sugiere 18\]", "18"),
    (
        r"\[CONFIRMAR CON TITULAR — precio actual publicado: \$69\.900 ARS\."
        r"[^\]]*\]",
        "$69.900 ARS por período de 30 (treinta) días",
    ),
    (r"\[CONFIRMAR CON TITULAR — URL definitiva\]", "{{sitio}}"),
    (r"\[CONFIRMAR CON TITULAR — fecha de publicación\]", "{{vigenciaDesde}}"),
    (
        r"\[CONFIRMAR CON TITULAR — jurisdicción del domicilio del\s*\n?\s*Titular\]",
        "la Ciudad Autónoma de Buenos Aires",
    ),
    (r"\[CONFIRMAR CON TITULAR — razón social o nombre\s*\n?\s*completo\]", "{{titular}}"),
    (r"\[CONFIRMAR CON TITULAR — razón social o nombre\]", "{{titular}}"),
    (r"CUIT \[CONFIRMAR CON TITULAR\]", "CUIT {{cuit}}"),
    (r"\*\*CUIT:\*\* \[CONFIRMAR CON TITULAR\]", "**CUIT:** {{cuit}}"),
    (r"con domicilio en \[CONFIRMAR CON TITULAR\]", "con domicilio en {{domicilio}}"),
    (r"\*\*Domicilio:\*\* \[CONFIRMAR CON TITULAR\]", "**Domicilio:** {{domicilio}}"),
    (r"\*\*Fecha de última actualización:\*\* \[CONFIRMAR CON TITULAR\]",
     "**Fecha de última actualización:** {{vigenciaDesde}}"),
    (r"\*\*Responsable:\*\* \[CONFIRMAR CON TITULAR\]", "**Responsable:** {{titular}}"),
    # Celdas de tabla: son el plazo de retención de un TERCERO, que no
    # controlamos. Decirlo así es exacto; inventar un plazo sería peor.
    (r"Según el plan contratado \*\[CONFIRMAR CON TITULAR\]\*",
     "Según el plan contratado con el proveedor"),
    (r"\*\[CONFIRMAR CON TITULAR\]\*", "Según la política del proveedor"),
    # El proveedor de IA se activa por configuración: es un hecho, no un dato
    # del titular.
    (r"\*\[CONFIRMAR CON TITULAR: activo sólo si está configurada la clave"
     r"(?: correspondiente)?\]\*",
     "*(activo sólo si ese proveedor está configurado)*"),
    # El correo y el dominio salen de la config, no hardcodeados.
    (r"`contacto@re-expert\.app`", "{{email}}"),
    (r"contacto@re-expert\.app", "{{email}}"),
]


def _quitar_blockquotes_internos(texto: str) -> str:
    """Elimina los bloques `>` que sean notas internas, con su línea en blanco."""
    lineas = texto.split("\n")
    salida: list[str] = []
    i = 0
    while i < len(lineas):
        if lineas[i].lstrip().startswith(">"):
            j = i
            while j < len(lineas) and (
                lineas[j].lstrip().startswith(">") or lineas[j].strip() == ""
            ):
                # Una línea en blanco corta el blockquote sólo si lo que sigue
                # no es otra línea `>`.
                if lineas[j].strip() == "":
                    if j + 1 >= len(lineas) or not lineas[j + 1].lstrip().startswith(">"):
                        break
                j += 1
            bloque = "\n".join(lineas[i:j])
            if any(m in bloque for m in INTERNOS):
                # Se come también la línea en blanco que quedaría colgando.
                while j < len(lineas) and lineas[j].strip() == "":
                    j += 1
                i = j
                continue
            salida.extend(lineas[i:j])
            i = j
            continue
        salida.append(lineas[i])
        i += 1
    return "\n".join(salida)


def _quitar_anexo(texto: str) -> str:
    """Corta el anexo de marcadores internos hasta el final del documento.

    Los T&C lo abren con `## Anexo — Marcadores…`; la política de cookies los
    tiene sueltos como `### [REVISIÓN LEGAL]`. Se corta desde lo primero que
    aparezca: de ahí para abajo es todo registro interno.
    """
    candidatos = [
        m.start()
        for m in re.finditer(
            r"^#{2,3} (?:Anexo\b.*|\[REVISIÓN LEGAL\]"
            r"|\[LÍMITE LEGAL\]|\[CONFIRMAR CON TITULAR\])\s*$",
            texto,
            re.M,
        )
    ]
    if candidatos:
        texto = texto[: min(candidatos)]
    # El separador `---` que quedaba colgando antes del anexo.
    return texto.rstrip().rstrip("-").rstrip() + "\n"


def _quitar_encabezado_borrador(texto: str) -> str:
    """Saca el aviso de BORRADOR y la línea de versión de trabajo."""
    texto = re.sub(
        r"^> ## ⚠️ BORRADOR.*?(?=\n\*\*Versión:)", "", texto, flags=re.S | re.M
    )
    texto = re.sub(r"^\*\*Versión:\*\* ([^\n]*?) \(borrador\)", r"**Versión:** \1", texto, flags=re.M)
    return texto


def _quitar_notas_inline(md: str) -> str:
    """Saca las notas editoriales sueltas dentro de un párrafo.

    Las que quedan después de aplicar CONOCIDOS son avisos a nosotros mismos
    ("si en el futuro se ofrece un SLA…"), no texto del contrato. Pueden ocupar
    varias líneas, así que el patrón cruza saltos de línea.
    """
    return re.sub(
        r"[ \t]*\[(?:REVISIÓN LEGAL|LÍMITE LEGAL|CONFIRMAR CON TITULAR)"
        r"[^\]]*\][ \t]*\n?",
        "",
        md,
    )


def convertir(md: str) -> str:
    md = _quitar_encabezado_borrador(md)
    md = _quitar_anexo(md)
    md = _quitar_blockquotes_internos(md)
    for patron, reemplazo in CONOCIDOS:
        md = re.sub(patron, reemplazo, md)
    md = _quitar_notas_inline(md)
    # Tres líneas en blanco seguidas quedan feas después de sacar bloques.
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    return md.strip() + "\n"


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    problemas = 0
    for nombre in DOCS:
        origen = ORIGEN / nombre
        if not origen.exists():
            print(f"  ⚠️  falta {origen}")
            problemas += 1
            continue
        salida = convertir(origen.read_text(encoding="utf-8"))

        # Red de seguridad: si algún marcador interno sobrevivió, es un bug del
        # conversor y NO se puede publicar así. Se busca el nombre del marcador
        # SIN el corchete de cierre: la primera versión de este chequeo pedía
        # `[CONFIRMAR CON TITULAR]` literal y dejó pasar una nota inline con
        # texto adentro (`[CONFIRMAR CON TITULAR — si en el futuro…]`).
        restos = [
            m for m in (*INTERNOS, "[BORRADOR", "Anexo — Marcadores")
            if m.rstrip("]") in salida
        ]
        if restos:
            print(f"  ❌ {nombre}: sobrevivieron marcadores {restos}")
            problemas += 1
            continue

        (DESTINO / nombre).write_text(salida, encoding="utf-8")
        tokens = sorted(set(re.findall(r"\{\{(\w+)\}\}", salida)))
        print(
            f"  ✅ {nombre}: {len(salida.splitlines())} líneas"
            f" (de {len(origen.read_text(encoding='utf-8').splitlines())})"
            f" · tokens: {', '.join(tokens) or 'ninguno'}"
        )
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
