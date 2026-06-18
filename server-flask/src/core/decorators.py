from functools import wraps
from flask import session
from src.core.responses import error_response

def requiere_login(f):
    """
    Decorador para proteger rutas que requieren autenticación.
    Verifica la existencia del técnico en la sesión de Flask.
    Retorna un error 401 si no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "tecnico_actual" not in session:
            return error_response(message="No autenticado", status_code=401)
        return f(*args, **kwargs)
    return decorated_function
