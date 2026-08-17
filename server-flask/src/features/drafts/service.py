"""Servicio utilitario para la generación de títulos de borradores.

Construye un título descriptivo y legible para cada borrador a partir del
nombre del empleado y los equipos incluidos, facilitando su identificación en
el listado de borradores.
"""

from datetime import datetime
from typing import Any


def generate_draft_title(
    usuario: dict[str, Any], equipos: list[dict[str, Any]]
) -> str:
    """Genera un título automático para un borrador.

    El formato varía según la cantidad y tipo de equipos:
    - Sin equipos: "Nombre - Sin equipos - DD/MM HH:MM".
    - Un equipo: "Nombre - Tipo Marca - DD/MM HH:MM".
    - Dos equipos: "Nombre - Tipo1 + Tipo2 - DD/MM".
    - Más de dos: "Nombre - Tipo1 + N accesorios - DD/MM".

    Args:
        usuario: Datos del empleado destinatario. Debe contener full_name.
        equipos: Lista de equipos asociados al borrador.

    Returns:
        str: Título generado para el borrador.
    """
    nombre = usuario.get("full_name", "Usuario")

    if not equipos or len(equipos) == 0:
        return f"{nombre} - Sin equipos - {datetime.now().strftime('%d/%m %H:%M')}"

    # Si hay un solo equipo principal (laptop)
    if len(equipos) == 1:
        eq = equipos[0]
        tipo = eq.get("equipment_type", "Equipo")
        marca = eq.get("manufacturer", "")
        return f"{nombre} - {tipo} {marca} - {datetime.now().strftime('%d/%m %H:%M')}"

    # Si hay múltiples equipos
    tipos = [eq.get("equipment_type", "Equipo") for eq in equipos]
    if len(tipos) == 2:
        return (
            f"{nombre} - {tipos[0]} + {tipos[1]} - {datetime.now().strftime('%d/%m')}"
        )
    else:
        return (
            f"{nombre} - {tipos[0]} + {len(tipos) - 1} accesorios - "
            f"{datetime.now().strftime('%d/%m')}"
        )
