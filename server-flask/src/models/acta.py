"""Modelos de dominio para actas y borradores de actas.

Este módulo define las entidades SQLAlchemy que persisten la información de
actas de dotación/renovación de equipos TI, así como los borradores
intermedios que permiten guardar formularios sin generar documentos
oficiales.
"""

import enum
from typing import TYPE_CHECKING, Any

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
    """Modelo de la tabla principal de actas.

    Representa un acta de dotación o renovación de equipos TI asociada a un
    empleado. Permite registrar el estado de firma, el estado de
    sincronización con Saludsa y los archivos generados (acta y pagaré).

    Attributes:
        id (str): Identificador único del acta. Formato ``ACT-YYYYMMDD-NNN``.
            Clave primaria.
        fecha (datetime): Fecha y hora de creación del acta en UTC. No
            nulo, indexado. Valor por defecto: ``datetime.now(timezone.utc)``.
        tipo (ActaType): Tipo de acta (dotación o renovación). No nulo,
            indexado. Se almacena mediante el helper ``value_enum``.
        estado (ActaStatus): Estado actual del acta (pendiente de firma,
            firmada o anulada). No nulo, indexado. Valor por defecto:
            ``ActaStatus.PENDIENTE_FIRMA.value``.
        sincronizado_saludsa (bool): Indica si el acta ya fue sincronizada
            con los sistemas de Saludsa. No nulo, indexado. Valor por
            defecto: ``False``.
        estado_sincronizacion (SyncStatus | None): Resultado de la última
            sincronización (exitosa, fallida o pendiente). Nulo permitido.
        timestamp_sincronizacion (datetime | None): Marca temporal de la
            última sincronización. Nulo permitido.
        empleado_id (int): Identificador del empleado asociado. Clave
            foránea hacia ``empleados.id``. No nulo, indexado.
        tiene_pagare (bool): Indica si el acta incluye un pagaré. No nulo.
            Valor por defecto: ``False``.
        archivo_acta (str | None): Ruta o identificador del archivo digital
            del acta. Nulo permitido.
        archivo_pagare (str | None): Ruta o identificador del archivo
            digital del pagaré. Nulo permitido.

    Relationships:
        empleado (Empleado): Relación muchos-a-uno con el empleado.
            Configurada con ``back_populates="actas"``.
        activos (list[Activo]): Relación muchos-a-muchos con los activos
            (laptops) asociados, a través de la tabla ``acta_activos``.
            Configurada con ``back_populates="actas"``.
        accesorios (list[Accesorio]): Relación muchos-a-muchos con los
            accesorios asociados, a través de la tabla
            ``acta_accesorios``. Configurada con
            ``back_populates="actas"``.
    """

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
        """Genera un texto resumen de los equipos principales asociados.

        Returns:
            str: Cadena concatenada con el hostname, número de serie,
            fabricante y modelo de cada activo. Si no hay activos,
            retorna ``"Sin equipo principal"``.
        """
        if not self.activos:
            return "Sin equipo principal"
            
        parts = []
        for activo in self.activos:
            hostname = getattr(activo, "hostname", "N/A") or "N/A"
            parts.append(f"Host: {hostname} | SN: {activo.serial_number} | {activo.manufacturer} {activo.model}")
        return " / ".join(parts)

    @property
    def resumen_accesorios(self) -> str:
        """Genera un texto resumen de la cantidad de accesorios asociados.

        Returns:
            str: ``"+N accesorios"`` si existe al menos un accesorio, o
            ``"Sin accesorios"`` en caso contrario.
        """
        num = len(self.accesorios)
        return f"+{num} accesorios" if num > 0 else "Sin accesorios"

    # --- SERIALIZACIÓN INTELIGENTE ---

    def to_dict(self, include_history_details: bool = False) -> dict[str, Any]:
        """Convierte la instancia en un diccionario seguro para JSON.

        Serializa las columnas del modelo, convirtiendo enumeraciones a su
        valor interno y objetos ``datetime`` a formato ISO 8601. Opcionalmente
        anexa un resumen del empleado y de los equipos/accesorios asociados.

        Args:
            include_history_details (bool, optional): Si es ``True``, incluye
                la información resumida del empleado y los resúmenes de
                equipos y accesorios. Valor por defecto: ``False``.

        Returns:
            dict[str, Any]: Representación en diccionario del acta.
        """
        result: dict[str, Any] = {}
        
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
    """Modelo de la tabla para borradores de actas.

    Permite almacenar formularios parciales o completos sin generar aún el
    documento oficial del acta. El JSON del usuario y de los equipos se
    guarda de forma serializada para recuperar el estado posteriormente.

    Attributes:
        id (int): Identificador autoincremental del borrador. Clave
            primaria.
        created_at (datetime): Fecha y hora de creación en UTC. No nulo.
            Valor por defecto: ``datetime.utcnow``.
        updated_at (datetime): Fecha y hora de última actualización en UTC.
            No nulo. Valor por defecto: ``datetime.utcnow``.
            Se actualiza automáticamente con ``onupdate=datetime.utcnow``.
        titulo (str): Título descriptivo del borrador. No nulo, indexado.
            Longitud máxima: 255 caracteres.
        usuario_json (str): Información del usuario/empleado en formato
            JSON serializado. No nulo.
        equipos_json (str): Información de equipos y accesorios en formato
            JSON serializado. No nulo.
        marcar_firmada (bool): Indica si el borrador debe marcarse como
            firmada al momento de generar el acta. No nulo. Valor por
            defecto: ``False``.
    """

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
