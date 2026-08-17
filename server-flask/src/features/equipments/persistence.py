"""Capa de persistencia para equipos y activos.

Gestiona la creación y reutilación de activos principales (laptops) por número
de serie, así como la inserción siempre nueva de accesorios asociados a un acta.
"""

from typing import Any

from src.infrastructure.persistence.db import db
from src.models.equipment import Accesorio, Activo


def upsert_activo(equipo_data: dict[str, Any]) -> Activo:
    """Crea o reutiliza un activo principal (laptop) por número de serie.

    Si ya existe un Activo con el mismo serial_number, retorna el existente. De
    lo contrario, crea un nuevo registro con los datos del equipo y lo agrega a
    la sesión.

    Args:
        equipo_data: Diccionario con los datos del activo. Se esperan las
            claves manufacturer, model, serial_number, hostname, purchase_cost,
            status, location y observation.

    Returns:
        Activo: Instancia del modelo Activo existente o recién creada.
    """
    serial_number = equipo_data.get("serial_number")
    activo = Activo.query.filter_by(serial_number=serial_number).first()

    if not activo:
        activo = Activo(
            manufacturer=equipo_data.get("manufacturer"),
            model=equipo_data.get("model"),
            serial_number=serial_number,
            hostname=equipo_data.get("hostname"),
            purchase_cost=equipo_data.get("purchase_cost"),
            status=equipo_data.get("status"),
            location=equipo_data.get("location"),
            observation=equipo_data.get("observation", ""),
        )
        db.session.add(activo)
        db.session.flush()

    return activo


def insert_accesorio(equipo_data: dict[str, Any]) -> Accesorio:
    """Inserta un nuevo accesorio en base de datos.

    A diferencia de los activos principales, los accesorios siempre se crean
    como registros nuevos para permitir múltiples unidades idénticas en
    distintos actas.

    Args:
        equipo_data: Diccionario con los datos del accesorio. Se esperan las
            claves equipment_type, manufacturer, model, serial_number, quantity,
            purchase_cost, status, location y observation.

    Returns:
        Accesorio: Instancia del modelo Accesorio recién creada.
    """
    accesorio = Accesorio(
        equipment_type=equipo_data.get("equipment_type"),
        manufacturer=equipo_data.get("manufacturer"),
        model=equipo_data.get("model"),
        serial_number=equipo_data.get("serial_number", "NA"),
        quantity=equipo_data.get("quantity"),
        purchase_cost=equipo_data.get("purchase_cost"),
        status=equipo_data.get("status"),
        location=equipo_data.get("location"),
        observation=equipo_data.get("observation", ""),
    )
    db.session.add(accesorio)
    db.session.flush()
    return accesorio
