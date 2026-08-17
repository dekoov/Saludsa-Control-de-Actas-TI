"""Gestión de la versión actual de la aplicación.

Este módulo lee la versión del proyecto desde un archivo ``version.txt``,
soportando tanto el modo de desarrollo local como el modo empaquetado con
PyInstaller (``sys._MEIPASS``). Si no se encuentra el archivo, se utiliza un
valor de respaldo.
"""

import os
import sys

VERSION_FALLBACK = "0.0.0-dev"
"""str: Versión por defecto cuando no se puede leer ``version.txt``."""


def get_current_version() -> str:
    """Lee la versión de la aplicación desde el archivo ``version.txt``.

    - En el ejecutable generado por PyInstaller, el archivo se busca en
      ``sys._MEIPASS``.
    - En desarrollo local se busca en ``server-flask/version.txt``.
    - Si el archivo no existe o no se puede leer, retorna ``VERSION_FALLBACK``.

    Returns:
        Cadena con la versión actual de la aplicación.
    """
    if hasattr(sys, "_MEIPASS"):
        version_path = os.path.join(sys._MEIPASS, "version.txt")
    else:
        CORE_DIR = os.path.dirname(os.path.abspath(__file__))
        SRC_DIR = os.path.dirname(CORE_DIR)          # src/
        PROJECT_ROOT = os.path.dirname(SRC_DIR)      # server-flask/
        version_path = os.path.join(PROJECT_ROOT, "version.txt")

    try:
        with open(version_path, "r", encoding="utf-8") as file:
            return file.read().strip() or VERSION_FALLBACK
    except OSError:
        return VERSION_FALLBACK


CURRENT_VERSION = get_current_version()
"""str: Versión actual de la aplicación resuelta al importar el módulo."""
