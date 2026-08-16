import os
import threading
import webbrowser


def abrir_web(icon, item):
    webbrowser.open("http://localhost:5000")


def abrir_carpeta_exe(application_path: str):
    def handler(icon, item):
        os.startfile(application_path)

    return handler


def abrir_logs(application_path: str):
    def handler(icon, item):
        log_dir = os.path.join(application_path, "logs")
        if os.path.exists(log_dir):
            os.startfile(log_dir)
        else:
            print("La carpeta de logs aún no se ha creado.")

    return handler


def buscar_actualizaciones():
    def handler(icon, item):
        def _worker():
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


def salir_aplicacion(icon, item):
    print("Cerrando la aplicación por completo...")
    icon.stop()
    os._exit(0)
