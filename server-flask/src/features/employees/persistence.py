from typing import Any

from src.infrastructure.persistence.db import db
from src.models.employee import Empleado


def upsert_empleado(usuario_data: dict[str, Any]) -> Empleado:
    """Upsert empleado: si username existe, reusar; si no, crear nuevo"""
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
