"""Enumeraciones del dominio de actas.

Este módulo define los tipos de documentos que pueden generarse dentro del
subdominio de actas, como el acta propiamente dicha y su pagaré
asociado.
"""

from enum import Enum


class DocumentType(Enum):
    """Tipos de documentos que el sistema puede generar para un acta.

    Attributes:
        ACTA (str): Documento principal de entrega de equipos TI.
        PAGARE (str): Documento de pagaré asociado al acta, cuando aplica.
    """

    ACTA = "ACTA"
    PAGARE = "PAGARE"
