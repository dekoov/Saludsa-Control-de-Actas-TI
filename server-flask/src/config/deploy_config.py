import os
import sys

def resolve_route(relative_route, is_frontend=False):
    """
    Obtiene la ruta a los recursos (dist o templates) tanto en el .exe como en local.
    """
    # 1. Modo ejecutable empaquetado (PyInstaller)
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_route)

    # 2. Modo desarrollo local
    CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
    SRC_DIR = os.path.dirname(CONFIG_DIR)    # src/
    PROJECT_ROOT = os.path.dirname(SRC_DIR)  # server-flask/
    
    if is_frontend:
        # Busca en la carpeta de React
        target_path = os.path.join(PROJECT_ROOT, '..', 'client-react', relative_route)
    else:
        # Busca en la carpeta del backend (Flask)
        target_path = os.path.join(PROJECT_ROOT, relative_route)
        
    return os.path.abspath(target_path)
