"""Acciones del menú contextual del icono de bandeja.

Cada función expuesta retorna un handler compatible con ``pystray.MenuItem`` o
puede usarse directamente como callback. Gestiona apertura de la web, carpetas,
búsqueda de actualizaciones y cierre de la aplicación.
"""
import os
import threading
import webbrowser
from typing import Any

from pystray import Icon as TrayIcon


def abrir_web(icon: TrayIcon, item: Any) -> None:
    """Abre la aplicación web en el navegador predeterminado.

    Args:
        icon: Instancia del icono de bandeja.
        item: Elemento del menú que disparó la acción.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        Abre ``http://localhost:5000`` en el navegador del sistema.
    """
    webbrowser.open("http://localhost:5000")


def abrir_carpeta_exe(application_path: str) -> Any:
    """Retorna un handler que abre la carpeta de instalación de la aplicación.

    Args:
        application_path: Ruta de la carpeta a abrir.

    Returns:
        Callable: Función handler para ``pystray.MenuItem``.
    """
    def handler(icon: TrayIcon, item: Any) -> None:
        """Abre la carpeta de instalación de la aplicación.

        Args:
            icon: Instancia del icono de bandeja.
            item: Elemento del menú que disparó la acción.

        Returns:
            None. Este método no retorna valor.
        """
        os.startfile(application_path)

    return handler


def abrir_logs(application_path: str) -> Any:
    """Retorna un handler que abre la carpeta de logs si existe.

    Args:
        application_path: Ruta base donde se encuentra la carpeta ``logs``.

    Returns:
        Callable: Función handler para ``pystray.MenuItem``.
    """
    def handler(icon: TrayIcon, item: Any) -> None:
        """Abre la carpeta de logs si ya fue creada.

        Args:
            icon: Instancia del icono de bandeja.
            item: Elemento del menú que disparó la acción.

        Returns:
            None. Este método no retorna valor.
        """
        log_dir = os.path.join(application_path, "logs")
        if os.path.exists(log_dir):
            os.startfile(log_dir)
        else:
            print("La carpeta de logs aún no se ha creado.")

    return handler


def buscar_actualizaciones() -> Any:
    """Retorna un handler que verifica actualizaciones en segundo plano.

    Returns:
        Callable: Función handler para ``pystray.MenuItem`` que lanza un hilo
        daemon para consultar el sistema de actualización.
    """
    def handler(icon: TrayIcon, item: Any) -> None:
        """Consulta actualizaciones disponibles y notifica el resultado.

        Args:
            icon: Instancia del icono de bandeja.
            item: Elemento del menú que disparó la acción.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Lanza un hilo daemon que ejecuta ``check_for_updates`` y muestra
            una notificación con el resultado.
        """
        def _worker() -> None:
            """Tarea en segundo plano que verifica actualizaciones.

            Returns:
                None. Este método no retorna valor.
            """
            from src.infrastructure.updater.updater import (
                check_for_updates,
                get_version_info,
            )

            try:
                disponible = check_for_updates()
                if disponible:
                    info = get_version_info()
                    icon.notify(
                        f"Hay una nueva versión disponible: v{info['latest_version']}. "
                        "Actualiza desde la ventana web del sistema.",
                        "Saludsa Actas",
                    )
                else:
                    icon.notify(
                        "Ya tienes la versión más reciente instalada.", "Saludsa Actas"
                    )
            except Exception as e:
                print(f"No se pudo buscar actualizaciones: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    return handler


def salir_aplicacion(icon: TrayIcon, item: Any) -> None:
    """Cierra la aplicación completamente.

    Args:
        icon: Instancia del icono de bandeja.
        item: Elemento del menú que disparó la acción.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        Detiene el icono de bandeja y termina el proceso con ``os._exit``.
    """
    print("Cerrando la aplicación por completo...")
    icon.stop()
    os._exit(0)