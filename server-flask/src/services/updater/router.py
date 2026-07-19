from flask import Blueprint

from src.core.responses import success_response, error_response
from src.core.decorators import requiere_login
from src.services.updater import updater

update_bp = Blueprint('update_bp', __name__)


@update_bp.route('/api/system/version', methods=['GET'])
@requiere_login
def system_version():
    """
    Retorna la versión actual de la aplicación junto con el estado del
    sistema de actualización (último chequeo, progreso de descarga, etc.).
    """
    return success_response(
        message="Información de versión",
        data=updater.get_version_info()
    )


@update_bp.route('/api/system/update/check', methods=['GET'])
@requiere_login
def check_update():
    """
    Fuerza un chequeo manual de actualizaciones contra el último release.
    """
    updater.check_for_updates()
    return success_response(
        message="Chequeo de actualizaciones completado",
        data=updater.get_version_info()
    )


@update_bp.route('/api/system/update/apply', methods=['POST'])
@requiere_login
def apply_update():
    """
    Inicia la descarga y aplicación de la actualización disponible.
    La app se cerrará automáticamente al finalizar para completar la instalación.
    """
    ok, message = updater.request_apply_update()
    if not ok:
        return error_response(message=message, status_code=400)
    return success_response(
        message=message,
        data=updater.get_version_info()
    )
