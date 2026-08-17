"""Punto de entrada del backend Flask de Control de Actas TI — Saludsa.

Este módulo realiza la inicialización completa de la aplicación Flask:

1. Carga las variables de entorno desde ``.env`` y detecta si la aplicación
   corre como ejecutable PyInstaller o en desarrollo local.
2. Configura logging, valida configuraciones críticas (LDAP, bot, correo),
   inicializa la base de datos, registra los blueprints de la API y sirve el
   frontend React empaquetado.
3. En el punto de entrada protegido ``if __name__ == "__main__"`` se gestiona
   la instancia única en Windows, se verifica el entorno de Playwright, se
   lanza el icono de la bandeja del sistema y se inicia el servidor web
   (waitress en producción o Werkzeug en desarrollo), siempre restringido a
   loopback.
"""

import multiprocessing
import os
import sys

from dotenv import load_dotenv
from src.infrastructure.updater.updater import cleanup_updater_runtime

# =======================================
# 1. CARGAR VARIABLES DE ENTORNO Y RUTAS
# =======================================
if getattr(sys, "frozen", False):
    # Si es .exe (PyInstaller), obtenemos la ruta de donde está el ejecutable
    application_path = os.path.dirname(sys.executable)
else:
    # Si estamos en local, usamos la ruta de este archivo main.py
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, ".env")
load_dotenv(env_path)

from src.config import config, resolve_route, setup_logging

setup_logging()
cleanup_updater_runtime()

import logging

logger = logging.getLogger(__name__)

print(f"Validando variables cargadas desde: {env_path}")
logger.info("Variables de entorno cargadas; inicio de aplicación SaludsaActas")

# =======================================
# 2. DEFINIR LA APLICACIÓN FLASK (Global)
# =======================================
import logging
from datetime import timedelta

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from src.config import config
from src.features.actas.router import equipment_bp
from src.features.ad.router import user_bp
from src.features.auth.router import auth_bp
from src.features.dashboard.router import dashboard_bp
from src.features.discounts.router import discounts_bp
from src.features.drafts.router import drafts_bp
from src.features.email.router import email_bp
from src.infrastructure.persistence.db import init_db
from src.infrastructure.updater.router import update_bp

logger = logging.getLogger(__name__)

# VALIDACIONES CRÍTICAS DE ENTORNO (Registradas en los Logs)
if not config.validate_ldap_config():
    missing_ldap = config.get_missing_ldap_vars()
    logger.warning(
        f"CONFIGURACIÓN INCOMPLETA: Faltan variables LDAP en el .env: {', '.join(missing_ldap)}"
    )

if not config.validate_bot_config():
    missing_bot = config.get_missing_bot_vars()
    logger.warning(
        f"CONFIGURACIÓN INCOMPLETA: Faltan credenciales del Bot YoSoySaludsa en el .env: {', '.join(missing_bot)}"
    )

if not config.validate_email_config():
    missing_email = config.get_missing_email_vars()
    logger.warning(
        f"CONFIGURACIÓN INCOMPLETA: Faltan variables del servidor SMTP/Correo en el .env: {', '.join(missing_email)}"
    )

REACT_DIR = resolve_route("dist", is_frontend=True)
app = Flask(__name__, static_folder=REACT_DIR, static_url_path="/")
app.secret_key = os.urandom(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# CORS restringido exclusivamente a orígenes loopback.
# El frontend en producción se sirve como static files desde Flask, por lo que
# normalmente no hay peticiones cross-origin. Estos orígenes cubren desarrollo.
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
)

init_db(app)

