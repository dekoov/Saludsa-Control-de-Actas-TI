"""Orquestador del icono de bandeja del sistema.

Combina la fábrica de iconos y las acciones del menú para inicializar
``pystray.Icon`` en un hilo daemon, permitiendo que la aplicación Flask
continúe ejecutándose en primer plano.
"""
import threading

from pystray import Icon, Menu, MenuItem

from src.core.version import CURRENT_VERSION
from src.infrastructure.tray.icon_factory import cargar_icono
from src.infrastructure.tray.menu_actions import (
    abrir_carpeta_exe,
    abrir_logs,
    abrir_web,
    buscar_actualizaciones,
    salir_aplicacion,
)


def inicializar_tray(application_path: str) -> None:
    """Configura y lanza el icono en la bandeja de tareas en un hilo secundario.

    Args:
        application_path: Ruta base de la aplicación, usada para cargar el
            icono y resolver las acciones de menú.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        - Crea una variable global ``icon_global``.
        - Lanza ``pystray.Icon.run`` en un hilo daemon.
    """
    imagen_icon = cargar_icono(application_path)

    menu_tray = Menu(
        MenuItem("Abrir Sistema (Web)", abrir_web, default=True),
        MenuItem("Buscar actualizaciones", buscar_actualizaciones()),
        MenuItem("Abrir carpeta del programa", abrir_carpeta_exe(application_path)),
        MenuItem("Ver carpeta de Logs", abrir_logs(application_path)),
        Menu.SEPARATOR,
        MenuItem("Salir", salir_aplicacion),
    )

    global icon_global
    icon_global = Icon(
        "SaludsaActas",
        imagen_icon,
        f"Saludsa Control Actas TI v{CURRENT_VERSION}",
        menu_tray,
    )

    tray_thread = threading.Thread(target=icon_global.run, daemon=True)
    tray_thread.start()