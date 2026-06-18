from enum import Enum

class EquipmentStatus(Enum):
    NUEVO = 'Nuevo'
    USADO = 'Usado'

class EquipmentType(Enum):
    LAPTOP = 'Laptop'
    DESKTOP = 'Desktop'
    MONITOR = 'Monitor'
    TECLADO = 'Teclado'
    MOUSE = 'Mouse'
    CARGADOR = 'Cargador'
    DIADEMA = 'Diadema'
    MOCHILA = 'Mochila'

class ActaType(Enum):
    DOTACION = 'Dotacion'
    RENOVACION = 'Renovacion'

class ActaStatus(Enum):
    PENDIENTE_FIRMA = "PENDIENTE_FIRMA"
    FIRMADA = "FIRMADA"
    ANULADA = "ANULADA"

class SyncStatus(Enum):
    EXITOSA = 'Exitosa'
    FALLIDA = 'Fallida'
    PENDIENTE = 'Pendiente'
