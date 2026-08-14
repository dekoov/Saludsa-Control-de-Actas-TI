import threading

from pystray import Icon, Menu

from src.core.version import CURRENT_VERSION
from src.infrastructure.tray.icon_factory import cargar_icono
from src.infrastructure.tray.menu_actions import (
    abrir_carpeta_exe,
    abrir_logs,
    abrir_web,
    buscar_actualizaciones,
    salir_aplicacion,
)


def inicializar_tray(application_path: str):
    """Configura y lanza el icono en la barra de tareas en un hilo secundario."""
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
