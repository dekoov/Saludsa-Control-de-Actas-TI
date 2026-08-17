"""Configuración y verificación del entorno de Playwright.

Este módulo gestiona la ubicación de los navegadores de Playwright,
garantizando que Chromium esté disponible tanto en desarrollo como en
aplicaciones empaquetadas con PyInstaller, donde se utiliza un directorio
persistente dentro de ``LOCALAPPDATA``.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "SaludsaActas"
"""str: Nombre de la aplicación usado para crear el directorio de navegadores."""

BROWSERS_DIR_NAME = "playwright-browsers"
"""str: Nombre del subdirectorio donde se almacenan los navegadores."""


def _is_frozen() -> bool:
    """Indica si la aplicación está ejecutándose como bundle PyInstaller.

    Returns:
        ``True`` si el atributo ``sys.frozen`` está presente; de lo contrario,
        ``False``.
    """
    return bool(getattr(sys, "frozen", False))


def _get_browsers_path() -> Path:
    """Obtiene el directorio persistente donde Playwright almacenará navegadores.

    Returns:
        Ruta absoluta del directorio de navegadores dentro de ``LOCALAPPDATA``.

    Raises:
        RuntimeError: Si la variable de entorno ``LOCALAPPDATA`` no está
            disponible.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")

    if not local_app_data:
        raise RuntimeError(
            "LOCALAPPDATA no está disponible; "
            "no se puede determinar ubicación de navegadores."
        )

    return Path(local_app_data) / APP_NAME / BROWSERS_DIR_NAME


def _chromium_installed(browsers_path: Path) -> bool:
    """Comprueba si existe una instalación de Chromium de Playwright.

    Args:
        browsers_path: Directorio donde se buscan los navegadores instalados.

    Returns:
        ``True`` si existe al menos un subdirectorio cuyo nombre comience con
        ``'chromium-'``; de lo contrario, ``False``.
    """
    if not browsers_path.is_dir():
        return False

    return any(
        item.is_dir() and item.name.startswith("chromium-")
        for item in browsers_path.iterdir()
    )


def _install_chromium() -> None:
    """Instala Chromium mediante el CLI de Playwright.

    Temporalmente reemplaza ``sys.argv`` para invocar el comando
    ``playwright install chromium`` y restaura el valor original al finalizar.

    Returns:
        None. Este método no retorna valor.
    """
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
    """Configura Playwright y garantiza que el navegador esté disponible.

    En desarrollo utiliza la configuración normal de Playwright, eliminando
    cualquier valor previo de ``PLAYWRIGHT_BROWSERS_PATH``. En aplicaciones
    empaquetadas con PyInstaller, apunta el entorno a un directorio persistente
    dentro de ``LOCALAPPDATA`` e instala Chromium si no está presente.

    Returns:
        None. Este método no retorna valor.

    Raises:
        RuntimeError: Si no se puede determinar la ubicación de navegadores,
            falla la instalación de Chromium o este no queda disponible tras
            intentar instalarlo.
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
