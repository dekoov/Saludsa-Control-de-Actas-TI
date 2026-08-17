"""Enumeraciones compartidas del dominio de Control de Actas TI.

Este módulo centraliza los tipos enumerados que se utilizan en los modelos
SQLAlchemy para representar estados, tipos de equipos y resultados de
sincronización de forma tipada y consistente.
"""

from enum import Enum


class EquipmentStatus(Enum):
    """Estados posibles de un equipo en el inventario.

    Attributes:
        NUEVO (str): Equipo nuevo, aún no asignado o recién ingresado.
        USADO (str): Equipo que ha sido utilizado previamente.
    """

    NUEVO = 'Nuevo'
    USADO = 'Usado'


class EquipmentType(Enum):
    """Tipos de equipos y accesorios soportados por el sistema.

    Attributes:
        LAPTOP (str): Computadora portátil.
        DESKTOP (str): Computadora de escritorio.
        MONITOR (str): Monitor o pantalla externa.
        TECLADO (str): Teclado.
        MOUSE (str): Mouse o ratón.
        CARGADOR (str): Cargador de laptop.
        DIADEMA (str): Diadema o auriculares con micrófono.
        MOCHILA (str): Mochila para transporte de equipos.
    """

    LAPTOP = 'Laptop'
    DESKTOP = 'Desktop'
    MONITOR = 'Monitor'
    TECLADO = 'Teclado'
    MOUSE = 'Mouse'
    CARGADOR = 'Cargador'
    DIADEMA = 'Diadema'
    MOCHILA = 'Mochila'


class ActaType(Enum):
    """Tipos de actas que puede generar el sistema.

    Attributes:
        DOTACION (str): Acta de dotación inicial de equipos a un empleado.
        RENOVACION (str): Acta de renovación o reemplazo de equipos
            existentes.
    """

    DOTACION = 'Dotacion'
    RENOVACION = 'Renovacion'


class ActaStatus(Enum):
    """Estados del ciclo de vida de un acta.

    Attributes:
        PENDIENTE_FIRMA (str): El acta fue generada pero aún no ha sido
            firmada.
        FIRMADA (str): El acta ya fue firmada por las partes involucradas.
        ANULADA (str): El acta fue anulada y no tiene efecto.
    """

    PENDIENTE_FIRMA = "PENDIENTE_FIRMA"
    FIRMADA = "FIRMADA"
    ANULADA = "ANULADA"


class SyncStatus(Enum):
    """Resultados posibles de la sincronización con Saludsa.

    Attributes:
        EXITOSA (str): La última sincronización finalizó correctamente.
        FALLIDA (str): La última sincronización presentó errores.
        PENDIENTE (str): Existe una sincronización pendiente por ejecutar.
    """

    EXITOSA = 'Exitosa'
    FALLIDA = 'Fallida'
    PENDIENTE = 'Pendiente'
