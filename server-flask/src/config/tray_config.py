import os
import sys
import webbrowser
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

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

    def salir_aplicacion(icon, item):
        print("Cerrando la aplicación por completo...")
        icon.stop()
        os._exit(0)

    # En pystray, el separador se invoca simplemente usando Menu.SEPARATOR (en mayúsculas)
    menu_tray = Menu(
        MenuItem('Abrir Sistema (Web)', abrir_web, default=True),
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
    icon_global = Icon("SaludsaActas", imagen_icon, "Saludsa Control Actas TI", menu_tray)
    
    # Correrlo en un Thread separado para que conviva con Flask simultáneamente
    tray_thread = threading.Thread(target=icon_global.run, daemon=True)
    tray_thread.start()
