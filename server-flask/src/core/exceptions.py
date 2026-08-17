"""Excepciones personalizadas y manejadores globales de errores.

Este módulo define una jerarquía de excepciones propias de la aplicación que
permiten comunicar errores de negocio con códigos HTTP asociados. También
registra los manejadores globales que convierten dichas excepciones en
respuestas JSON estandarizadas.
"""

import logging
import traceback
from typing import Any

from flask import Flask, Response

from src.api.responses import error_response

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Excepción base para todos los errores controlados de la aplicación.

    Attributes:
        message: Mensaje descriptivo del error.
        status_code: Código HTTP asociado al error.
        payload: Datos adicionales sobre el error que se incluirán en la
            respuesta JSON.
    """

    def __init__(
        self, message: str, status_code: int = 400, payload: Any | None = None
    ):
        """Inicializa una excepción de aplicación.

        Args:
            message: Mensaje descriptivo del error.
            status_code: Código de estado HTTP asociado. Por defecto ``400``.
            payload: Datos adicionales a incluir en la respuesta de error.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


class NotFoundError(AppError):
    """Excepción para recursos no encontrados (HTTP 404)."""

    def __init__(self, message: str, payload: None = None):
        """Inicializa un error de tipo ``NotFoundError``.

        Args:
            message: Mensaje descriptivo indicando qué recurso no existe.
            payload: No se utiliza; se mantiene por compatibilidad con la
                interfaz base.
        """
        super().__init__(message, status_code=404, payload=payload)


class ValidationError(AppError):
    """Excepción para datos de entrada inválidos o incompletos (HTTP 400)."""

    def __init__(self, message: str, payload: Any | None = None):
        """Inicializa un error de tipo ``ValidationError``.

        Args:
            message: Mensaje descriptivo del error de validación.
            payload: Detalles adicionales sobre los campos o valores inválidos.
        """
        super().__init__(message, status_code=400, payload=payload)


class DatabaseError(AppError):
    """Excepción para errores relacionados con la base de datos (HTTP 500)."""

    def __init__(self, message: str, payload: Any | None = None):
        """Inicializa un error de tipo ``DatabaseError``.

        Args:
            message: Mensaje descriptivo del error de base de datos.
            payload: Datos adicionales sobre el error.
        """
        super().__init__(message, status_code=500, payload=payload)


class ExternalServiceError(AppError):
    """Excepción para errores al comunicarse con servicios externos (HTTP 502)."""

    def __init__(self, message: str, payload: Any | None = None):
        """Inicializa un error de tipo ``ExternalServiceError``.

        Args:
            message: Mensaje descriptivo del error del servicio externo.
            payload: Datos adicionales sobre el error.
        """
        super().__init__(message, status_code=502, payload=payload)


def init_error_handlers(app: Flask) -> None:
    """Registra manejadores de errores personalizados en la aplicación Flask.

    Configura dos manejadores globales: uno para excepciones de tipo
    ``AppError`` (o sus subclases) y otro para cualquier excepción inesperada.
    Ambos retornan respuestas JSON consistentes generadas por ``error_response``.

    Args:
        app: Instancia de la aplicación Flask donde se registrarán los
            manejadores de error.

    Returns:
        None. Este método no retorna valor.
    """

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError) -> tuple[Response, int]:
        """Maneja excepciones controladas de tipo ``AppError``.

        Args:
            error: Excepción de aplicación capturada.

        Returns:
            Tupla ``(Response, int)`` con la respuesta JSON de error y su
            código de estado HTTP.
        """
        return error_response(
            message=error.message, details=error.payload, status_code=error.status_code
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> tuple[Response, int]:
        """Maneja excepciones inesperadas no controladas.

        Registra el error y su traza en los logs antes de retornar una
        respuesta genérica de error interno con código HTTP ``500``.

        Args:
            error: Excepción inesperada capturada.

        Returns:
            Tupla ``(Response, int)`` con la respuesta JSON de error interno
            y el código de estado ``500``.
        """
        logger.error(f"Unexpected error: {error!s}")
        logger.error(traceback.format_exc())

        return error_response(
            message="An unexpected error occurred. Please try again later.",
            details=str(error),
            status_code=500,
        )
