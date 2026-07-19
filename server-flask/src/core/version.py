import os
import sys

VERSION_FALLBACK = "0.0.0-dev"


def get_current_version() -> str:
    """
    Lee la versión de la aplicación desde el archivo version.txt.

    - En el .exe (PyInstaller) el archivo viaja empaquetado y se busca en sys._MEIPASS.
    - En desarrollo local se busca en server-flask/version.txt.
    - Si el archivo no existe (desarrollo), retorna "0.0.0-dev".
    """
    if hasattr(sys, '_MEIPASS'):
        version_path = os.path.join(sys._MEIPASS, 'version.txt')
    else:
        CORE_DIR = os.path.dirname(os.path.abspath(__file__))
        SRC_DIR = os.path.dirname(CORE_DIR)          # src/
        PROJECT_ROOT = os.path.dirname(SRC_DIR)      # server-flask/
        version_path = os.path.join(PROJECT_ROOT, 'version.txt')

    try:
        with open(version_path, 'r', encoding='utf-8') as f:
            return f.read().strip() or VERSION_FALLBACK
    except OSError:
        return VERSION_FALLBACK


CURRENT_VERSION = get_current_version()
