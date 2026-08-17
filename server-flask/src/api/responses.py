"""Utilidades para construir respuestas HTTP JSON consistentes.

Este módulo expone funciones auxiliares que estandarizan la estructura de
las respuestas exitosas y de error devueltas por la API REST del backend.
Todas las funciones retornan una tupla ``(Response, status_code)`` compatible
con el retorno directo de rutas Flask.
"""

import math
from typing import Any

from flask import Response, jsonify


def success_response(
    message: str = "Success",
    data: Any = None,
    meta: dict[str, Any] | None = None,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Response, int]:
    """Genera una respuesta JSON de éxito con un formato consistente.

    La respuesta incluye siempre los campos ``status`` y ``message``. Los
    campos ``data`` y ``meta`` solo se incluyen cuando se proporcionan.

    Args:
        message: Mensaje descriptivo de la operación exitosa.
        data: Datos a incluir en la respuesta. Se omiten si es ``None``.
        meta: Metadatos adicionales (paginación, totales, etc.). Se omiten
            si es ``None``.
        status_code: Código de estado HTTP a retornar. Por defecto ``200``.
        headers: Diccionario de cabeceras HTTP a añadir a la respuesta.

    Returns:
        Tupla ``(Response, int)`` con el objeto ``Response`` de Flask y el
        código de estado HTTP correspondiente.

    Example:
        >>> success_response("Usuario creado", data={"id": 1})
        (<Response 52 bytes [200 OK]>, 200)
    """
    payload = {
        "status": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    response = jsonify(payload)
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response, status_code


def error_response(
    message: str,
    details: Any | None = None,
    status_code: int = 400,
    headers: dict[str, str] | None = None,
) -> tuple[Response, int]:
    """Genera una respuesta JSON de error con un formato consistente.

    La respuesta incluye los campos ``status`` y ``message``. El campo
    ``details`` solo se incluye cuando se proporciona.

    Args:
        message: Mensaje descriptivo del error.
        details: Información adicional sobre el error. Se omiten si es ``None``.
        status_code: Código de estado HTTP a retornar. Por defecto ``400``.
        headers: Diccionario de cabeceras HTTP a añadir a la respuesta.

    Returns:
        Tupla ``(Response, int)`` con el objeto ``Response`` de Flask y el
        código de estado HTTP correspondiente.
    """
    payload = {"status": False, "message": message}
    if details is not None:
        payload["details"] = details
    response = jsonify(payload)

    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response, status_code


def created_response(
    message: str = "Resource created successfully",
    data: Any | None = None,
    meta: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[Response, int]:
    """Genera una respuesta JSON para recursos creados exitosamente.

    Es un envoltorio de ``success_response`` que utiliza el código de estado
    HTTP ``201 Created``.

    Args:
        message: Mensaje descriptivo de la creación.
        data: Datos del recurso creado. Se omiten si es ``None``.
        meta: Metadatos adicionales. Se omiten si es ``None``.
        headers: Diccionario de cabeceras HTTP a añadir a la respuesta.

    Returns:
        Tupla ``(Response, int)`` con el objeto ``Response`` de Flask y el
        código de estado ``201``.
    """
    return success_response(
        message=message, data=data, meta=meta, status_code=201, headers=headers
    )


def no_content_response(
    message: str = "No content", headers: dict[str, str] | None = None
) -> tuple[Response, int]:
    """Genera una respuesta JSON para casos donde no hay contenido que devolver.

    Aunque el código de estado es ``204 No Content``, la función retorna un
    cuerpo JSON mínimo para mantener la consistencia con el resto de la API.

    Args:
        message: Mensaje descriptivo de la ausencia de contenido.
        headers: Diccionario de cabeceras HTTP a añadir a la respuesta.

    Returns:
        Tupla ``(Response, int)`` con el objeto ``Response`` de Flask y el
        código de estado ``204``.
    """
    response = jsonify({"status": True, "message": message})
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response, 204


def paginated_response(
    message: str,
    data: list[Any],
    page: int,
    per_page: int,
    total_items: int,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[Response, int]:
    """Genera una respuesta JSON paginada con metadatos de paginación.

    Calcula automáticamente el número total de páginas y los indicadores
    ``has_next`` y ``has_prev`` a partir de los parámetros recibidos.

    Args:
        message: Mensaje descriptivo de la operación exitosa.
        data: Lista de elementos de la página actual.
        page: Número de página actual (comienza en ``1``).
        per_page: Cantidad máxima de elementos por página.
        total_items: Cantidad total de elementos disponibles.
        status_code: Código de estado HTTP a retornar. Por defecto ``200``.
        headers: Diccionario de cabeceras HTTP a añadir a la respuesta.

    Returns:
        Tupla ``(Response, int)`` con el objeto ``Response`` de Flask y el
        código de estado HTTP correspondiente.

    Example:
        >>> paginated_response("Ok", data=[1, 2], page=1, per_page=2, total_items=5)
        (<Response 120 bytes [200 OK]>, 200)
    """
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0

    meta = {
        "current_page": page,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
    return success_response(
        message=message, data=data, meta=meta, status_code=status_code, headers=headers
    )
