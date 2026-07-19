import os
import sys
import webbrowser
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

from src.core.version import CURRENT_VERSION

def crear_icono_por_defecto():
    """Genera un icono temporal (un cuadrado azul con bordes redondeados)."""
    img = Image.new('RGB', (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([(16, 16), (48, 48)], fill=(255, 255, 255))
    return img

def inicializar_tray(application_path):
    """Configura y lanza el icono en la barra de tareas en un hilo secundario."""
    
    def abrir_web(icon, item):
        webbrowser.open('http://localhost:5000')

    def abrir_carpeta_exe(icon, item):
        os.startfile(application_path)

    def abrir_logs(icon, item):
        log_dir = os.path.join(application_path, "logs")
        if os.path.exists(log_dir):
            os.startfile(log_dir)
        else:
            print("La carpeta de logs aún no se ha creado.")

    def buscar_actualizaciones(icon, item):
        """Lanza un chequeo manual de actualizaciones sin bloquear el menú del tray."""
        def _worker():
            from src.services.updater.updater import check_for_updates, get_version_info
            try:
                disponible = check_for_updates()
                if disponible:
                    info = get_version_info()
                    icon.notify(
                        f"Hay una nueva versión disponible: v{info['latest_version']}. "
                        "Actualiza desde la ventana web del sistema.",
                        "Saludsa Actas"
                    )
                else:
                    icon.notify("Ya tienes la versión más reciente instalada.", "Saludsa Actas")
            except Exception as e:
                print(f"No se pudo buscar actualizaciones: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def salir_aplicacion(icon, item):
        print("Cerrando la aplicación por completo...")
        icon.stop()
        os._exit(0)

    # En pystray, el separador se invoca simplemente usando Menu.SEPARATOR (en mayúsculas)
    menu_tray = Menu(
        MenuItem('Abrir Sistema (Web)', abrir_web, default=True),
        MenuItem('Buscar actualizaciones', buscar_actualizaciones),
        MenuItem('Abrir carpeta del programa', abrir_carpeta_exe),
        MenuItem('Ver carpeta de Logs', abrir_logs),
        Menu.SEPARATOR, 
        MenuItem('Salir', salir_aplicacion)
    )

    # Intentamos buscar tu favicon.svg o dist para el icono
    if getattr(sys, 'frozen', False):
        ruta_logo = os.path.join(application_path, "_internal", "dist", "favicon.svg")
    else:
        ruta_logo = os.path.abspath(os.path.join(application_path, "..", "client-react", "dist", "favicon.svg"))

    if os.path.exists(ruta_logo):
        try:
            imagen_icon = Image.open(ruta_logo)
        except Exception:
            imagen_icon = crear_icono_por_defecto()
    else:
        imagen_icon = crear_icono_por_defecto()

    global icon_global
    icon_global = Icon("SaludsaActas", imagen_icon, f"Saludsa Control Actas TI v{CURRENT_VERSION}", menu_tray)
    
    # Correrlo en un Thread separado para que conviva con Flask simultáneamente
    tray_thread = threading.Thread(target=icon_global.run, daemon=True)
    tray_thread.start()
