"""Helper para definir columnas SQLAlchemy basadas en valores de enum.

Proporciona una fábrica que construye columnas ``Enum`` de SQLAlchemy usando
el valor de cada miembro de un ``Enum`` de Python, en lugar de su nombre.
"""
from enum import Enum

from sqlalchemy import Enum as SAEnum


def value_enum(enum_class: type[Enum]) -> SAEnum:
    """Crea una instancia de ``sqlalchemy.Enum`` que persiste los valores.

    Args:
        enum_class: Clase que hereda de ``enum.Enum``.

    Returns:
        SAEnum: Columna/tipo SQLAlchemy configurada para almacenar
        ``member.value`` de cada miembro del enum.
    """
    return SAEnum(
        enum_class,
        values_callable=lambda enum_cls: [
            member.value for member in enum_cls
        ],
    )