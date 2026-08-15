from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.db import db
from src.models.acta import Acta


class Empleado(db.Model):
    """Tabla para datos de empleados"""

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
        self.username = username
        self.full_name = full_name
        self.national_id = national_id
        self.city = city


    # Relationships
    actas: Mapped["Acta"] = relationship(back_populates="empleado", lazy=True)
