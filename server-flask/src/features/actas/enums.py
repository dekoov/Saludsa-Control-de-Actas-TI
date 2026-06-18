# src/features/actas/enums.py
from enum import Enum

class DocumentType(Enum):
    """Tipos de documentos que el sistema puede generar."""
    ACTA = "ACTA"
    PAGARE = "PAGARE"
