import os
import sys
import multiprocessing  
from dotenv import load_dotenv

# =======================================
# 1. CARGAR VARIABLES DE ENTORNO Y RUTAS
# =======================================
if getattr(sys, 'frozen', False):
    # Si es .exe (PyInstaller), obtenemos la ruta de donde está el ejecutable
    application_path = os.path.dirname(sys.executable)
else:
    # Si estamos en local, usamos la ruta de este archivo main.py
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
load_dotenv(env_path)

from src.config import config, setup_logging, resolve_route
setup_logging()

import logging
logger = logging.getLogger(__name__)

print(f"Validando variables cargadas desde: {env_path}")
# Forzamos un print directo a la terminal para verificar visualmente que no está vacío
print(f"   [LDAP SERVER]: {config.LDAP_SERVER}")
print(f"   [BOT USER]: {config.SALUDSA_USERNAME}")

# =======================================
# 2. DEFINIR LA APLICACIÓN FLASK (Global)
# =======================================
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.features.actas.router import equipment_bp
from src.services.ad.router import user_bp
from src.features.dashboard.router import dashboard_bp
from src.features.drafts.router import drafts_bp
from src.features.auth.router import auth_bp
from src.features.email.router import email_bp
from src.features.discounts.router import discounts_bp
from src.config import config, resolve_route
from src.core.db import init_db
import logging

logger = logging.getLogger(__name__)

# VALIDACIONES CRÍTICAS DE ENTORNO (Registradas en los Logs)
if not config.validate_ldap_config():
    missing_ldap = config.get_missing_ldap_vars()
    logger.warning(f"⚠️ CONFIGURACIÓN INCOMPLETA: Faltan variables LDAP en el .env: {', '.join(missing_ldap)}")

if not config.validate_bot_config():
    missing_bot = config.get_missing_bot_vars()
    logger.warning(f"⚠️ CONFIGURACIÓN INCOMPLETA: Faltan credenciales del Bot YoSoySaludsa en el .env: {', '.join(missing_bot)}")

if not config.validate_email_config():
    missing_email = config.get_missing_email_vars()
    logger.warning(f"⚠️ CONFIGURACIÓN INCOMPLETA: Faltan variables del servidor SMTP/Correo en el .env: {', '.join(missing_email)}")

REACT_DIR = resolve_route('dist', is_frontend=True)
app = Flask(__name__, static_folder=REACT_DIR, static_url_path='/')
app.secret_key = os.urandom(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)
)

CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:5000"])

init_db(app)

app.register_blueprint(user_bp)
app.register_blueprint(equipment_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(drafts_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)
app.register_blueprint(discounts_bp)

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def serve_react_on_404(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "API endpoint no encontrado"}), 404
    return app.send_static_file('index.html')

# =======================================
# 3. EL PUNTO DE ARRANQUE PROTEGIDO 🛡️
# =======================================
# Todo lo que está aquí adentro SOLO se ejecutará 1 vez por el proceso maestro
if __name__ == '__main__':
    # 1. Soporte vital para procesos de Windows compilados (LÍNEA 1 ABSOLUTA)
    multiprocessing.freeze_support()

    # 2. Control de Instancia Única (Mutex) 
    if getattr(sys, 'frozen', False):
        import ctypes
        mutex_name = "Local\\SaludsaActas_Unique_Mutex_ID_300504"
        crear_mutex = ctypes.windll.kernel32.CreateMutexW
        obtener_error = ctypes.windll.kernel32.GetLastError
        
        handle_mutex = crear_mutex(None, False, mutex_name)
        if obtener_error() == 183: # ERROR_ALREADY_EXISTS
            # Cierre silencioso antes de inicializar recursos pesados
            sys.exit(0)

    # 3. Configurar entorno físico (Logs y Navegadores)
    from src.config import setup_logging, check_playwright
    from src.config.tray_config import inicializar_tray

    print(f"Buscando .env en: {env_path}")
    check_playwright(application_path)

    # 4. Lanzar el icono de la barra de tareas
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or getattr(sys, 'frozen', False):
        inicializar_tray(application_path)
    else:
        print("Proceso vigilante de Flask detectado: saltando System Tray.")

    # 5. Encender el servidor
    es_produccion = getattr(sys, 'frozen', False) or config.is_production()
    
    # Si es .exe, FORZAMOS el debug a False por seguridad. 
    # Si es local, respetamos la variable de tu config / .env
    modo_debug = False if es_produccion else config.FLASK_DEBUG

    print(f"=========================================")
    print(f"Iniciando servidor: {'MODO PRODUCCIÓN (.exe)' if es_produccion else 'MODO DESARROLLO (Local)'}")
    print(f"Puerto: {config.PORT}")
    print(f"Debug activo: {modo_debug}")
    print(f"=========================================")
    
    if es_produccion:
        # Servidor de producción real para Windows (Elimina el Warning de Werkzeug)
        from waitress import serve
        logger.info(f"Levantando servidor WSGI de producción en http://127.0.0.1:{config.PORT}")
        serve(app, host='127.0.0.1', port=config.PORT)
    else:
        # 🛠️ Servidor de desarrollo clásico
        app.run(
            debug=modo_debug,
            port=config.PORT,
            host='127.0.0.1'
        )