app.register_blueprint(user_bp)
app.register_blueprint(equipment_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(drafts_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)
app.register_blueprint(discounts_bp)
app.register_blueprint(update_bp)


@app.route("/")
def home() -> Response:
    """Sirve la aplicación React en la ruta raíz ``/``.

    Returns:
        Respuesta de Flask con el contenido de ``index.html`` del frontend.

    Response codes:
        200: Página principal servida correctamente.
        404: No se encontró ``index.html`` en la carpeta estática.
        500: Error interno al leer el archivo estático.
    """
    return app.send_static_file("index.html")


@app.errorhandler(404)
def serve_react_on_404(e: Exception) -> tuple[Response, int]:
    """Maneja errores 404 sirviendo el frontend o una respuesta JSON de API.

    Si la ruta no encontrada comienza con ``/api/``, retorna un error JSON.
    En cualquier otro caso, delega la ruta al frontend React para permitir
    el enrutamiento del lado del cliente.

    Args:
        e: Excepción HTTP 404 capturada por Flask.

    Returns:
        Tupla ``(Response, int)`` con la respuesta adecuada y su código de
        estado HTTP.
    """
    if request.path.startswith("/api/"):
        return jsonify({"error": "API endpoint no encontrado"}), 404
    return app.send_static_file("index.html")


# =======================================
# 3. EL PUNTO DE ARRANQUE PROTEGIDO 🛡️
# =======================================
# Todo lo que está aquí adentro SOLO se ejecutará 1 vez por el proceso maestro
if __name__ == "__main__":
    """Inicia la aplicación como proceso maestro.

    Este bloque se ejecuta únicamente cuando el archivo se ejecuta
directamente. Sus responsabilidades son:

    1. Habilitar ``multiprocessing.freeze_support()`` para ejecutables de
       Windows generados con PyInstaller.
    2. Garantizar una única instancia de la aplicación mediante un mutex de
       Windows cuando corre como ejecutable.
    3. Verificar que Playwright tenga Chromium disponible.
    4. Inicializar el icono de la bandeja del sistema (system tray).
    5. Arrancar el programador de auto-actualizaciones.
    6. Levantar el servidor WSGI, siempre restringido a ``127.0.0.1``.
    """

    # 1. Soporte vital para procesos de Windows compilados (LÍNEA 1 ABSOLUTA)
    multiprocessing.freeze_support()

    # 2. Control de Instancia Única (Mutex)
    if getattr(sys, "frozen", False):
        import ctypes

        mutex_name = "Local\\SaludsaActas_Unique_Mutex_ID_300504"
        crear_mutex = ctypes.windll.kernel32.CreateMutexW
        obtener_error = ctypes.windll.kernel32.GetLastError

        handle_mutex = crear_mutex(None, False, mutex_name)
        if obtener_error() == 183:  # ERROR_ALREADY_EXISTS
            # Cierre silencioso antes de inicializar recursos pesados
            sys.exit(0)

    # 3. Configurar entorno físico (Logs y Navegadores)
    from src.config import check_playwright, setup_logging
    from src.infrastructure.tray.tray_orchestrator import inicializar_tray

    logger.info("Buscando archivo .env en: %s", env_path)
    check_playwright()

    # 4. Lanzar el icono de la barra de tareas
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or getattr(sys, "frozen", False):
        inicializar_tray(application_path)
    else:
        print("Proceso vigilante de Flask detectado: saltando System Tray.")

    # 4.5 Iniciar el programador de auto-actualizaciones (solo activo en el .exe)
    from src.infrastructure.updater.updater import start_update_scheduler

    start_update_scheduler()

    # 5. Encender el servidor
    es_produccion = getattr(sys, "frozen", False) or config.is_production()

    # Si es .exe, FORZAMOS el debug a False por seguridad.
    # Si es local, respetamos la variable de tu config / .env
    modo_debug = False if es_produccion else config.FLASK_DEBUG

    _LOCALHOST_ONLY_HOST = "127.0.0.1"

    print("=========================================")
    print(
        f"Iniciando servidor: {'MODO PRODUCCIÓN (.exe)' if es_produccion else 'MODO DESARROLLO (Local)'}"
    )
    print(f"Binding: {_LOCALHOST_ONLY_HOST}:{config.PORT} (solo loopback)")
    print(f"Debug activo: {modo_debug}")
    print("=========================================")

    if es_produccion:
        # Servidor de producción real para Windows (Elimina el Warning de Werkzeug)
        from waitress import serve

        logger.info(
            f"Levantando servidor WSGI de producción en http://{_LOCALHOST_ONLY_HOST}:{config.PORT}"
        )
        serve(app, host=_LOCALHOST_ONLY_HOST, port=config.PORT)
    else:
        # 🛠️ Servidor de desarrollo clásico — SIEMPRE loopback
        app.run(debug=modo_debug, port=config.PORT, host=_LOCALHOST_ONLY_HOST)
