"""Capa de persistencia para empleados.

Gestiona la creación y reutilación de registros de empleados en base de datos.
Si un empleado con el mismo username ya existe, se retorna el existente;
de lo contrario se crea uno nuevo.
"""

from typing import Any

from src.infrastructure.persistence.db import db
from src.models.employee import Empleado


def upsert_empleado(usuario_data: dict[str, Any]) -> Empleado:
    """Crea o reutiliza un registro de empleado.

    Busca un empleado por username. Si existe, lo retorna; si no, crea un nuevo
    registro con los datos proporcionados y lo agrega a la sesión de base de
    datos.

    Args:
        usuario_data: Diccionario con los datos del empleado. Se esperan las
            claves username, full_name, national_id y city.

    Returns:
        Empleado: Instancia del modelo Empleado existente o recién creada.
    """
    username = usuario_data.get("username")
    empleado = Empleado.query.filter_by(username=username).first()

    if not empleado:
        empleado = Empleado(
            username=usuario_data.get("username", ""),
            full_name=usuario_data.get("full_name", ""),
            national_id=usuario_data.get("national_id", ""),
            city=usuario_data.get("city", ""),
        )
        db.session.add(empleado)
        db.session.flush()

    return empleado
