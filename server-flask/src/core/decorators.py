"""Decoradores transversales para rutas y funciones del backend.

Este módulo contiene decoradores reutilizables que añaden comportamientos
comunes, como la verificación de autenticación de usuarios antes de permitir
el acceso a ciertas rutas de la API.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import session

from src.api.responses import error_response


def requiere_login(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorador para proteger rutas que requieren autenticación.

    Verifica que exista la clave ``'tecnico_actual'`` en la sesión de Flask.
    Si el usuario no ha iniciado sesión, retorna una respuesta de error con
    código HTTP ``401 Unauthorized`` sin ejecutar la función decorada.

    Args:
        func: Función de vista de Flask que se desea proteger.

    Returns:
        Función envuelta que ejecuta ``func`` solo cuando hay sesión activa.
    """
    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """Función envuelta que valida sesión antes de ejecutar la vista.

        Returns:
            Any: Resultado de la función de vista protegida, o una respuesta
            JSON con código HTTP ``401`` si no hay sesión activa.
        """
        if "tecnico_actual" not in session:
            return error_response(message="No autenticado", status_code=401)
        return func(*args, **kwargs)

    return decorated_function
