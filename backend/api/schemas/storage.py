"""
Schemas de Almacenamiento (Configuración → Almacenamiento).

La sección lista los archivos del usuario y permite renombrar / borrar /
descargar. Hoy la única fuente real es `plan_files` (planos): es la única tabla
del sistema que guarda bytes de un usuario. Los entregables que genera el chat
(PDF/XLSX) van a un bucket con URL firmada y NO tienen fila en la DB, así que no
hay forma de saber de quién es cada uno — por eso no se listan (ver docstring de
api/routes/storage.py).

El id que viaja al front es compuesto (`"planos:<uuid>"`) desde v1: cuando entre
una segunda fuente, el contrato del front no cambia.
"""
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

# Caracteres que rompen el header Content-Disposition o el filesystem del que
# descarga. Se limpian ANTES de validar longitud (si no, un nombre de 300 espacios
# pasaría el min_length y quedaría vacío en la DB).
_PROHIBIDOS = '"\\/:*?<>|\r\n\t'


def _limpiar_nombre(v):
    if not isinstance(v, str):
        return v
    # Control chars fuera (incluye \r\n que permitirían inyectar headers).
    v = "".join(c for c in v if ord(c) >= 32 or c == " ")
    for c in _PROHIBIDOS:
        v = v.replace(c, "")
    return v.strip()


NombreArchivo = Annotated[
    str,
    BeforeValidator(_limpiar_nombre),
    Field(min_length=1, max_length=255),
]


class RenameRequest(BaseModel):
    """Renombrar un archivo. Solo el nombre: nada más es editable desde acá."""

    name: NombreArchivo
