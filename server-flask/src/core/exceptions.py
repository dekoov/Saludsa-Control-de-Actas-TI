# C:/Users/Usuario/Code_/WindSurf/Saludsa-Demo-App/server-flask/src/core/exceptions.py
from flask import Flask, jsonify
import logging
import traceback
from typing import Any, Optional
from src.core.responses import error_response

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base class for all application exceptions."""
    def __init__(self, message: str, status_code: int = 400, payload: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

class ValidationError(AppError):
    """"400 - Los datos enviados por el cliente son invalidos o incompletos."""
    def __init__(self, message: str, payload: Optional[Any] = None):
        super().__init__(message, status_code=400, payload=payload)

class DatabaseError(AppError):
    """500 - Error relacionado con la base de datos."""
    def __init__(self, message: str, payload: Optional[Any] = None):
        super().__init__(message, status_code=500, payload=payload)

class ExternalServiceError(AppError):
    """502 - Error al comunicarse con un servicio externo."""
    def __init__(self, message: str, payload: Optional[Any] = None):
        super().__init__(message, status_code=502, payload=payload)


def init_error_handlers(app: Flask):
    """Registrar manejadores de errores personalizados en la aplicación Flask."""

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        # CORRECCIÓN: Asumimos que tienes importado 'error_response' de src.core.responses
        return error_response(
            message=error.message,
            details=error.payload,
            status_code=error.status_code
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.error(f"Unexpected error: {str(error)}")
        logger.error(traceback.format_exc())

        return error_response(
            message="An unexpected error occurred. Please try again later.",
            details=str(error),
            status_code=500
        )
