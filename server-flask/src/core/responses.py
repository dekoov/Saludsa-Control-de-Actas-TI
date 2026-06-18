import math
from flask import jsonify, Response
from typing import Any, Optional, Dict, List, Tuple

def success_response(
        message: str = "Success",
        data: Any = None, 
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
) -> Tuple[Response, int]:
    """Genera una respuesta JSON de éxito con un formato consistente."""
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
        details: Optional[Any] = None,
        status_code: int = 400,
        headers: Optional[Dict[str, str]] = None
    ) -> Tuple[Response, int]:
        """Genera una respuesta JSON de error con un formato consistente."""
        payload = {
            "status": False,
            "message": message
        }
        if details is not None:
            payload["details"] = details
        response = jsonify(payload)

        if headers:
            for key, value in headers.items():
                response.headers[key] = value
        return response, status_code

def created_response(
        message: str = "Resource created successfully",
        data: Optional[Any] = None, 
        meta: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
) -> Tuple[Response, int]:
    """Genera una respuesta JSON para recursos creados."""
    return success_response(message=message, data=data, meta=meta, status_code=201, headers=headers)

def no_content_response(
        message: str = "No content",
        headers: Optional[Dict[str, str]] = None
) -> Tuple[Response, int]:
    """Genera una respuesta JSON para casos donde no hay contenido que devolver."""
    response = jsonify({
        "status": True,
        "message": message
    })
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response, 204

def paginated_response(
    message: str,
    data: List[Any],
    page: int,
    per_page: int,
    total_items: int,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Tuple[Response, int]:
    """Genera una respuesta JSON paginada con metadatos de paginación."""
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0

    meta = {
        "current_page": page,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    return success_response(message=message, data=data, meta=meta, status_code=status_code, headers=headers)
