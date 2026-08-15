# C:/Users/Usuario/Code_/WindSurf/Saludsa-Demo-App/server-flask/src/core/exceptions.py
import logging
import traceback
from typing import Any

from flask import Flask

from src.api.responses import error_response

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for all application exceptions."""

    def __init__(
        self, message: str, status_code: int = 400, payload: Any | None = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

class NotFoundError(AppError):
    """404 - El recurso solicitado no existe"""

    def __init__(self, message: str, payload: None = None):
        super().__init__(message, status_code=404, payload=payload)

class ValidationError(AppError):
    """ "400 - Los datos enviados por el cliente son invalidos o incompletos."""

    def __init__(self, message: str, payload: Any | None = None):
        super().__init__(message, status_code=400, payload=payload)


class DatabaseError(AppError):
    """500 - Error relacionado con la base de datos."""

    def __init__(self, message: str, payload: Any | None = None):
        super().__init__(message, status_code=500, payload=payload)


class ExternalServiceError(AppError):
    """502 - Error al comunicarse con un servicio externo."""

    def __init__(self, message: str, payload: Any | None = None):
        super().__init__(message, status_code=502, payload=payload)


def init_error_handlers(app: Flask):
    """Registrar manejadores de errores personalizados en la aplicación Flask."""

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return error_response(
            message=error.message, details=error.payload, status_code=error.status_code
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.error(f"Unexpected error: {error!s}")
        logger.error(traceback.format_exc())

        return error_response(
            message="An unexpected error occurred. Please try again later.",
            details=str(error),
            status_code=500,
        )
