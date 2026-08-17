"""Rutas Flask del sistema de auto-actualización.

Expone endpoints protegidos con ``@requiere_login`` para consultar la versión
actual, forzar un chequeo de actualizaciones y aplicar una actualización
descargable.
"""
from flask import Blueprint, Response

from src.api.responses import error_response, success_response
from src.core.decorators import requiere_login
from src.infrastructure.updater import updater

update_bp = Blueprint("update_bp", __name__)


@update_bp.route("/api/system/version", methods=["GET"])
@requiere_login
def system_version() -> Response:
    """Retorna información de versión y estado del sistema de actualización.

    HTTP Method: GET
    Route: /api/system/version

    Headers:
        Authentication/Sesión: Requiere sesión de técnico activa (controlada
        por ``@requiere_login``).

    Returns:
        Response: JSON con código 200.

        Estructura de respuesta exitosa::

            {
                "success": true,
                "message": "Información de versión",
                "data": {
                    "current_version": "1.2.3",
                    "update_available": false,
                    "latest_version": null,
                    "sha256": null,
                    "download_url": null,
                    "published_at": null,
                    "last_check": "2026-08-16T12:00:00+00:00",
                    "applying": false,
                    "progress": null,
                    "stage": null,
                    "error": null
                }
            }

    Response codes:
        200: Información de versión retornada exitosamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno del servidor.
    """
    return success_response(
        message="Información de versión",
        data=updater.get_version_info(),
    )


@update_bp.route("/api/system/update/check", methods=["GET"])
@requiere_login
def check_update() -> Response:
    """Fuerza un chequeo manual de actualizaciones contra el último release.

    HTTP Method: GET
    Route: /api/system/update/check

    Headers:
        Authentication/Sesión: Requiere sesión de técnico activa.

    Returns:
        Response: JSON con código 200.

        Estructura de respuesta exitosa::

            {
                "success": true,
                "message": "Chequeo de actualizaciones completado",
                "data": { ... estado actualizado de versión ... }
            }

    Side Effects:
        Invoca ``updater.check_for_updates()`` y actualiza el estado en
        memoria del sistema de actualización.

    Response codes:
        200: Chequeo completado y estado actualizado retornado.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno del servidor.
    """
    updater.check_for_updates()
    return success_response(
        message="Chequeo de actualizaciones completado",
        data=updater.get_version_info(),
    )


@update_bp.route("/api/system/update/apply", methods=["POST"])
@requiere_login
def apply_update() -> Response:
    """Inicia la descarga y aplicación de la actualización disponible.

    HTTP Method: POST
    Route: /api/system/update/apply

    Headers:
        Authentication/Sesión: Requiere sesión de técnico activa.
        Content-Type: application/json (opcional; no requiere body).

    JSON Body: Vacío. No se requieren parámetros.

    Returns:
        Response: JSON con código 200 si la actualización inicia, o 400 si no
        hay actualización disponible.

        Estructura de respuesta exitosa (200)::

            {
                "success": true,
                "message": "Descargando actualización v1.2.4...",
                "data": { ... estado de versión ... }
            }

        Estructura de respuesta de error (400)::

            {
                "success": false,
                "message": "No hay ninguna actualización disponible"
            }

    Side Effects:
        Lanza la descarga del instalador en segundo plano y programa el cierre
        de la aplicación para completar la instalación.

    Response codes:
        200: Actualización iniciada correctamente.
        400: No hay actualización disponible o ya está en curso.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno del servidor.
    """
    ok, message = updater.request_apply_update()
    if not ok:
        return error_response(message=message, status_code=400)
    return success_response(
        message=message,
        data=updater.get_version_info(),
    )