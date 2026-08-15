import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "SaludsaActas"
BROWSERS_DIR_NAME = "playwright-browsers"


def _is_frozen() -> bool:
    """Indica si la aplicación está ejecutándose como bundle PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def _get_browsers_path() -> Path:
    """
    Obtiene directorio persistente donde Playwright almacenará navegadores.

    Raises:
        RuntimeError: Si LOCALAPPDATA no está disponible.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")

    if not local_app_data:
        raise RuntimeError(
            "LOCALAPPDATA no está disponible; "
            "no se puede determinar ubicación de navegadores."
        )

    return Path(local_app_data) / APP_NAME / BROWSERS_DIR_NAME


def _chromium_installed(browsers_path: Path) -> bool:
    """Comprueba si existe una instalación de Chromium de Playwright."""
    if not browsers_path.is_dir():
        return False

    return any(
        item.is_dir() and item.name.startswith("chromium-")
        for item in browsers_path.iterdir()
    )


def _install_chromium() -> None:
    """Instala Chromium mediante Playwright."""
    from playwright.__main__ import main as playwright_main

    original_argv = sys.argv.copy()

    try:
        sys.argv = [
            "playwright",
            "install",
            "chromium",
        ]

        playwright_main()

    finally:
        sys.argv = original_argv


def check_playwright() -> None:
    """
    Configura Playwright y garantiza navegador disponible.

    En desarrollo utiliza configuración normal de Playwright.
    En PyInstaller utiliza directorio persistente dentro de LOCALAPPDATA.
    """
    if not _is_frozen():
        os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
        logger.info("Playwright: modo desarrollo.")
        return

    browsers_path = _get_browsers_path()
    browsers_path.mkdir(parents=True, exist_ok=True)

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

    logger.info(
        "Playwright: modo empaquetado. Navegadores: %s",
        browsers_path,
    )

    if _chromium_installed(browsers_path):
        logger.info("Playwright: Chromium ya está instalado.")
        return

    logger.info("Playwright: Chromium no encontrado. Instalando...")

    try:
        _install_chromium()
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise RuntimeError(
                f"Playwright no pudo instalar Chromium. Código: {exc.code}"
            ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Error durante instalación de Chromium."
        ) from exc

    if not _chromium_installed(browsers_path):
        raise RuntimeError(
            "Playwright terminó instalación, pero Chromium no fue encontrado."
        )

    logger.info("Playwright: Chromium instalado correctamente.")
