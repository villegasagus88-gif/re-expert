"""
Filtro de datos financieros y sensibles para la memoria automática del chat.

Por qué existe: el asistente guarda memoria **en silencio**, sin confirmación
del usuario, y hasta ahora la única barrera contra persistir un CBU o una
tarjeta era una frase en el prompt del modelo. Un prompt no es un control: es
una sugerencia estadística. Si el usuario dicta un CBU y el modelo decide
guardarlo, terminábamos con un dato financiero persistido que nunca declaramos
recolectar (art. 4 Ley 25.326: los datos deben ser adecuados y no excesivos
respecto de la finalidad).

Esto es la barrera determinista: corre en el servidor, antes del INSERT, y no
depende de que el modelo obedezca.

Criterio: **bloquear, no enmascarar**. Guardar "mi CBU es ***" no aporta nada y
deja al usuario creyendo que el dato quedó registrado.
"""
import re

# CBU/CVU argentino: 22 dígitos exactos. Se permiten separadores para atrapar
# también "0170 0599 2000 0012 3456 78".
_CBU = re.compile(r"(?<!\d)(?:\d[\s.-]?){22}(?!\d)")

# Alias de CBU: 6-20 caracteres con puntos, formato "mi.alias.mp". Se exige la
# palabra alias cerca para no matchear cualquier texto con puntos.
_ALIAS = re.compile(r"\balias\b[^\n]{0,20}?\b[a-z0-9]+(?:\.[a-z0-9]+){2,}\b", re.I)

# Tarjetas: 13-19 dígitos con separadores opcionales.
_TARJETA = re.compile(r"(?<!\d)(?:\d[\s-]?){13,19}(?!\d)")

# CVV explícito y vencimiento de tarjeta.
_CVV = re.compile(r"\b(?:cvv|cvc|cod(?:igo)?\s*de\s*seguridad)\b\D{0,10}\d{3,4}\b", re.I)
_VENCIMIENTO = re.compile(r"\b(0[1-9]|1[0-2])\s*/\s*(\d{2}|\d{4})\b")

# Contraseñas dichas en el chat.
_PASSWORD = re.compile(r"\b(?:contrase[nñ]a|password|clave|pin)\b\s*(?:es|:)\s*\S+", re.I)


def _luhn(numero: str) -> bool:
    """Valida el dígito verificador de una tarjeta. Evita marcar como tarjeta
    cualquier número largo (una superficie, un presupuesto, un expediente)."""
    d = [int(c) for c in numero if c.isdigit()]
    if not 13 <= len(d) <= 19:
        return False
    suma, par = 0, False
    for n in reversed(d):
        if par:
            n *= 2
            if n > 9:
                n -= 9
        suma += n
        par = not par
    return suma % 10 == 0


def detectar_dato_financiero(texto: str) -> str | None:
    """
    Devuelve el tipo de dato sensible detectado, o None si el texto está limpio.

    Falsos positivos: se evitan a propósito. Un CBU son 22 dígitos EXACTOS y una
    tarjeta tiene que pasar Luhn, así que montos, superficies, números de
    expediente y coordenadas no se marcan.
    """
    if not texto:
        return None
    t = str(texto)

    if _CBU.search(t):
        return "CBU/CVU"
    if _ALIAS.search(t):
        return "alias bancario"
    if _CVV.search(t):
        return "código de seguridad de tarjeta"
    if _PASSWORD.search(t):
        return "contraseña"
    for m in _TARJETA.finditer(t):
        crudo = re.sub(r"\D", "", m.group())
        # 22 dígitos ya lo agarró _CBU; acá interesan las tarjetas reales.
        if len(crudo) != 22 and _luhn(crudo):
            return "número de tarjeta"
    return None


def texto_seguro_para_memoria(*partes: str) -> tuple[bool, str | None]:
    """
    ¿Se puede persistir esto en la memoria automática?

    Devuelve (es_seguro, tipo_detectado). El caller corta antes del INSERT.
    """
    for p in partes:
        tipo = detectar_dato_financiero(p)
        if tipo:
            return False, tipo
    return True, None
