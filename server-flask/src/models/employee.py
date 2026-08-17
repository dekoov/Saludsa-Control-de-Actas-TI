"""Modelo de dominio para los empleados del sistema.

Este módulo define la entidad ``Empleado``, que representa a los
funcionarios de Saludsa que reciben equipos TI mediante actas de dotación
o renovación. Cada empleado puede tener múltiples actas asociadas.
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.db import db
from src.models.acta import Acta


class Empleado(db.Model):
    """Modelo de la tabla de empleados.

    Almacena los datos básicos de identificación y ubicación de un empleado.
    Se utiliza como entidad principal para vincular las actas de entrega de
    equipos TI.

    Attributes:
        id (int): Identificador autoincremental del empleado. Clave
            primaria.
        username (str): Nombre de usuario único en el sistema. No nulo,
            único.
        full_name (str): Nombre completo del empleado. No nulo.
        national_id (str): Número de identificación nacional (cédula). No
            nulo, indexado.
        city (str): Ciudad o ubicación del empleado. No nulo.

    Relationships:
        actas (Acta): Relación uno-a-muchos con las actas asociadas al
            empleado. Configurada con ``back_populates="empleado"`` y
            carga ``lazy=True``.
    """

    __tablename__ = "empleados"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    national_id: Mapped[str] = mapped_column(nullable=False, index=True)
    city: Mapped[str] = mapped_column(nullable=False)

    def __init__(
        self,
        username: str,
        full_name: str,
        national_id: str,
        city: str
    ) -> None:
        """Inicializa una nueva instancia de ``Empleado``.

        Args:
            username (str): Nombre de usuario único del empleado.
            full_name (str): Nombre completo del empleado.
            national_id (str): Número de identificación nacional.
            city (str): Ciudad o ubicación del empleado.

        Returns:
            None. Este método no retorna valor.
        """
        self.username = username
        self.full_name = full_name
        self.national_id = national_id
        self.city = city


    # Relationships
    actas: Mapped["Acta"] = relationship(back_populates="empleado", lazy=True)
