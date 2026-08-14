import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

def _detect_bundle_dir() -> Path | None:
    meipass = getattr(sys, "_MEIPASS", None)

    if isinstance(meipass, str):
        return Path(meipass)

    return None

BUNDLE_DIR = _detect_bundle_dir()

if BUNDLE_DIR is not None:
    logger.info("Aplicación ejecutándose como bundle PyInstaller")
else:
    logger.info("Aplicación ejecutándose en modo desarrollo")


def _get_bundle_dir() -> Path | None:
    """
    Retorna directorio raíz de recursos creado por PyInstaller.

    Returns:
        Path si aplicación corre empaquetada con PyInstaller.
        None si corre en desarrollo.
    """
    meipass = getattr(sys, "_MEIPASS", None)

    if isinstance(meipass, str):
        return Path(meipass)

    return None


def _get_project_root() -> Path:
    """
    Retorna raíz del proyecto en entorno de desarrollo.
    """
    config_dir = Path(__file__).resolve().parent
    src_dir = config_dir.parent
    return src_dir.parent


def resolve_route(relative_route: str, is_frontend: bool = False) -> str:
    """
    Resuelve ruta de recursos para desarrollo o ejecutable PyInstaller.

    Args:
        relative_route: Ruta relativa al recurso.
        is_frontend: Si True, busca recurso dentro de client-react.

    Returns:
        Ruta absoluta al recurso.
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
