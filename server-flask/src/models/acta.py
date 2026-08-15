import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .employee import Empleado
    from .equipment import Accesorio

from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.db import db
from src.infrastructure.persistence.enums_value import value_enum

from .enums import ActaStatus, ActaType, SyncStatus
from .equipment import Activo, acta_accesorios, acta_activos


class Acta(db.Model):
    """Tabla principal de actas"""

    __tablename__ = "actas"

    id: Mapped[str] = mapped_column(primary_key=True)  # Formato "ACT-YYYYMMDD-NNN"

    fecha: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    tipo: Mapped[ActaType] = mapped_column(value_enum(ActaType), nullable=False, index=True)

    estado: Mapped[ActaStatus] = mapped_column(
        value_enum(ActaStatus), default=ActaStatus.PENDIENTE_FIRMA.value, nullable=False, index=True
    )
    sincronizado_saludsa: Mapped[bool] = mapped_column(
        default=False, nullable=False, index=True
    )
    estado_sincronizacion: Mapped[SyncStatus | None] = mapped_column(value_enum(SyncStatus), nullable=True)

    timestamp_sincronizacion: Mapped[datetime | None] = mapped_column(nullable=True)

    empleado_id: Mapped[int] = mapped_column(
        ForeignKey("empleados.id"), nullable=False, index=True
    )
    tiene_pagare: Mapped[bool] = mapped_column(default=False, nullable=False)

    archivo_acta: Mapped[str | None] = mapped_column(nullable=True)

    archivo_pagare: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    empleado: Mapped["Empleado"] = relationship(back_populates="actas")

    activos: Mapped[list["Activo"]] = relationship(
        secondary=acta_activos, back_populates="actas"
    )

    accesorios: Mapped[list["Accesorio"]] = relationship(
        secondary=acta_accesorios, back_populates="actas"
    )

    # ----- LOGICA DE NEGOCIO ENCAPSULADA -----

    @property
    def resumen_equipos(self) -> str:
        """Genera el texto resumen de los equipos asociados al acta."""
        if not self.activos:
            return "Sin equipo principal"
            
        parts = []
        for activo in self.activos:
            hostname = getattr(activo, "hostname", "N/A") or "N/A"
            parts.append(f"Host: {hostname} | SN: {activo.serial_number} | {activo.manufacturer} {activo.model}")
        return " / ".join(parts)

    @property
    def resumen_accesorios(self) -> str:
        """Genera el texto resumen de la cantidad de accesorios."""
        num = len(self.accesorios)
        return f"+{num} accesorios" if num > 0 else "Sin accesorios"

    # --- SERIALIZACIÓN INTELIGENTE ---

    def to_dict(self, include_history_details=False) -> dict:
        """
        Convierte el modelo a un diccionario seguro para JSON.
        Si include_history_details es True, anexa las relaciones formateadas.
        """
        result = {}
        
        # 1. Serialización dinámica de columnas
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            if isinstance(value, enum.Enum):
                result[column.name] = value.value
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
                
        # 2. Inclusión opcional de relaciones (Para la vista frontend)
        if include_history_details:
            result["empleado"] = {
                "full_name": self.empleado.full_name if self.empleado else "N/A",
                "username": getattr(self.empleado, "username", "N/A") if self.empleado else "N/A",
            }
            result["equipos_resumen"] = self.resumen_equipos
            result["accesorios_resumen"] = self.resumen_accesorios
            
        return result


class ActaDraft(db.Model):
    """Tabla para borradores de actas (formularios guardados sin generar documentos)"""

    __tablename__ = "acta_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    titulo: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    usuario_json: Mapped[str] = mapped_column(nullable=False)
    equipos_json: Mapped[str] = mapped_column(nullable=False)
    marcar_firmada: Mapped[bool] = mapped_column(default=False, nullable=False)
