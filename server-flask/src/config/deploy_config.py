"""Resolución de rutas de recursos para desarrollo y despliegue.

Este módulo detecta si la aplicación se ejecuta como un bundle de
PyInstaller o en modo desarrollo, y proporciona utilidades para resolver
rutas absolutas a recursos estáticos, incluyendo el frontend empaquetado.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _detect_bundle_dir() -> Path | None:
    """Detecta el directorio temporal creado por PyInstaller.

    Returns:
        Ruta al directorio ``_MEIPASS`` cuando la aplicación corre empaquetada;
        de lo contrario, ``None``.
    """
    meipass = getattr(sys, "_MEIPASS", None)

    if isinstance(meipass, str):
        return Path(meipass)

    return None


BUNDLE_DIR = _detect_bundle_dir()
"""Path | None: Directorio del bundle detectado al importar el módulo."""

if BUNDLE_DIR is not None:
    logger.info("Aplicación ejecutándose como bundle PyInstaller")
else:
    logger.info("Aplicación ejecutándose en modo desarrollo")


def _get_bundle_dir() -> Path | None:
    """Retorna el directorio raíz de recursos creado por PyInstaller.

    Returns:
        ``Path`` si la aplicación corre empaquetada con PyInstaller.
        ``None`` si corre en desarrollo.
    """
    meipass = getattr(sys, "_MEIPASS", None)

    if isinstance(meipass, str):
        return Path(meipass)

    return None


def _get_project_root() -> Path:
    """Retorna la raíz del proyecto en entorno de desarrollo.

    Returns:
        Ruta absoluta al directorio ``server-flask``.
    """
    config_dir = Path(__file__).resolve().parent
    src_dir = config_dir.parent
    return src_dir.parent


def resolve_route(relative_route: str, is_frontend: bool = False) -> str:
    """Resuelve la ruta de un recurso para desarrollo o ejecutable PyInstaller.

    Args:
        relative_route: Ruta relativa al recurso dentro del proyecto o del
            bundle.
        is_frontend: Si es ``True``, busca el recurso dentro de la carpeta
            ``client-react`` del proyecto en modo desarrollo.

    Returns:
        Ruta absoluta al recurso solicitado.
    """
    bundle_dir = _get_bundle_dir()

    # PyInstaller
    if bundle_dir is not None:
        return str(bundle_dir / relative_route)

    # Desarrollo
    project_root = _get_project_root()

    if is_frontend:
        target_path = project_root.parent / "client-react" / relative_route
    else:
        target_path = project_root / relative_route

    return str(target_path.resolve())
